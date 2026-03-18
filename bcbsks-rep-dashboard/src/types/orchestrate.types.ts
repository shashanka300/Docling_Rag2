export interface WXOConfiguration {
  orchestrationID: string;
  hostURL: string;
  rootElementID: string;
  deploymentPlatform: string;
  crn: string;
  chatOptions: {
    agentId: string;
    agentEnvironmentId: string;
  };
}

export interface WXOLoader {
  init: () => void;
  destroy?: () => void;
}

declare global {
  interface Window {
    wxOConfiguration?: WXOConfiguration;
    wxoLoader?: WXOLoader;
  }
}

// Made with Bob
