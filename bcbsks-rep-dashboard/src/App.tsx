import React from 'react';
import { CustomerProvider } from './context/CustomerContext';
import { DashboardLayout } from './components/layout/DashboardLayout';
import { CustomerPanel } from './components/customer/CustomerPanel';
import { AssistantPanel } from './components/assistant/AssistantPanel';

function App() {
  return (
    <CustomerProvider>
      <DashboardLayout
        leftPanel={<CustomerPanel />}
        rightPanel={<AssistantPanel />}
      />
    </CustomerProvider>
  );
}

export default App;

// Made with Bob
