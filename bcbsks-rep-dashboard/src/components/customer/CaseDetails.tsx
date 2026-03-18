import React from 'react';
import type { Case, Member } from '../../types/customer.types';
import './CaseDetails.css';

interface CaseDetailsProps {
    case: Case;
    member: Member;
}

export const CaseDetails: React.FC<CaseDetailsProps> = ({ case: caseData, member }) => {
    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div className="case-details">
            <h3 className="section-title">Case Information</h3>

            <div className="details-grid">
                <div className="detail-item">
                    <label>Subject</label>
                    <div className="detail-value">{caseData.subject}</div>
                </div>

                <div className="detail-item full-width">
                    <label>Description</label>
                    <div className="detail-value">{caseData.description}</div>
                </div>

                <div className="detail-item">
                    <label>Priority</label>
                    <div className="detail-value">{caseData.priority}</div>
                </div>

                <div className="detail-item">
                    <label>Status</label>
                    <div className="detail-value">{caseData.status}</div>
                </div>

                <div className="detail-item">
                    <label>Type</label>
                    <div className="detail-value">{caseData.type}</div>
                </div>

                <div className="detail-item">
                    <label>Owner</label>
                    <div className="detail-value">{caseData.owner}</div>
                </div>

                <div className="detail-item">
                    <label>Created Date</label>
                    <div className="detail-value">{formatDate(caseData.createdDate)}</div>
                </div>

                <div className="detail-item">
                    <label>Last Modified</label>
                    <div className="detail-value">{formatDate(caseData.lastModified)}</div>
                </div>
            </div>

            <h3 className="section-title">Member Information</h3>

            <div className="details-grid">
                <div className="detail-item">
                    <label>Member Name</label>
                    <div className="detail-value">{member.firstName} {member.lastName}</div>
                </div>

                <div className="detail-item">
                    <label>Member ID</label>
                    <div className="detail-value">{member.memberId}</div>
                </div>

                <div className="detail-item">
                    <label>Date of Birth</label>
                    <div className="detail-value">{new Date(member.dateOfBirth).toLocaleDateString()}</div>
                </div>

                <div className="detail-item">
                    <label>Phone</label>
                    <div className="detail-value">{member.phone}</div>
                </div>

                <div className="detail-item">
                    <label>Email</label>
                    <div className="detail-value">{member.email}</div>
                </div>

                <div className="detail-item">
                    <label>Line of Business</label>
                    <div className="detail-value">{member.lineOfBusiness}</div>
                </div>
            </div>
        </div>
    );
};

// Made with Bob
