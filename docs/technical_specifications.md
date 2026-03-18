# Technical Specifications - BCBSKS Rep Dashboard

## Technology Stack Details

### Core Dependencies
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "typescript": "^5.0.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.0.0",
    "vite": "^4.4.0"
  }
}
```

### Optional Dependencies (Based on Styling Choice)
```json
{
  "dependencies": {
    "tailwindcss": "^3.3.0",
    "autoprefixer": "^10.4.14",
    "postcss": "^8.4.27"
  }
}
```

## Type Definitions

### Core Types
```typescript
// src/types/customer.types.ts

export type LineOfBusiness = 'Commercial' | 'Medicare Advantage' | 'Medicaid';
export type CaseStatus = 'New' | 'In Progress' | 'Pending' | 'Resolved' | 'Closed';
export type CasePriority = 'Low' | 'Medium' | 'High' | 'Critical';
export type CaseType = 'Prior Auth' | 'Benefits Question' | 'Claims' | 'General Inquiry';

export interface Member {
  id: string;
  firstName: string;
  lastName: string;
  memberId: string;
  dateOfBirth: string;
  policyNumber: string;
  lineOfBusiness: LineOfBusiness;
  planType: string;
  effectiveDate: string;
  terminationDate?: string;
  phone: string;
  email: string;
  address?: {
    street: string;
    city: string;
    state: string;
    zipCode: string;
  };
}

export interface Case {
  id: string;
  caseNumber: string;
  subject: string;
  description: string;
  status: CaseStatus;
  priority: CasePriority;
  type: CaseType;
  owner: string;
  createdDate: string;
  lastModified: string;
  memberId: string;
  resolution?: string;
  tags?: string[];
}

export interface Source {
  id: string;
  title: string;
  url: string;
  snippet: string;
  documentDate?: string;
  version?: string;
}

export interface NextStep {
  id: string;
  description: string;
  completed: boolean;
  priority: number;
}

export interface CaseContext {
  member: Member;
  case: Case;
  caseSummary: string;
  suggestedNextSteps: NextStep[];
  sources: Source[];
  knowledgeArticles?: string[];
  experts?: string[];
}
```

### Orchestrate Types
```typescript
// src/types/orchestrate.types.ts

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
```

## Mock Data Implementation

### Sample Customer Data
```typescript
// src/data/mockCustomerData.ts

import { Member, Case, CaseContext, Source, NextStep } from '../types/customer.types';

export const mockMembers: Member[] = [
  {
    id: 'mem-001',
    firstName: 'John',
    lastName: 'Smith',
    memberId: 'BCBS-MA-123456',
    dateOfBirth: '1965-03-15',
    policyNumber: 'POL-MA-789012',
    lineOfBusiness: 'Medicare Advantage',
    planType: 'Medicare Advantage PPO',
    effectiveDate: '2024-01-01',
    phone: '(555) 123-4567',
    email: 'john.smith@email.com',
    address: {
      street: '123 Main Street',
      city: 'Topeka',
      state: 'KS',
      zipCode: '66603'
    }
  },
  {
    id: 'mem-002',
    firstName: 'Sarah',
    lastName: 'Johnson',
    memberId: 'BCBS-COM-234567',
    dateOfBirth: '1985-07-22',
    policyNumber: 'POL-COM-890123',
    lineOfBusiness: 'Commercial',
    planType: 'PPO Gold',
    effectiveDate: '2023-06-01',
    phone: '(555) 234-5678',
    email: 'sarah.johnson@email.com',
    address: {
      street: '456 Oak Avenue',
      city: 'Wichita',
      state: 'KS',
      zipCode: '67202'
    }
  }
];

export const mockCases: Case[] = [
  {
    id: 'case-001',
    caseNumber: 'CS-2024-001234',
    subject: 'Prior Authorization - Outpatient Imaging',
    description: 'Member is requesting prior authorization for outpatient MRI imaging for lower back pain. Needs clarification on current policy requirements.',
    status: 'In Progress',
    priority: 'High',
    type: 'Prior Auth',
    owner: 'Rep: Jennifer Martinez',
    createdDate: '2024-03-15T09:30:00Z',
    lastModified: '2024-03-18T14:22:00Z',
    memberId: 'mem-001',
    tags: ['imaging', 'prior-auth', 'medicare']
  },
  {
    id: 'case-002',
    caseNumber: 'CS-2024-001235',
    subject: 'Benefits Question - Specialist Coverage',
    description: 'Member asking about coverage for out-of-network specialist visit. Needs information on reimbursement rates and claim submission process.',
    status: 'New',
    priority: 'Medium',
    type: 'Benefits Question',
    owner: 'Rep: Michael Chen',
    createdDate: '2024-03-18T11:15:00Z',
    lastModified: '2024-03-18T11:15:00Z',
    memberId: 'mem-002',
    tags: ['benefits', 'specialist', 'commercial']
  }
];

