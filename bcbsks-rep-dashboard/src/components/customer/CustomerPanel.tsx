import React, { useState } from 'react';
import { useCustomer } from '../../context/CustomerContext';
import { CaseHeader } from './CaseHeader';
import { CaseDetails } from './CaseDetails';
import { CaseMetadata } from './CaseMetadata';
import './CustomerPanel.css';

export const CustomerPanel: React.FC = () => {
    const { caseContext } = useCustomer();
    const [activeTab, setActiveTab] = useState<'details' | 'chatter'>('details');

    if (!caseContext) {
        return <div className="customer-panel-loading">Loading case information...</div>;
    }

    return (
        <div className="customer-panel">
            <CaseHeader case={caseContext.case} />

            <div className="tabs-container">
                <div className="tabs">
                    <button
                        className={`tab ${activeTab === 'details' ? 'active' : ''}`}
                        onClick={() => setActiveTab('details')}
                    >
                        Details
                    </button>
                    <button
                        className={`tab ${activeTab === 'chatter' ? 'active' : ''}`}
                        onClick={() => setActiveTab('chatter')}
                    >
                        Chatter
                    </button>
                </div>
            </div>

            <div className="tab-content">
                {activeTab === 'details' ? (
                    <>
                        <CaseDetails case={caseContext.case} member={caseContext.member} />
                        <CaseMetadata case={caseContext.case} member={caseContext.member} />
                    </>
                ) : (
                    <div className="chatter-content">
                        <p className="text-gray-500">Activity feed coming soon...</p>
                    </div>
                )}
            </div>
        </div>
    );
};

// Made with Bob
