import { create } from "zustand";

type LlmState = {
	provider: string;
	model: string;
	setProvider: (p: string) => void;
	setModel: (m: string) => void;
};
export const useLlm = create<LlmState>((set) => ({
	provider: "ollama",
	model: "llama3",
	setProvider: (provider) => set({ provider }),
	setModel: (model) => set({ model }),
}));
