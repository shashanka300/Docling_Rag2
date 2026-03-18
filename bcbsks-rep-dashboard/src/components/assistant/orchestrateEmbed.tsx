/* eslint-disable @typescript-eslint/no-explicit-any */
// Lightweight React wrapper for Watsonx Orchestrate webchat (without JWT)

import { useEffect, useState, useRef } from "react";
import './orchestrateEmbed.css';

export type OrchestrateEmbedProps = {
  rootElementId?: string;
  showLauncher?: boolean;
  orchestrationId?: string;
  hostURL?: string;
  crn?: string;
  agentId?: string;
  agentEnvironmentId?: string;
  deploymentPlatform?: "ibmcloud" | "openshift" | string;
  layoutForm?: 'float' | 'fullscreen-overlay' | 'custom';
  layoutWidth?: string;
  layoutHeight?: string;
};

declare global {
  interface Window {
    wxoLoader?: {
      init: () => void;
      destroy?: () => void;
    };
    wxOConfiguration: any;
  }
}

export default function OrchestrateEmbed({
  rootElementId = "orchestrate-chat-container",
  showLauncher = true,
  orchestrationId,
  hostURL,
  crn,
  agentId,
  agentEnvironmentId,
  deploymentPlatform = "ibmcloud",
  layoutForm = "custom",
  layoutWidth = "100%",
  layoutHeight = "100%",
}: OrchestrateEmbedProps) {
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!hostURL || !orchestrationId || !agentId) {
      console.error("[OrchestrateEmbed] Missing required configuration");
      setError("Missing required configuration");
      return;
    }

    // Wait for the container element to be available
    if (!containerRef.current) {
      console.error("[OrchestrateEmbed] Container element not found");
      setError("Container element not found");
      return;
    }

    console.log(`Initializing agent in ${rootElementId}`);

    // Configure wxO with the actual HTMLElement reference for custom layout
    window.wxOConfiguration = {
      orchestrationID: orchestrationId,
      hostURL: hostURL,
      deploymentPlatform: deploymentPlatform,
      crn: crn || "",
      showLauncher: showLauncher,
      chatOptions: {
        agentId: agentId,
        environment_id: agentEnvironmentId || undefined,
      },
      layout: {
        form: layoutForm,
        // For custom layout, provide the actual HTMLElement reference
        customElement: layoutForm === 'custom' ? containerRef.current : undefined,
        // For float layout, provide width and height
        width: layoutForm === 'float' ? layoutWidth : undefined,
        height: layoutForm === 'float' ? layoutHeight : undefined,
        showOrchestrateHeader: true,
      },
    };

    // Only add rootElementID for fullscreen-overlay layout
    if (layoutForm === 'fullscreen-overlay') {
      window.wxOConfiguration.rootElementID = rootElementId;
    }

    const timeoutId = setTimeout(() => {
      const scriptId = 'wxo-loader-script';
      let script = document.getElementById(scriptId) as HTMLScriptElement | null;

      if (!script) {
        script = document.createElement('script');
        script.id = scriptId;
        script.src = `${window.wxOConfiguration.hostURL}/wxochat/wxoLoader.js?embed=true`;
        script.addEventListener('load', () => {
          if (window.wxoLoader?.init) {
            try {
              window.wxoLoader.init();
              setIsInitialized(true);
              console.log(`Agent initialized in ${rootElementId}`);
            } catch (err) {
              console.error('wxO initialization error:', err);
              setError(`Initialization failed: ${err}`);
            }
          }
        });
        script.addEventListener('error', () => {
          setError("Failed to load wxoLoader script");
        });
        document.head.appendChild(script);
      } else if (window.wxoLoader?.init) {
        try {
          window.wxoLoader.init();
          setIsInitialized(true);
        } catch (err) {
          console.error('wxO initialization error:', err);
          setError(`Initialization failed: ${err}`);
        }
      }
    }, 0);

    return () => {
      clearTimeout(timeoutId);
      if (window.wxoLoader?.destroy) {
        window.wxoLoader.destroy();
      }
    };
  }, [rootElementId, showLauncher, orchestrationId, hostURL, crn, agentId, agentEnvironmentId, deploymentPlatform, layoutForm, layoutWidth, layoutHeight]);

  if (error) {
    return (
      <div className="orchestrate-error">
        <p>Failed to load chat: {error}</p>
      </div>
    );
  }

  // Render the container div that will hold the chat widget
  return (
    <div 
      ref={containerRef}
      id={rootElementId}
      className="orchestrate-container"
      style={{ width: '100%', height: '100%' }}
    >
      {!isInitialized && (
        <div className="orchestrate-loading">
          <div className="loading-spinner"></div>
          <p>Loading watsonx Orchestrate...</p>
        </div>
      )}
    </div>
  );
}
