# BCBSKS Customer Representative Dashboard - Plan Summary

## Executive Overview

This plan outlines the development of a modern, AI-powered customer service dashboard for BCBSKS representatives. The dashboard combines traditional case management with watsonx Orchestrate's AI capabilities to create an efficient, rep-focused workspace.

## Key Features

### 1. Split-Panel Dashboard Layout
- **Left Panel (60%)**: Customer and case information
- **Right Panel (40%)**: AI assistant with embedded watsonx Orchestrate

### 2. Customer Information Panel
- Case header with status and priority
- Tabbed interface (Details/Chatter)
- Comprehensive case metadata
- Member information display

### 3. AI Assistant Panel
- Case understanding with AI-generated summary
- Suggested next steps with actionable items
- Source citations and knowledge articles
- Embedded watsonx Orchestrate chat widget
- Quick action buttons

### 4. watsonx Orchestrate Integration
- Seamless embedding using provided script
- Real-time AI assistance for reps
- Grounded answers with citations
- Plain-language talk tracks
- Call summary generation

## Visual Design

### Layout Structure
```
┌─────────────────────────────────────────────────────────────┐
│                    BCBSKS Header                            │
├──────────────────────────────┬──────────────────────────────┤
│                              │                              │
│   Customer Information       │    AI Assistant Panel        │
│   ┌────────────────────┐    │   ┌────────────────────┐    │
│   │ Case Header        │    │   │ Case Assistant     │    │
│   │ - Title            │    │   │ - Summary          │    │
│   │ - Status Badge     │    │   │ - Tabs             │    │
│   └────────────────────┘    │   └────────────────────┘    │
│                              │                              │
│   ┌────────────────────┐    │   ┌────────────────────┐    │
│   │ Details Tab        │    │   │ Next Steps         │    │
│   │ - Subject          │    │   │ - Action items     │    │
│   │ - Description      │    │   │ - Sources          │    │
│   │ - Priority         │    │   └────────────────────┘    │
│   │ - Status           │    │                              │
│   │ - Owner            │    │   ┌────────────────────┐    │
│   └────────────────────┘    │   │ Action Buttons     │    │
│                              │   └────────────────────┘    │
│   ┌────────────────────┐    │                              │
│   │ Case Metadata      │    │   ┌────────────────────┐    │
│   │ - Member ID        │    │   │ Orchestrate Chat   │    │
│   │ - Policy Number    │    │   │ Widget             │    │
│   │ - LOB              │    │   │                    │    │
│   └────────────────────┘    │   └────────────────────┘    │
│                              │                              │
└──────────────────────────────┴──────────────────────────────┘
                                              ┌──────┐
                                              │ WXO  │ (Floating)
                                              └──────┘
```

## Technology Stack

### Frontend Framework
- **React 18+**: Modern component-based architecture
- **TypeScript**: Type-safe development
- **Vite**: Lightning-fast build tool

### Styling Approach
- **CSS Modules** or **Tailwind CSS**
- Salesforce Lightning Design System inspiration
- Responsive design for desktop and tablet

### State Management
- **React Context API**: Global state management
- **Custom Hooks**: Reusable logic (useOrchestrate, useCustomer)

### Integration
- **watsonx Orchestrate**: Script-based embedding
- **Mock Data**: Realistic BCBSKS scenarios

## Project Structure

