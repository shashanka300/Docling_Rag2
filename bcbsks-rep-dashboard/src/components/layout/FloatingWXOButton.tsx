import React, { useState } from 'react';
import './FloatingWXOButton.css';

export const FloatingWXOButton: React.FC = () => {
    const [isExpanded, setIsExpanded] = useState(false);

    return (
        <>
            <button
                className="floating-wxo-button"
                onClick={() => setIsExpanded(!isExpanded)}
                aria-label="Toggle WXO Assistant"
            >
                WXO
            </button>

            {isExpanded && (
                <div className="floating-wxo-panel">
                    <div className="floating-wxo-header">
                        <h3>WXO Assistant</h3>
                        <button
                            className="close-button"
                            onClick={() => setIsExpanded(false)}
                            aria-label="Close"
                        >
                            ×
                        </button>
                    </div>
                    <div className="floating-wxo-content">
                        <p>Quick access to WXO features</p>
                    </div>
                </div>
            )}
        </>
    );
};

// Made with Bob
