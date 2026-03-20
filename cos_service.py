"""
IBM Cloud Object Storage (COS) Service
Handles file upload, download, and management operations for media files.
"""

import os
import mimetypes
from typing import Optional, Dict, List, BinaryIO
from pathlib import Path
from datetime import datetime, timedelta
import structlog
import ibm_boto3
import boto3
from ibm_botocore.client import Config, ClientError
from botocore.client import Config as BotocoreConfig
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = structlog.get_logger(__name__)


class COSSettings(BaseSettings):
    """COS configuration from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore extra fields from .env
    )
    
    cos_endpoint: str = ""
    cos_api_key_id: str = ""
    cos_instance_crn: str = ""
    cos_bucket_name: str = ""
    cos_region: str = "us-south"
    
    # Signed URL configuration
    cos_use_signed_urls: bool = False
    cos_signed_url_expiration: int = 3600  # 1 hour default
    cos_hmac_access_key_id: str = ""
    cos_hmac_secret_access_key: str = ""


class COSService:
    """
    Service for interacting with IBM Cloud Object Storage.
    
    Features:
    - Upload files with automatic content-type detection
    - Generate public URLs for uploaded files
    - Delete files
    - List files in bucket
    - Batch operations
    """
    
    def __init__(self):
        """Initialize COS client with credentials from environment."""
        self.settings = COSSettings()
        
        if not all([
            self.settings.cos_endpoint,
            self.settings.cos_api_key_id,
            self.settings.cos_instance_crn,
            self.settings.cos_bucket_name
        ]):
            logger.warning("COS credentials not fully configured")
            self._client = None
            self._hmac_client = None
            return
        
        try:
            # Initialize IBM COS client (for uploads with API key)
            self._client = ibm_boto3.client(
                's3',
                ibm_api_key_id=self.settings.cos_api_key_id,
                ibm_service_instance_id=self.settings.cos_instance_crn,
                config=Config(signature_version='oauth'),
                endpoint_url=self.settings.cos_endpoint
            )
            
            logger.info(
                "cos_client_initialized",
                bucket=self.settings.cos_bucket_name,
                region=self.settings.cos_region
            )
            
            # Initialize HMAC client for signed URLs (if credentials provided)
            if self.settings.cos_hmac_access_key_id and self.settings.cos_hmac_secret_access_key:
                self._hmac_client = boto3.client(
                    's3',
                    aws_access_key_id=self.settings.cos_hmac_access_key_id,
                    aws_secret_access_key=self.settings.cos_hmac_secret_access_key,
                    endpoint_url=self.settings.cos_endpoint,
                    config=BotocoreConfig(signature_version='s3v4')
                )
                logger.info("cos_hmac_client_initialized_for_signed_urls")
            else:
                self._hmac_client = None
                if self.settings.cos_use_signed_urls:
                    logger.warning("Signed URLs enabled but HMAC credentials not configured")
                    
        except Exception as e:
            logger.error("cos_client_initialization_failed", error=str(e))
            self._client = None
            self._hmac_client = None
    
    def is_configured(self) -> bool:
        """Check if COS is properly configured."""
        return self._client is not None
    
    def upload_file(
        self,
        file_path: str,
        object_key: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        public: bool = True
    ) -> Dict[str, str]:
        """
        Upload a file to COS bucket.
        
        Args:
            file_path: Local path to file to upload
            object_key: Key (path) in COS bucket (e.g., "labs/ask-hr/video.mp4")
            content_type: MIME type (auto-detected if not provided)
            metadata: Optional metadata to attach to object
            public: If True, set ACL to public-read. If False, keep private (default: True for backward compatibility)
            
        Returns:
            Dict with 'url', 'key', 'size', 'content_type', 'signed' (bool)
            
        Raises:
            FileNotFoundError: If local file doesn't exist
            ClientError: If upload fails
        """
        if not self.is_configured():
            raise RuntimeError("COS service not configured")
        
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Auto-detect content type if not provided
        if not content_type:
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                content_type = 'application/octet-stream'
        
        # Get file size
        file_size = file_path_obj.stat().st_size
        
        try:
            # Upload file
            with open(file_path, 'rb') as file_data:
                extra_args = {
                    'ContentType': content_type,
                }
                
                # Only set public ACL if explicitly requested
                if public:
                    extra_args['ACL'] = 'public-read'
                
                if metadata:
                    extra_args['Metadata'] = metadata
                
                self._client.upload_fileobj(
                    file_data,
                    self.settings.cos_bucket_name,
                    object_key,
                    ExtraArgs=extra_args
                )
            
            # Generate appropriate URL (signed or public)
            url = self.get_url(object_key, signed=not public)
            
            logger.info(
                "file_uploaded_to_cos",
                object_key=object_key,
                size_mb=round(file_size / (1024 * 1024), 2),
                content_type=content_type
            )
            
            return {
                'url': url,
                'key': object_key,
                'size': file_size,
                'content_type': content_type,
                'signed': not public and self.settings.cos_use_signed_urls
            }
            
        except ClientError as e:
            logger.error(
                "cos_upload_failed",
                object_key=object_key,
                error=str(e)
            )
            raise
    
    def upload_file_object(
        self,
        file_obj: BinaryIO,
        object_key: str,
        content_type: str,
        metadata: Optional[Dict[str, str]] = None,
        public: bool = True
    ) -> Dict[str, str]:
        """
        Upload a file object (e.g., from HTTP upload) to COS.
        
        Args:
            file_obj: File-like object to upload
            object_key: Key in COS bucket
            content_type: MIME type
            metadata: Optional metadata
            public: If True, set ACL to public-read. If False, keep private (default: True)
            
        Returns:
            Dict with upload details including 'signed' boolean
        """
        if not self.is_configured():
            raise RuntimeError("COS service not configured")
        
        try:
            extra_args = {
                'ContentType': content_type,
            }
            
            # Only set public ACL if explicitly requested
            if public:
                extra_args['ACL'] = 'public-read'
            
            if metadata:
                extra_args['Metadata'] = metadata
            
            self._client.upload_fileobj(
                file_obj,
                self.settings.cos_bucket_name,
                object_key,
                ExtraArgs=extra_args
            )
            
            # Generate appropriate URL (signed or public)
            url = self.get_url(object_key, signed=not public)
            
            logger.info(
                "file_object_uploaded_to_cos",
                object_key=object_key,
                content_type=content_type,
                public=public
            )
            
            return {
                'url': url,
                'key': object_key,
                'content_type': content_type,
                'signed': not public and self.settings.cos_use_signed_urls
            }
            
        except ClientError as e:
            logger.error(
                "cos_upload_failed",
                object_key=object_key,
                error=str(e)
            )
            raise
    
    def delete_file(self, object_key: str) -> bool:
        """
        Delete a file from COS bucket.
        
        Args:
            object_key: Key of object to delete
            
        Returns:
            True if deleted successfully
        """
        if not self.is_configured():
            raise RuntimeError("COS service not configured")
        
        try:
            self._client.delete_object(
                Bucket=self.settings.cos_bucket_name,
                Key=object_key
            )
            
            logger.info("file_deleted_from_cos", object_key=object_key)
            return True
            
        except ClientError as e:
            logger.error(
                "cos_delete_failed",
                object_key=object_key,
                error=str(e)
            )
            return False
    
    def file_exists(self, object_key: str) -> bool:
        """
        Check if a file exists in COS bucket.
        
        Args:
            object_key: Key to check
            
        Returns:
            True if file exists
        """
        if not self.is_configured():
            return False
        
        try:
            self._client.head_object(
                Bucket=self.settings.cos_bucket_name,
                Key=object_key
            )
            return True
        except ClientError:
            return False
    
    def list_files(self, prefix: str = "") -> List[Dict]:
        """
        List files in COS bucket with optional prefix filter.
        
        Args:
            prefix: Optional prefix to filter results (e.g., "labs/ask-hr/")
            
        Returns:
            List of dicts with file information
        """
        if not self.is_configured():
            raise RuntimeError("COS service not configured")
        
        try:
            response = self._client.list_objects_v2(
                Bucket=self.settings.cos_bucket_name,
                Prefix=prefix
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'url': self.get_public_url(obj['Key'])
                })
            
            return files
            
        except ClientError as e:
            logger.error("cos_list_failed", prefix=prefix, error=str(e))
            raise
    
    def get_public_url(self, object_key: str) -> str:
        """
        Generate public URL for an object in COS bucket.
        
        Args:
            object_key: Key of object
            
        Returns:
            Public URL string
        """
        # Format: https://<bucket>.s3.<region>.cloud-object-storage.appdomain.cloud/<key>
        bucket = self.settings.cos_bucket_name
        region = self.settings.cos_region
        return f"https://{bucket}.s3.{region}.cloud-object-storage.appdomain.cloud/{object_key}"
    
    def generate_signed_url(
        self,
        object_key: str,
        expiration: Optional[int] = None,
        method: str = 'get_object'
    ) -> str:
        """
        Generate a pre-signed URL for secure, time-limited access.
        
        Args:
            object_key: Key of object in COS
            expiration: URL expiration in seconds (default from settings)
            method: S3 method ('get_object', 'put_object', 'delete_object')
            
        Returns:
            Pre-signed URL string
            
        Raises:
            RuntimeError: If HMAC credentials not configured
        """
        if not self._hmac_client:
            raise RuntimeError(
                "HMAC credentials required for signed URLs. "
                "Set COS_HMAC_ACCESS_KEY_ID and COS_HMAC_SECRET_ACCESS_KEY in environment."
            )
        
        expiration = expiration or self.settings.cos_signed_url_expiration
        
        try:
            url = self._hmac_client.generate_presigned_url(
                ClientMethod=method,
                Params={
                    'Bucket': self.settings.cos_bucket_name,
                    'Key': object_key
                },
                ExpiresIn=expiration
            )
            
            logger.info(
                "signed_url_generated",
                object_key=object_key,
                expiration_seconds=expiration,
                method=method
            )
            
            return url
            
        except Exception as e:
            logger.error(
                "signed_url_generation_failed",
                object_key=object_key,
                error=str(e)
            )
            raise
    
    def generate_signed_upload_url(
        self,
        object_key: str,
        content_type: str,
        expiration: int = 300  # 5 minutes for uploads
    ) -> Dict:
        """
        Generate pre-signed URL for direct client-side uploads.
        
        Args:
            object_key: Destination key in COS
            content_type: MIME type of file
            expiration: Upload URL expiration (default: 5 minutes)
            
        Returns:
            Dict with 'url' and 'fields' for POST upload
            
        Raises:
            RuntimeError: If HMAC credentials not configured
        """
        if not self._hmac_client:
            raise RuntimeError(
                "HMAC credentials required for signed upload URLs. "
                "Set COS_HMAC_ACCESS_KEY_ID and COS_HMAC_SECRET_ACCESS_KEY in environment."
            )
        
        try:
            response = self._hmac_client.generate_presigned_post(
                Bucket=self.settings.cos_bucket_name,
                Key=object_key,
                Fields={'Content-Type': content_type},
                Conditions=[
                    {'Content-Type': content_type},
                    ['content-length-range', 0, 104857600]  # Max 100MB
                ],
                ExpiresIn=expiration
            )
            
            logger.info(
                "signed_upload_url_generated",
                object_key=object_key,
                expiration_seconds=expiration
            )
            
            return response
            
        except Exception as e:
            logger.error(
                "signed_upload_url_generation_failed",
                object_key=object_key,
                error=str(e)
            )
            raise
    
    def get_url(self, object_key: str, signed: Optional[bool] = None) -> str:
        """
        Get URL for object (signed or public based on configuration).
        
        Args:
            object_key: Key of object
            signed: Override global setting (True=signed, False=public, None=use config)
            
        Returns:
            URL string (signed or public)
        """
        use_signed = signed if signed is not None else self.settings.cos_use_signed_urls
        
        if use_signed and self._hmac_client:
            try:
                return self.generate_signed_url(object_key)
            except Exception as e:
                logger.warning(
                    "failed_to_generate_signed_url_falling_back_to_public",
                    object_key=object_key,
                    error=str(e)
                )
                return self.get_public_url(object_key)
        else:
            return self.get_public_url(object_key)
    
    def batch_upload(
        self,
        files: List[Dict[str, str]],
        progress_callback: Optional[callable] = None  # type: ignore
    ) -> Dict:
        """
        Upload multiple files in batch.
        
        Args:
            files: List of dicts with 'local_path' and 'object_key'
            progress_callback: Optional callback(current, total, file_info)
            
        Returns:
            Dict with 'successful', 'failed', 'results'
        """
        if not self.is_configured():
            raise RuntimeError("COS service not configured")
        
        results = {
            'successful': [],
            'failed': [],
            'total': len(files)
        }
        
        for i, file_info in enumerate(files, 1):
            try:
                result = self.upload_file(
                    file_path=file_info['local_path'],
                    object_key=file_info['object_key']
                )
                results['successful'].append({
                    **file_info,
                    **result
                })
                
                if progress_callback:
                    progress_callback(i, len(files), result)
                    
            except Exception as e:
                logger.error(
                    "batch_upload_file_failed",
                    file=file_info['local_path'],
                    error=str(e)
                )
                results['failed'].append({
                    **file_info,
                    'error': str(e)
                })
        
        logger.info(
            "batch_upload_completed",
            successful=len(results['successful']),
            failed=len(results['failed']),
            total=results['total']
        )
        
        return results


# Singleton instance
_cos_service: Optional[COSService] = None


def get_cos_service() -> COSService:
    """Get or create COS service singleton instance."""
    global _cos_service
    if _cos_service is None:
        _cos_service = COSService()
    return _cos_service