export const mockSources: Source[] = [
  {
    id: 'src-001',
    title: 'Prior Authorization Policy - Imaging Services',
    url: 'https://sharepoint.bcbsks.com/policies/prior-auth-imaging-2024',
    snippet: 'Outpatient imaging services including MRI, CT, and PET scans require prior authorization for Medicare Advantage members when ordered for non-emergency conditions...',
    documentDate: '2024-01-15',
    version: 'v2.3'
  },
  {
    id: 'src-002',
    title: 'Medicare Advantage Coverage Guidelines',
    url: 'https://sharepoint.bcbsks.com/policies/ma-coverage-2024',
    snippet: 'Medicare Advantage plans follow CMS guidelines with additional coverage options. Prior authorization requirements may differ from commercial plans...',
    documentDate: '2024-02-01',
    version: 'v1.8'
  }
];

export const mockNextSteps: NextStep[] = [
  {
    id: 'step-001',
    description: 'Verify member has active coverage for imaging services',
    completed: false,
    priority: 1
  },
  {
    id: 'step-002',
    description: 'Confirm ordering physician is in-network',
    completed: false,
    priority: 2
  },
  {
    id: 'step-003',
    description: 'Submit prior authorization request through portal',
    completed: false,
    priority: 3
  }
];

export const mockCaseContext: CaseContext = {
  member: mockMembers[0],
  case: mockCases[0],
  caseSummary: 'Member John Smith (Medicare Advantage) is requesting prior authorization for outpatient MRI imaging. Current policy requires prior auth for non-emergency imaging. Need to verify coverage, confirm in-network provider, and submit authorization request.',
  suggestedNextSteps: mockNextSteps,
  sources: mockSources,
  knowledgeArticles: [
    'How to Submit Prior Authorization Requests',
    'Medicare Advantage Imaging Coverage FAQ',
    'Understanding Prior Auth Turnaround Times'
  ],
  experts: [
    'Dr. Emily Rodriguez - Medical Director',
    'Tom Wilson - Prior Auth Specialist'
  ]
};

// Helper function to get case context by case ID
export const getCaseContext = (caseId: string): CaseContext | null => {
  const caseData = mockCases.find(c => c.id === caseId);
  if (!caseData) return null;
  
  const member = mockMembers.find(m => m.id === caseData.memberId);
  if (!member) return null;
  
  return {
    member,
    case: caseData,
    caseSummary: mockCaseContext.caseSummary,
    suggestedNextSteps: mockNextSteps,
    sources: mockSources
  };
};
```

## Context Implementation

### Customer Context
```typescript
// src/context/CustomerContext.tsx

import React, { createContext, useContext, useState, ReactNode } from 'react';
import { CaseContext, NextStep } from '../types/customer.types';
import { mockCaseContext } from '../data/mockCustomerData';

interface CustomerContextType {
  caseContext: CaseContext | null;
  loading: boolean;
  error: Error | null;
  setCaseContext: (context: CaseContext) => void;
  updateCaseSummary: (summary: string) => void;
  addNextStep: (step: string) => void;
  completeNextStep: (stepId: string) => void;
  refreshCase: () => Promise<void>;
}

const CustomerContext = createContext<CustomerContextType | undefined>(undefined);

export const CustomerProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [caseContext, setCaseContext] = useState<CaseContext | null>(mockCaseContext);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const updateCaseSummary = (summary: string) => {
    if (caseContext) {
      setCaseContext({
        ...caseContext,
        caseSummary: summary
      });
    }
  };

  const addNextStep = (description: string) => {
    if (caseContext) {
      const newStep: NextStep = {
        id: `step-${Date.now()}`,
        description,
        completed: false,
        priority: caseContext.suggestedNextSteps.length + 1
      };
      
      setCaseContext({
        ...caseContext,
        suggestedNextSteps: [...caseContext.suggestedNextSteps, newStep]
      });
    }
  };

  const completeNextStep = (stepId: string) => {
    if (caseContext) {
      const updatedSteps = caseContext.suggestedNextSteps.map(step =>
        step.id === stepId ? { ...step, completed: true } : step
      );
      
      setCaseContext({
        ...caseContext,
        suggestedNextSteps: updatedSteps
      });
    }
  };

  const refreshCase = async () => {
    setLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      // In real implementation, fetch fresh data from API
      setError(null);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <CustomerContext.Provider
      value={{
        caseContext,
        loading,
        error,
        setCaseContext,
        updateCaseSummary,
        addNextStep,
        completeNextStep,
        refreshCase
      }}
    >
      {children}
    </CustomerContext.Provider>
  );
};

