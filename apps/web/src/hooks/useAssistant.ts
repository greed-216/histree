import { createContext, useContext, useEffect } from 'react';
import type { AskContext } from '../lib/ask';
export type AssistantScope = { key: string; title: string; label: string; context?: AskContext; prompt?: string; suggestions: string[] };
export type AssistantRequest = { question: string; selectedText?: string; serial: number };
type AssistantValue = { scope: AssistantScope; open: boolean; request: AssistantRequest | null; show: (question?: string, selectedText?: string) => void; close: () => void; handled: () => void; register: (scope: AssistantScope) => () => void };
export const AssistantContext = createContext<AssistantValue | null>(null);
export function useAssistant() {
  const value = useContext(AssistantContext);
  if (!value) throw new Error('AssistantProvider is required');
  return value;
}
export function useAssistantScope(scope: AssistantScope | null) {
  const { register } = useAssistant();
  const serialized = JSON.stringify(scope);
  useEffect(() => { if (serialized !== 'null') return register(JSON.parse(serialized)); }, [register, serialized]);
}
