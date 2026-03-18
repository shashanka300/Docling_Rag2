import React from 'react';
import type { ReactNode } from 'react';
import './DashboardLayout.css';

interface DashboardLayoutProps {
    leftPanel: ReactNode;
    rightPanel: ReactNode;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({
    leftPanel,
    rightPanel
}) => {
    return (
        <div className="dashboard-layout">
            <header className="dashboard-header">
                <div className="header-logo">
                    <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
                        <rect width="40" height="40" rx="8" fill="#0176d3" />
                        <text x="20" y="28" fontSize="20" fontWeight="bold" fill="white" textAnchor="middle">BC</text>
                    </svg>
                </div>
                <div className="header-title">
                    <h1>BCBSKS Customer Service Dashboard</h1>
                </div>
                <div className="header-actions">
                    <button className="header-button">Settings</button>
                </div>
            </header>

            <main className="dashboard-main">
                <div className="dashboard-left-panel">
                    {leftPanel}
                </div>
                <div className="dashboard-right-panel">
                    {rightPanel}
                </div>
            </main>
        </div>
    );
};

// Made with Bob
