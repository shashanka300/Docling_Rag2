# Anonymous Chat Access for BCBSKS Dashboard

## Overview
The BCBSKS customer representative dashboard is configured to allow **anonymous chat access** without requiring JWT authentication. This is suitable for demo and development purposes.

## Current Configuration

The dashboard is already set up for anonymous access. The `orchestrateEmbed.tsx` component does NOT include a `token` parameter in the `wxOConfiguration`, which allows anonymous users to access the chat.

### Configuration in AssistantPanel.tsx

```typescript
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
```

**Note**: No `token` prop is passed, which enables anonymous access.

## Security Considerations

According to watsonx Orchestrate documentation, anonymous access should only be used when:

1. ✅ **No sensitive data is exposed** - The demo uses mock customer data
2. ✅ **No tools with functional credentials are accessible** - The agent should be configured without sensitive tool access

## Watsonx Orchestrate Instance Configuration

To enable anonymous access on your watsonx Orchestrate instance:

1. Go to your watsonx Orchestrate instance settings
2. Navigate to **Security** settings for embedded chat
3. **Disable security** or ensure anonymous authentication is allowed
4. Verify that the agent doesn't have access to:
   - Sensitive data sources
   - Tools configured with functional credentials
   - Production systems

## When to Use JWT Authentication

For production deployments with sensitive data, you should implement JWT authentication:

### Required Steps:
1. Generate RSA key pair (client keys)
2. Obtain IBM's public key from watsonx Orchestrate
3. Create a server-side JWT generation endpoint
4. Pass the JWT token to the embed configuration

### Example with JWT:
```typescript
// Fetch JWT from your server
async function getIdentityToken() {
  const response = await fetch('http://localhost:5555/createJWT');
  return await response.text();
}

// Initialize with token
window.wxOConfiguration = {
  // ... other config
  token: await getIdentityToken(),
};
```

## Testing Anonymous Access

1. Start the development server:
   ```bash
   cd bcbsks-rep-dashboard
   npm run dev
   ```

2. Open the dashboard in your browser
3. The chat widget should initialize without requiring authentication
4. Users can interact with the agent anonymously

## Troubleshooting

### If chat fails to initialize:
1. Check browser console for errors
2. Verify the watsonx Orchestrate instance allows anonymous access
3. Ensure the `orchestrationId`, `agentId`, and `hostURL` are correct
4. Check that the agent environment is properly configured

### Common Errors:
- **"Authentication required"**: Security is enabled on the watsonx Orchestrate instance
- **"Invalid configuration"**: Check orchestrationId and agentId values
- **"Failed to load"**: Verify hostURL and network connectivity

## References
- [watsonx Orchestrate Security Architecture](https://developer.watson-orchestrate.ibm.com/_releases/1.15.0/agents/integrate_agents)
- [Integrating Agents with Web Applications](https://developer.watson-orchestrate.ibm.com/webchat/get_started)