export const useCustomer = () => {
  const context = useContext(CustomerContext);
  if (context === undefined) {
    throw new Error('useCustomer must be used within a CustomerProvider');
  }
  return context;
};
```

## Orchestrate Integration Hook

```typescript
// src/hooks/useOrchestrate.ts

import { useEffect, useState, useCallback } from 'react';
import { WXOConfiguration } from '../types/orchestrate.types';

interface UseOrchestrate {
  isLoaded: boolean;
  isInitialized: boolean;
  error: Error | null;
  reload: () => void;
}

export const useOrchestrate = (
  config: WXOConfiguration,
  containerId: string = 'orchestrate-chat-container'
): UseOrchestrate => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const loadOrchestrate = useCallback(() => {
    try {
      // Set configuration on window object
      window.wxOConfiguration = {
        ...config,
        rootElementID: containerId
      };

      // Create and load script
      const script = document.createElement('script');
      script.src = `${config.hostURL}/wxochat/wxoLoader.js?embed=true`;
      script.async = true;

      script.addEventListener('load', () => {
        setIsLoaded(true);
        
        // Initialize the chat widget
        if (window.wxoLoader) {
          try {
            window.wxoLoader.init();
            setIsInitialized(true);
          } catch (err) {
            setError(err as Error);
            console.error('Failed to initialize Orchestrate:', err);
          }
        }
      });

      script.addEventListener('error', (err) => {
        setError(new Error('Failed to load Orchestrate script'));
        console.error('Script load error:', err);
      });

      document.head.appendChild(script);

      // Cleanup function
      return () => {
        document.head.removeChild(script);
        delete window.wxOConfiguration;
        delete window.wxoLoader;
      };
    } catch (err) {
      setError(err as Error);
      console.error('Error setting up Orchestrate:', err);
    }
  }, [config, containerId]);

  useEffect(() => {
    const cleanup = loadOrchestrate();
    return cleanup;
  }, [loadOrchestrate]);

  const reload = useCallback(() => {
    setIsLoaded(false);
    setIsInitialized(false);
    setError(null);
    loadOrchestrate();
  }, [loadOrchestrate]);

  return { isLoaded, isInitialized, error, reload };
};
```

## Component Examples

### OrchestrateChatWidget Component
```typescript
// src/components/assistant/OrchestrateChatWidget.tsx

import React from 'react';
import { useOrchestrate } from '../../hooks/useOrchestrate';
import { WXOConfiguration } from '../../types/orchestrate.types';

interface OrchestrateChatWidgetProps {
  config: WXOConfiguration;
  className?: string;
}

export const OrchestrateChatWidget: React.FC<OrchestrateChatWidgetProps> = ({
  config,
  className = ''
}) => {
  const { isLoaded, isInitialized, error, reload } = useOrchestrate(
    config,
    'orchestrate-chat-container'
  );

  if (error) {
    return (
      <div className={`orchestrate-error ${className}`}>
        <p>Failed to load chat widget</p>
        <button onClick={reload}>Retry</button>
      </div>
    );
  }

  if (!isLoaded || !isInitialized) {
    return (
      <div className={`orchestrate-loading ${className}`}>
        <p>Loading chat...</p>
      </div>
    );
  }

  return (
    <div className={`orchestrate-container ${className}`}>
      <div id="orchestrate-chat-container" />
    </div>
  );
};
```

### DashboardLayout Component
```typescript
// src/components/layout/DashboardLayout.tsx

import React, { ReactNode } from 'react';
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
          <img src="/bcbsks-logo.svg" alt="BCBSKS" />
        </div>
        <div className="header-title">
          <h1>Customer Service Dashboard</h1>
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
```

## Styling Examples

### DashboardLayout CSS
```css
/* src/components/layout/DashboardLayout.css */

.dashboard-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f3f4f6;
}

.dashboard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  background-color: #ffffff;
  border-bottom: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.header-logo img {
  height: 40px;
}

.header-title h1 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.dashboard-main {
  display: flex;
  flex: 1;
  gap: 1.5rem;
  padding: 1.5rem;
  overflow: hidden;
}

.dashboard-left-panel {
  flex: 0 0 60%;
  background-color: #ffffff;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow-y: auto;
}

.dashboard-right-panel {
  flex: 0 0 calc(40% - 1.5rem);
  background-color: #ffffff;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow-y: auto;
}

@media (max-width: 1024px) {
  .dashboard-main {
    flex-direction: column;
  }
  
  .dashboard-left-panel,
  .dashboard-right-panel {
    flex: 1 1 auto;
  }
}
```

## Configuration Files

### Vite Config
```typescript
// vite.config.ts

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    open: true
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
});
```

### TypeScript Config
```json
// tsconfig.json

{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

This technical specification provides all the code examples and implementation details needed to build the dashboard.