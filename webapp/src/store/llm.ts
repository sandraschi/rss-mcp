import { create } from "zustand";

type ProviderInfo = {
	id: string;
	name: string;
	url: string;
	models?: string[];
	available?: boolean;
};

type LlmState = {
	provider: string;
	model: string;
	providers: ProviderInfo[];
	gpuDetected: boolean;
	setProvider: (p: string) => void;
	setModel: (m: string) => void;
	setProviders: (list: ProviderInfo[]) => void;
	setGpuDetected: (val: boolean) => void;
};

const initialProvider = localStorage.getItem("llm_provider") || "ollama";
const initialModel = localStorage.getItem("llm_model") || "llama3";

export const useLlm = create<LlmState>((set) => ({
	provider: initialProvider,
	model: initialModel,
	providers: [],
	gpuDetected: false,
	setProvider: (provider) => {
		try {
			localStorage.setItem("llm_provider", provider);
		} catch {
			/* ignore */
		}
		set({ provider });
	},
	setModel: (model) => {
		try {
			localStorage.setItem("llm_model", model);
		} catch {
			/* ignore */
		}
		set({ model });
	},
	setProviders: (providers) => set({ providers }),
	setGpuDetected: (gpuDetected) => set({ gpuDetected }),
}));
