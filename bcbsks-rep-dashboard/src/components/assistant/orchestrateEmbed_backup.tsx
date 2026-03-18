/* eslint-disable @typescript-eslint/no-explicit-any */
// src/components/OrchestrateEmbed.tsx
// Lightweight React wrapper that bootstraps the Watsonx Orchestrate webchat
// with secure JWT authentication

import { useEffect, useState } from "react";
import './orchestrateEmbed.css';

/**
 * Props for OrchestrateEmbed component
 */
export type OrchestrateEmbedProps = {
  /** The DOM element id that the chat should attach to. Defaults to 'root'. */
  rootElementId?: string;
  /** Whether to show the floating launcher. Defaults to false for modal usage. */
  showLauncher?: boolean;
  /** Orchestration ID */
  orchestrationId?: string;
  /** Host URL (e.g. https://us-south.watson-orchestrate.cloud.ibm.com) */
  hostURL?: string;
  /** CRN */
  crn?: string;
  /** Agent ID */
  agentId?: string;
  /** Agent Environment ID (optional) */
  agentEnvironmentId?: string;
  /** Deployment platform */
  deploymentPlatform?: "ibmcloud" | "openshift" | string;
  /** Layout form: 'float', 'fullscreen-overlay', or 'custom' */
  layoutForm?: 'float' | 'fullscreen-overlay' | 'custom';
  /** Layout width (for float mode) */
  layoutWidth?: string;
  /** Layout height (for float mode) */
  layoutHeight?: string;
};

// Declare globals used by the embed script
declare global {
  interface Window {
    wxoLoader?: {
      init: () => void;
      destroy?: () => void;
    };
    wxOConfiguration: any;
  }
}

