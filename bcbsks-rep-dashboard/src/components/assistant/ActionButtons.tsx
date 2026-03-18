import React from 'react';
import './ActionButtons.css';

export const ActionButtons: React.FC = () => {
    const handleFollowUp = () => {
        console.log('Ask a follow up clicked');
    };

    const handleWriteResponse = () => {
        console.log('Write response clicked');
    };

    return (
        <div className="action-buttons">
            <button className="action-button primary" onClick={handleFollowUp}>
                Ask a follow up
            </button>
            <button className="action-button secondary" onClick={handleWriteResponse}>
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M2 12h12M2 8h12M2 4h12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                </svg>
                Write response with watsonx Orchestrate
            </button>
        </div>
    );
};

// Made with Bob
