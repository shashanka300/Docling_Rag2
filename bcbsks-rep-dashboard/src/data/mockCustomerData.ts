import type { Member, Case, CaseContext, Source, NextStep } from '../types/customer.types';

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

// Made with Bob
