# watsonx Orchestrate Embed Fix

## Issue
The watsonx Orchestrate chat widget was failing to initialize with the error:
```
wxO error ::: Bootstrap ::: Failed to load or mount the main application module. 
Error: Custom layout requires an HTMLElement. Got: undefined
```

## Root Cause
When using `layout.form: 'custom'`, watsonx Orchestrate requires an actual **HTMLElement reference** via the `layout.customElement` parameter, not just a string ID via `rootElementID`.

## Solution
Updated `orchestrateEmbed.tsx` to:

1. **Use React useRef hook** to get a reference to the container DOM element
2. **Pass the HTMLElement reference** to `layout.customElement` for custom layout
3. **Render a container div** that the chat widget can mount into
4. **Only use rootElementID** for fullscreen-overlay layout (as per documentation)

### Key Changes

```typescript
// Added useRef to get DOM element reference
const containerRef = useRef<HTMLDivElement>(null);

// Configure with actual HTMLElement for custom layout
window.wxOConfiguration = {
  // ... other config
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

// Return a container div with the ref
return (
  <div 
    ref={containerRef}
    id={rootElementId}
    className="orchestrate-container"
    style={{ width: '100%', height: '100%' }}
  >
    {/* Loading state */}
  </div>
);
```

## Layout Options

According to watsonx Orchestrate documentation, there are three layout forms:

### 1. **fullscreen-overlay** (Default)
- Displays chat in fullscreen mode
- Requires: `rootElementID` (string ID of container)
- Optional: `showLauncher` (boolean)

### 2. **float**
- Displays chat as a floating window
- Requires: `width` and `height` (e.g., '350px', '30rem')

### 3. **custom**
- Custom layout with full control
- **Requires: `customElement` (HTMLElement reference)**
- This is what we're using for the dashboard

## Testing
After this fix, the chat widget should initialize properly without the HTMLElement error. The widget will render inside the container div and fill the available space in the assistant panel.

## References
- [watsonx Orchestrate Layout Documentation](https://developer.watson-orchestrate.ibm.com/agents/integrate_agents)
- [Customizing the chat UI](https://developer.watson-orchestrate.ibm.com/webchat/customization_ui_configuration)