export default function OrchestrateEmbed({
  rootElementId = "root",
  showLauncher = false,
  orchestrationId,
  hostURL,
  crn,
  agentId,
  agentEnvironmentId,
  deploymentPlatform = "ibmcloud",
  layoutForm = "fullscreen-overlay",
  layoutWidth = "600px",
  layoutHeight = "800px",
}: OrchestrateEmbedProps) {
  const [jwtToken, setJwtToken] = useState<string | null>(null);
  const [isLoadingToken, setIsLoadingToken] = useState(true);
  const [tokenError, setTokenError] = useState<string | null>(null);

  // Fetch JWT token from backend
  useEffect(() => {
    const fetchJWTToken = async () => {
      try {
        setIsLoadingToken(true);
        setTokenError(null);

        console.log('🔐 Fetching JWT token from backend...');

        // Get current page for context
        const currentPage = typeof window !== 'undefined' ? window.location.pathname : '/';
        const apiUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/jwt/create?current_page=${encodeURIComponent(currentPage)}`;

        console.log(`📍 Current page: ${currentPage}`);

        const response = await fetch(apiUrl, {
          method: 'GET',
          credentials: 'include', // Include cookies for anonymous user ID
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch JWT token: ${response.status} ${response.statusText}`);
        }

        const data = await response.json();

        if (!data.token) {
          throw new Error('No token in response');
        }

        console.log('✅ JWT token fetched successfully');
        console.log(`⏱️ Token expires in ${data.expires_in} seconds`);
        console.log(`📍 Context includes current page: ${currentPage}`);

        // Decode JWT to show context variables
        try {
          const parts = data.token.split('.');
          if (parts.length === 3) {
            const payload = JSON.parse(atob(parts[1]));
            console.log('🔍 JWT Payload decoded:');
            console.log('  - Subject (user ID):', payload.sub);
            console.log('  - Issued at:', new Date(payload.iat * 1000).toLocaleString());
            console.log('  - Expires at:', new Date(payload.exp * 1000).toLocaleString());
            console.log('  - Context variables:', payload.context);

            // Pretty print context for easy reading
            if (payload.context) {
              console.log('📋 Context Variables Detail:');
              Object.entries(payload.context).forEach(([key, value]) => {
                console.log(`  - ${key}:`, value);
              });
            }
          }
        } catch (decodeError) {
          console.warn('⚠️ Could not decode JWT token for logging:', decodeError);
        }

        setJwtToken(data.token);
        setIsLoadingToken(false);
      } catch (error) {
        console.error('❌ Failed to fetch JWT token:', error);
        setTokenError(error instanceof Error ? error.message : 'Unknown error');
        setIsLoadingToken(false);
      }
    };

    fetchJWTToken();
  }, []);

  // Initialize agent with JWT token
  useEffect(() => {
    // Wait for JWT token to be fetched
    if (isLoadingToken || !jwtToken) {
      if (tokenError) {
        console.error('[OrchestrateEmbed] Cannot initialize agent without JWT token');
      }
      return;
    }

    // Validate required configuration
    if (!hostURL || !orchestrationId || !agentId) {
      console.error("[OrchestrateEmbed] Missing required configuration:", {
        hostURL: hostURL || '❌ MISSING',
        orchestrationId: orchestrationId || '❌ MISSING',
        agentId: agentId || '❌ MISSING',
      });
      return;
    }

    console.log(`🔌 Initializing agent in ${rootElementId} with JWT authentication`);

    // Event handler to inject context variables into each message
    const preSendHandler = (event: any) => {
      console.log('📤 pre:send event triggered');

      // Get user info from JWT token
      const getUserInfoFromJWT = () => {
        const token = window.wxOConfiguration?.token;
        if (!token) {
          return { email: 'anonymous', authenticated: false };
        }

        try {
          const parts = token.split('.');
          if (parts.length === 3) {
            const payload = JSON.parse(atob(parts[1]));
            return {
              email: payload.context?.user_email || 'anonymous',
              authenticated: payload.context?.authenticated || false,
              role: payload.context?.user_role || 'guest'
            };
          }
        } catch (error) {
          console.warn('Could not decode JWT for context:', error);
        }

        return { email: 'anonymous', authenticated: false };
      };

      // Get current page
      const currentPage = typeof window !== 'undefined' ? window.location.pathname : '/';
      const userInfo = getUserInfoFromJWT();

      // Inject context variables into the message payload
      // According to watsonx Orchestrate docs, context must be set on event.message.context
      event.message.context = {
        user_email: userInfo.email,
        current_page: currentPage,
        authenticated: userInfo.authenticated
      };

      console.log('✅ Context variables injected:', event.message.context);
    };

    // Chat load handler to register events
    const onChatLoad = (instance: any) => {
      console.log('💬 Chat loaded, registering pre:send event handler');
      instance.on('pre:send', preSendHandler);

      // Store instance globally for debugging
      (window as any).wxoChatInstance = instance;
    };

    // Set configuration with JWT token and event handlers
    window.wxOConfiguration = {
      orchestrationID: orchestrationId,
      hostURL: hostURL,
      rootElementID: rootElementId,
      deploymentPlatform: deploymentPlatform,
      crn: crn || "",
      showLauncher: showLauncher,
      token: jwtToken, // ← JWT token for authentication
      chatOptions: {
        agentId: agentId,
        agentEnvironmentId: agentEnvironmentId || undefined,
        onLoad: onChatLoad, // ← Register event handlers
      },
      layout: {
        form: layoutForm,
        width: layoutForm === 'float' ? layoutWidth : undefined,
        height: layoutForm === 'float' ? layoutHeight : undefined,
        showOrchestrateHeader: true,
        showMaxWidth: false,
      },
      header: {
        showResetButton: true,
        showAiDisclaimer: true,
        showMaximize: false,
      },
      style: {
        headerColor: '#0f62fe',
        userMessageBackgroundColor: '#0f62fe',
        primaryColor: '#0f62fe',
        showBackgroundGradient: true,
      }
    };

    // Use setTimeout to ensure DOM is ready
    const timeoutId = setTimeout(() => {
      const scriptId = 'wxo-loader-script';
      let script = document.getElementById(scriptId) as HTMLScriptElement | null;

      if (!script) {
        console.log(`📥 Loading wxoLoader script`);
        script = document.createElement('script');
        script.id = scriptId;
        script.src = `${window.wxOConfiguration.hostURL}/wxochat/wxoLoader.js?embed=true`;
        script.addEventListener('load', () => {
          console.log(`✅ wxoLoader script loaded successfully`);
          if (window.wxoLoader?.init) {
            try {
              window.wxoLoader.init();
              console.log(`✅ Agent initialized in ${rootElementId} with JWT authentication`);
            } catch (error) {
              console.error(`❌ Failed to initialize agent in ${rootElementId}:`, error);
            }
          } else {
            console.error('❌ window.wxoLoader.init not available after script load');
          }
        });
        script.addEventListener('error', (error) => {
          console.error(`❌ Failed to load wxoLoader script:`, error);
        });
        document.head.appendChild(script);
      } else {
        console.log(`♻️ wxoLoader script already exists, re-initializing for ${rootElementId}...`);
        if (window.wxoLoader?.init) {
          try {
            window.wxoLoader.init();
            console.log(`✅ Agent re-initialized in ${rootElementId} with JWT authentication`);
          } catch (error) {
            console.error(`❌ Failed to re-initialize agent in ${rootElementId}:`, error);
          }
        }
      }
    }, 0);

    // Cleanup on unmount
    return () => {
      clearTimeout(timeoutId);
      try {
        if (window.wxoLoader?.destroy) {
          console.log(`🧹 Destroying agent in ${rootElementId}`);
          window.wxoLoader.destroy();
        }
      } catch (error) {
        console.error(`⚠️ Error destroying agent in ${rootElementId}:`, error);
      }
    };
  }, [
    jwtToken,
    isLoadingToken,
    rootElementId,
    showLauncher,
    orchestrationId,
    hostURL,
    crn,
    agentId,
    agentEnvironmentId,
    deploymentPlatform,
  ]);

  // Handle token refresh on expiration
  useEffect(() => {
    if (!jwtToken) return;

    const handleTokenExpired = async () => {
      try {
        console.log('🔄 Token expired, refreshing...');

        // Get current page for context
        const currentPage = typeof window !== 'undefined' ? window.location.pathname : '/';
        const apiUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/jwt/refresh?current_page=${encodeURIComponent(currentPage)}`;

        const response = await fetch(apiUrl, {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error('Failed to refresh token');
        }

        const data = await response.json();

        if (data.token) {
          console.log('✅ Token refreshed successfully');
          console.log(`📍 Updated context with current page: ${currentPage}`);
          setJwtToken(data.token);

          // Update configuration with new token
          if (window.wxOConfiguration) {
            window.wxOConfiguration.token = data.token;
          }
        }
      } catch (error) {
        console.error('❌ Failed to refresh token:', error);
      }
    };

    // Listen for token expiration event (if supported by wxoLoader)
    window.addEventListener('wxo:tokenExpired', handleTokenExpired);

    return () => {
      window.removeEventListener('wxo:tokenExpired', handleTokenExpired);
    };
  }, [jwtToken]);

  // Add global helper function to decode JWT from console
  useEffect(() => {
    if (typeof window !== 'undefined') {
      (window as any).decodeJWT = () => {
        const token = window.wxOConfiguration?.token;

        if (!token) {
          console.error('❌ No JWT token found in wxOConfiguration');
          return null;
        }

        try {
          const parts = token.split('.');
          if (parts.length !== 3) {
            console.error('❌ Invalid JWT token format');
            return null;
          }

          const payload = JSON.parse(atob(parts[1]));

          console.log('🔍 JWT Token Decoded:');
          console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
          console.log('Subject (User ID):', payload.sub);
          console.log('Issued At:', new Date(payload.iat * 1000).toLocaleString());
          console.log('Expires At:', new Date(payload.exp * 1000).toLocaleString());
          console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
          console.log('📋 Context Variables:');

          if (payload.context && typeof payload.context === 'object') {
            Object.entries(payload.context).forEach(([key, value]) => {
              console.log(`  ${key}:`, value);
            });
          } else {
            console.log('  (no context variables found)');
          }

          console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
          console.log('Full Payload:', payload);

          return payload;
        } catch (error) {
          console.error('❌ Error decoding JWT:', error);
          return null;
        }
      };

      console.log('💡 Tip: Run decodeJWT() in console to see JWT context variables');
    }

    return () => {
      if (typeof window !== 'undefined') {
        delete (window as any).decodeJWT;
      }
    };
  }, [jwtToken]);

  // Show loading or error state
  if (isLoadingToken) {
    return null; // Loading handled by parent component
  }

  if (tokenError) {
    console.error('[OrchestrateEmbed] JWT token error:', tokenError);
    return null; // Error handled by parent component
  }

  // This component renders nothing; it just bootstraps the chat
  return null;
}
