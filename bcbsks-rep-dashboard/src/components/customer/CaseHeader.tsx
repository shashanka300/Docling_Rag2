import React from 'react';
import type { Case } from '../../types/customer.types';
import './CaseHeader.css';

interface CaseHeaderProps {
    case: Case;
}

export const CaseHeader: React.FC<CaseHeaderProps> = ({ case: caseData }) => {
    const getStatusColor = (status: string) => {
        switch (status) {
            case 'New': return 'status-new';
            case 'In Progress': return 'status-in-progress';
            case 'Pending': return 'status-pending';
            case 'Resolved': return 'status-resolved';
            case 'Closed': return 'status-closed';
            default: return 'status-default';
        }
    };

    const getPriorityColor = (priority: string) => {
        switch (priority) {
            case 'Critical': return 'priority-critical';
            case 'High': return 'priority-high';
            case 'Medium': return 'priority-medium';
            case 'Low': return 'priority-low';
            default: return 'priority-default';
        }
    };

    return (
        <div className="case-header">
            <div className="case-header-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" strokeWidth="2" />
                    <path d="M9 11L11 13L15 9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
            </div>
            <div className="case-header-content">
                <div className="case-header-top">
                    <span className="case-type">{caseData.type}</span>
                    <span className="case-number">{caseData.caseNumber}</span>
                </div>
                <h2 className="case-subject">{caseData.subject}</h2>
                <div className="case-badges">
                    <span className={`badge ${getStatusColor(caseData.status)}`}>
                        {caseData.status}
                    </span>
                    <span className={`badge ${getPriorityColor(caseData.priority)}`}>
                        {caseData.priority}
                    </span>
                </div>
            </div>
        </div>
    );
};

// Made with Bob
