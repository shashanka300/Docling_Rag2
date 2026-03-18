import React, { useState } from 'react';
import { useCustomer } from '../../context/CustomerContext';
import './CaseAssistant.css';

export const CaseAssistant: React.FC = () => {
    const { caseContext } = useCustomer();
    const [activeTab, setActiveTab] = useState<'summary' | 'knowledge' | 'experts'>('summary');

    if (!caseContext) {
        return null;
    }

    return (
        <div className="case-assistant">
            <div className="assistant-header">
                <div className="assistant-icon">
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                        <circle cx="10" cy="10" r="8" stroke="currentColor" strokeWidth="2" />
                        <path d="M10 6v4l3 2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
                    </svg>
                </div>
                <h3 className="assistant-title">Case Assistant</h3>
            </div>

            <div className="assistant-subtitle">Understand this case</div>

            <div className="assistant-tabs">
                <button
                    className={`assistant-tab ${activeTab === 'summary' ? 'active' : ''}`}
                    onClick={() => setActiveTab('summary')}
                >
                    Summary
                </button>
                <button
                    className={`assistant-tab ${activeTab === 'knowledge' ? 'active' : ''}`}
                    onClick={() => setActiveTab('knowledge')}
                >
                    Knowledge
                </button>
                <button
                    className={`assistant-tab ${activeTab === 'experts' ? 'active' : ''}`}
                    onClick={() => setActiveTab('experts')}
                >
                    Experts
                </button>
            </div>

            <div className="assistant-content">
                {activeTab === 'summary' && (
                    <div className="summary-content">
                        <p>{caseContext.caseSummary}</p>
                    </div>
                )}

                {activeTab === 'knowledge' && (
                    <div className="knowledge-content">
                        <h4>Related Knowledge Articles</h4>
                        <ul className="knowledge-list">
                            {caseContext.knowledgeArticles?.map((article, index) => (
                                <li key={index}>
                                    <a href="#" className="knowledge-link">{article}</a>
                                </li>
                            ))}
                        </ul>
                    </div>
                )}

                {activeTab === 'experts' && (
                    <div className="experts-content">
                        <h4>Subject Matter Experts</h4>
                        <ul className="experts-list">
                            {caseContext.experts?.map((expert, index) => (
                                <li key={index} className="expert-item">{expert}</li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>

            <a href="#" className="external-link">
                → Open in watsonx Orchestrate
            </a>
        </div>
    );
};

// Made with Bob