```
bcbsks-rep-dashboard/
├── docs/                          # Documentation
│   ├── requirements.md            # Original requirements
│   ├── sample_ui.png              # UI reference
│   ├── implementation_plan.md     # Detailed implementation plan
│   ├── component_hierarchy.md     # Component structure
│   ├── technical_specifications.md # Code examples & specs
│   └── PLAN_SUMMARY.md            # This file
├── src/
│   ├── components/
│   │   ├── layout/                # Layout components
│   │   ├── customer/              # Customer panel components
│   │   └── assistant/             # AI assistant components
│   ├── context/                   # React Context providers
│   ├── data/                      # Mock data
│   ├── types/                     # TypeScript definitions
│   ├── hooks/                     # Custom React hooks
│   └── styles/                    # Global styles
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## Implementation Phases

### Phase 1: Foundation (Days 1-2)
- ✅ Set up Vite + React + TypeScript
- ✅ Create project structure
- ✅ Define TypeScript types
- ✅ Create mock data
- ✅ Set up basic styling

### Phase 2: Customer Panel (Days 3-4)
- ✅ Build CaseHeader component
- ✅ Implement Details/Chatter tabs
- ✅ Create CaseMetadata display
- ✅ Style to match sample UI

### Phase 3: Assistant Panel (Days 5-6)
- ✅ Create CaseAssistant component
- ✅ Implement SuggestedNextSteps
- ✅ Add action buttons
- ✅ Style assistant panel

### Phase 4: Orchestrate Integration (Day 7)
- ✅ Implement useOrchestrate hook
- ✅ Create OrchestrateChatWidget component
- ✅ Test embedding and initialization
- ✅ Handle error states

### Phase 5: Polish & Testing (Day 8)
- ✅ Responsive design
- ✅ Cross-browser testing
- ✅ Performance optimization
- ✅ Documentation

## Key Components

### 1. DashboardLayout
Main container managing the split-panel layout with responsive behavior.

### 2. CustomerPanel
Left panel displaying case and member information with tabbed interface.

### 3. AssistantPanel
Right panel with AI assistant features and embedded Orchestrate chat.

### 4. OrchestrateChatWidget
Handles watsonx Orchestrate embedding using the provided script configuration.

### 5. FloatingWXOButton
Bottom-right floating button for quick access to chat widget.

## watsonx Orchestrate Configuration

```javascript
window.wxOConfiguration = {
  orchestrationID: "ad4fa6953138448689fb746aade5025e_3f8fb562-4a6f-4cec-92a2-1172811cffee",
  hostURL: "https://us-south.watson-orchestrate.cloud.ibm.com",
  rootElementID: "orchestrate-chat-container",
  deploymentPlatform: "ibmcloud",
  crn: "crn:v1:bluemix:public:watsonx-orchestrate:us-south:a/ad4fa6953138448689fb746aade5025e:3f8fb562-4a6f-4cec-92a2-1172811cffee::",
  chatOptions: {
    agentId: "18015fee-4a97-4b2f-885d-fa9be453627b",
    agentEnvironmentId: "9cbdfa15-f4cc-4163-a6c2-248c9dd47aa8",
  }
};
```

## Mock Data Scenarios

### Scenario 1: Prior Authorization
- **Member**: John Smith (Medicare Advantage)
- **Issue**: Outpatient MRI imaging prior auth
- **Status**: In Progress
- **Priority**: High

### Scenario 2: Benefits Question
- **Member**: Sarah Johnson (Commercial)
- **Issue**: Out-of-network specialist coverage
- **Status**: New
- **Priority**: Medium

### Scenario 3: Claims Issue
- **Member**: Robert Davis (Medicaid)
- **Issue**: Claim denial inquiry
- **Status**: Pending
- **Priority**: High

## Success Criteria

### Functional Requirements
- ✅ Dashboard displays with split-panel layout
- ✅ Customer information loads from mock data
- ✅ watsonx Orchestrate embeds successfully
- ✅ All components are interactive
- ✅ Responsive design works on desktop/tablet

### Technical Requirements
- ✅ TypeScript compilation without errors
- ✅ Fast development server (<2s startup)
- ✅ Optimized production build
- ✅ Cross-browser compatibility
- ✅ Accessible design (WCAG 2.1 AA)

### User Experience Requirements
- ✅ Intuitive navigation
- ✅ Clear visual hierarchy
- ✅ Smooth animations
- ✅ Fast loading times (<3s)
- ✅ Professional appearance

## Next Steps

### Immediate Actions
1. **Review this plan** - Confirm approach and requirements
2. **Switch to Code mode** - Begin implementation
3. **Set up project** - Initialize Vite + React + TypeScript
4. **Create components** - Build dashboard iteratively
5. **Integrate Orchestrate** - Embed chat widget
6. **Test & refine** - Ensure quality and performance

### Future Enhancements
- Real API integration (replace mock data)
- Authentication and authorization
- CRM system integration
- Real-time updates via WebSockets
- Advanced analytics and reporting
- Multi-case workspace management

## Documentation References

For detailed information, refer to:
- **[implementation_plan.md](./implementation_plan.md)** - Complete implementation guide
- **[component_hierarchy.md](./component_hierarchy.md)** - Component structure and data flow
- **[technical_specifications.md](./technical_specifications.md)** - Code examples and API details
- **[requirements.md](./requirements.md)** - Original business requirements

## Estimated Timeline

- **Total Duration**: 8 working days
- **Phase 1 (Foundation)**: 2 days
- **Phase 2 (Customer Panel)**: 2 days
- **Phase 3 (Assistant Panel)**: 2 days
- **Phase 4 (Orchestrate)**: 1 day
- **Phase 5 (Polish)**: 1 day

## Questions or Modifications?

This plan is flexible and can be adjusted based on:
- Specific design preferences
- Additional feature requirements
- Integration needs
- Timeline constraints
- Technical constraints

Ready to proceed with implementation? Switch to **Code mode** to begin building!