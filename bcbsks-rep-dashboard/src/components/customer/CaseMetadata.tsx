import React from 'react';
import type { Case, Member } from '../../types/customer.types';
import './CaseMetadata.css';

interface CaseMetadataProps {
    case: Case;
    member: Member;
}

export const CaseMetadata: React.FC<CaseMetadataProps> = ({ case: caseData, member }) => {
    return (
        <div className="case-metadata">
            <h3 className="section-title">Additional Information</h3>

            <div className="metadata-grid">
                <div className="metadata-item">
                    <label>Policy Number</label>
                    <div className="metadata-value">{member.policyNumber}</div>
                </div>

                <div className="metadata-item">
                    <label>Plan Type</label>
                    <div className="metadata-value">{member.planType}</div>
                </div>

                <div className="metadata-item">
                    <label>Effective Date</label>
                    <div className="metadata-value">
                        {new Date(member.effectiveDate).toLocaleDateString()}
                    </div>
                </div>

                <div className="metadata-item">
                    <label>Case Number</label>
                    <div className="metadata-value">{caseData.caseNumber}</div>
                </div>

                {member.address && (
                    <div className="metadata-item full-width">
                        <label>Address</label>
                        <div className="metadata-value">
                            {member.address.street}<br />
                            {member.address.city}, {member.address.state} {member.address.zipCode}
                        </div>
                    </div>
                )}

                {caseData.tags && caseData.tags.length > 0 && (
                    <div className="metadata-item full-width">
                        <label>Tags</label>
                        <div className="metadata-tags">
                            {caseData.tags.map((tag, index) => (
                                <span key={index} className="tag">{tag}</span>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

// Made with Bob
