import React, { useState } from 'react';
import { useCustomer } from '../../context/CustomerContext';
import './SuggestedNextSteps.css';

export const SuggestedNextSteps: React.FC = () => {
    const { caseContext, completeNextStep } = useCustomer();
    const [showSources, setShowSources] = useState(false);

    if (!caseContext) {
        return null;
    }

    return (
        <div className="suggested-next-steps">
            <h3 className="section-title">Suggested next steps</h3>

            <ul className="steps-list">
                {caseContext.suggestedNextSteps.map((step) => (
                    <li key={step.id} className="step-item">
                        <input
                            type="checkbox"
                            checked={step.completed}
                            onChange={() => completeNextStep(step.id)}
                            className="step-checkbox"
                        />
                        <span className={step.completed ? 'step-text completed' : 'step-text'}>
                            {step.description}
                        </span>
                    </li>
                ))}
            </ul>

            <button
                className="sources-toggle"
                onClick={() => setShowSources(!showSources)}
            >
                Sources {showSources ? '▼' : '▶'}
            </button>

            {showSources && (
                <div className="sources-content">
                    {caseContext.sources.map((source) => (
                        <div key={source.id} className="source-item">
                            <a href={source.url} target="_blank" rel="noopener noreferrer" className="source-title">
                                {source.title}
                            </a>
                            <p className="source-snippet">{source.snippet}</p>
                            {source.documentDate && (
                                <div className="source-meta">
                                    <span className="source-date">Updated: {new Date(source.documentDate).toLocaleDateString()}</span>
                                    {source.version && <span className="source-version">Version: {source.version}</span>}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

// Made with Bob
