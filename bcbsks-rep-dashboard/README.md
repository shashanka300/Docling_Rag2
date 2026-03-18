# BCBSKS Customer Representative Dashboard

A modern, AI-powered customer service dashboard for BCBSKS representatives that integrates watsonx Orchestrate for intelligent assistance.

## Features

- **Split-Panel Dashboard**: Customer information on the left, AI assistant on the right
- **Case Management**: View and manage customer cases with detailed information
- **Member Information**: Access comprehensive member details and policy information
- **AI Assistant**: Embedded watsonx Orchestrate chat widget for real-time assistance
- **Case Summary**: AI-generated case summaries with knowledge articles and expert recommendations
- **Suggested Next Steps**: Actionable items with source citations
- **Responsive Design**: Works on desktop and tablet devices
- **Floating WXO Button**: Quick access to AI features

## Technology Stack

- **React 18+**: Modern component-based UI framework
- **TypeScript**: Type-safe development
- **Vite**: Lightning-fast build tool and dev server
- **watsonx Orchestrate**: AI-powered assistant integration
- **CSS Modules**: Component-scoped styling

## Project Structure

```
bcbsks-rep-dashboard/
├── src/
│   ├── components/
│   │   ├── layout/              # Layout components
│   │   │   ├── DashboardLayout.tsx
│   │   │   ├── DashboardLayout.css
│   │   │   ├── FloatingWXOButton.tsx
│   │   │   └── FloatingWXOButton.css
│   │   ├── customer/            # Customer panel components
│   │   │   ├── CustomerPanel.tsx
│   │   │   ├── CaseHeader.tsx
│   │   │   ├── CaseDetails.tsx
│   │   │   ├── CaseMetadata.tsx
│   │   │   └── *.css
│   │   └── assistant/           # AI assistant components
│   │       ├── AssistantPanel.tsx
│   │       ├── CaseAssistant.tsx
│   │       ├── SuggestedNextSteps.tsx
│   │       ├── ActionButtons.tsx
│   │       ├── OrchestrateChatWidget.tsx
│   │       └── *.css
│   ├── context/
│   │   └── CustomerContext.tsx  # Global state management
│   ├── data/
│   │   └── mockCustomerData.ts  # Mock data for demo
│   ├── hooks/
│   │   └── useOrchestrate.ts    # Orchestrate integration hook
│   ├── types/
│   │   ├── customer.types.ts    # TypeScript type definitions
│   │   └── orchestrate.types.ts
│   ├── App.tsx                  # Main application component
│   ├── main.tsx                 # Application entry point
│   └── index.css                # Global styles
├── public/
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

1. Navigate to the project directory:
```bash
cd bcbsks-rep-dashboard
```

2. Install dependencies (already done):
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

4. Open your browser and navigate to:
```
http://localhost:3000
```

### Build for Production

```bash
npm run build
```

The production-ready files will be in the `dist` directory.

### Preview Production Build

```bash
npm run preview
```

## Configuration

### watsonx Orchestrate Configuration

The Orchestrate configuration is located in `src/components/assistant/AssistantPanel.tsx`:

```typescript
const orchestrateConfig = {
  orchestrationID: "your-orchestration-id",
  hostURL: "https://us-south.watson-orchestrate.cloud.ibm.com",
  rootElementID: "orchestrate-chat-container",
  deploymentPlatform: "ibmcloud",
  crn: "your-crn",
  chatOptions: {
    agentId: "your-agent-id",
    agentEnvironmentId: "your-environment-id",
  }
};
```

Update these values with your actual watsonx Orchestrate credentials.

### Mock Data

Mock customer and case data is defined in `src/data/mockCustomerData.ts`. You can:

- Add more mock cases
- Modify existing case scenarios
- Update member information
- Customize suggested next steps

## Component Overview

### Layout Components

- **DashboardLayout**: Main container with header and split-panel layout
- **FloatingWXOButton**: Bottom-right floating button for quick access

### Customer Panel Components

- **CustomerPanel**: Container for customer information with tabs
- **CaseHeader**: Displays case title, status, and priority
- **CaseDetails**: Shows detailed case and member information
- **CaseMetadata**: Additional metadata fields

### Assistant Panel Components

- **AssistantPanel**: Container for AI assistant features
- **CaseAssistant**: Case summary with tabs (Summary/Knowledge/Experts)
- **SuggestedNextSteps**: Actionable items with source citations
- **ActionButtons**: Quick action buttons
- **OrchestrateChatWidget**: Embedded watsonx Orchestrate chat

## Customization

### Styling

Global CSS variables are defined in `src/index.css`:

```css
:root {
  --primary-blue: #0176d3;
  --light-blue: #e0f2fe;
  --navy: #1e3a8a;
  /* ... more variables */
}
```

Modify these to match your brand colors.

### Adding New Cases

Edit `src/data/mockCustomerData.ts`:

```typescript
export const mockCases: Case[] = [
  {
    id: 'case-003',
    caseNumber: 'CS-2024-001236',
    subject: 'Your Case Subject',
    // ... more fields
  }
];
```

### Integrating Real APIs

Replace mock data with API calls:

1. Create API service files in `src/services/`
2. Update `CustomerContext` to fetch from APIs
3. Add loading and error states
4. Implement data refresh mechanisms

## Features in Detail

### Case Management

- View case details including subject, description, priority, and status
- Track case history and modifications
- Access member information alongside case data

### AI Assistant

- **Case Summary**: AI-generated overview of the case
- **Knowledge Articles**: Related documentation and policies
- **Subject Matter Experts**: Recommended experts for consultation
- **Suggested Next Steps**: Actionable items with checkboxes
- **Source Citations**: Links to policy documents with metadata

### watsonx Orchestrate Integration

The dashboard embeds watsonx Orchestrate using a custom hook:

```typescript
const { isLoaded, isInitialized, error, reload } = useOrchestrate(config);
```

Features:
- Automatic script loading
- Error handling and retry mechanism
- Loading states
- Clean initialization

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Troubleshooting

### Orchestrate Widget Not Loading

1. Check console for errors
2. Verify configuration credentials
3. Ensure network connectivity to Orchestrate servers
4. Try the reload button in the widget

### TypeScript Errors

```bash
npm run build
```

Check for type errors and fix them before running the dev server.

### Styling Issues

Clear browser cache and hard reload:
- Chrome/Edge: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
- Firefox: Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)

## Future Enhancements

- [ ] Real API integration
- [ ] Authentication and authorization
- [ ] Multi-case workspace
- [ ] Real-time updates via WebSockets
- [ ] Advanced search and filtering
- [ ] Export case data
- [ ] Print-friendly views
- [ ] Dark mode support
- [ ] Accessibility improvements
- [ ] Performance optimizations

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

Internal use only - BCBSKS

## Support

For questions or issues, contact the development team.

---

Built with ❤️ for BCBSKS Customer Service Representatives
