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

// Made with Bob
