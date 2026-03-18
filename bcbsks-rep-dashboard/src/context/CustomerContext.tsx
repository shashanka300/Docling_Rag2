import React, { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';
import type { CaseContext, NextStep } from '../types/customer.types';
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
            await new Promise(resolve => setTimeout(resolve, 1000));
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

// Made with Bob
