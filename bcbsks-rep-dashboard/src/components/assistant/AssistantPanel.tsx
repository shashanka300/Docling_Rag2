import React from 'react';
import { CaseAssistant } from './CaseAssistant';
import { SuggestedNextSteps } from './SuggestedNextSteps';
import { ActionButtons } from './ActionButtons';
import OrchestrateEmbed from './orchestrateEmbed';
import './AssistantPanel.css';

export const AssistantPanel: React.FC = () => {
    return (
        <div className="assistant-panel">
            <CaseAssistant />
            <SuggestedNextSteps />
            <ActionButtons />
            <div className="orchestrate-section">
                <h3 className="section-title">AI Assistant</h3>
                <div className="orchestrate-chat-wrapper">
                    <OrchestrateEmbed
                        rootElementId="orchestrate-chat-container"
                        orchestrationId="ad4fa6953138448689fb746aade5025e_3f8fb562-4a6f-4cec-92a2-1172811cffee"
                        hostURL="https://us-south.watson-orchestrate.cloud.ibm.com"
                        crn="crn:v1:bluemix:public:watsonx-orchestrate:us-south:a/ad4fa6953138448689fb746aade5025e:3f8fb562-4a6f-4cec-92a2-1172811cffee::"
                        agentId="18015fee-4a97-4b2f-885d-fa9be453627b"
                        deploymentPlatform="ibmcloud"
                        layoutForm="custom"
                        showLauncher={true}
                    />
                </div>
            </div>
        </div>
    );
};

// Made with Bob
