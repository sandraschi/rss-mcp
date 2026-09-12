import { useEffect, useState } from "react";
import { probeLlm } from "../lib/provider";
import { useLlm } from "../store/llm";

export default function Settings() {
	const {
		provider,
		model,
		providers,
		setProvider,
		setModel,
		setProviders,
		gpuDetected,
		setGpuDetected,
	} = useLlm();

	const [msg, setMsg] = useState("");
	const [probing, setProbing] = useState(false);
	const [backendPorts, setBackendPorts] = useState<{
		backend: number;
		frontend: number;
	} | null>(null);

	const discoverProviders = async () => {
		try {
			const r = await fetch("/api/llm/discover");
			const j = await r.json();
			if (j.providers) setProviders(j.providers);
		} catch {
			/* ignore */
		}
	};

	// biome-ignore lint/correctness/useExhaustiveDependencies: mount discovery effect
	useEffect(() => {
		void discoverProviders();
		fetch("/api/capabilities")
			.then((r) => r.json())
			.then((j) => {
				if (j.ports) setBackendPorts(j.ports);
			})
			.catch(() => {});

		fetch("/api/llm/onboarding")
			.then((r) => r.json())
			.then((j) => {
				if (typeof j.gpu_detected === "boolean") setGpuDetected(j.gpu_detected);
			})
			.catch(() => {});
	}, [setProviders, setGpuDetected]);

	async function probe() {
		setProbing(true);
		try {
			const res = await probeLlm(provider);
			setMsg(res);
		} finally {
			setProbing(false);
		}
	}

	const activeProvider = providers.find((p) => p.id === provider);
	const availableModels = activeProvider?.models?.length
		? activeProvider.models
		: ["llama3", "mistral", "qwen2.5-coder", "phi3"];

	return (
		<div className="max-w-3xl space-y-6">
			<div>
				<h1
					data-testid="settings-title"
					className="text-xl font-bold text-slate-100"
				>
					Settings & Intelligence
				</h1>
				<p className="text-sm text-slate-300">
					Configure local LLM inference engines and system options for rss-mcp.
				</p>
			</div>

			<div
				data-testid="settings-llm"
				className="rounded-lg bg-slate-900/60 border border-slate-800 p-5 space-y-4"
			>
				<h2 className="text-base font-semibold text-slate-200">
					Local LLM Provider
				</h2>

				<div className="grid grid-cols-2 gap-3">
					{[
						{
							id: "ollama",
							name: "Ollama",
							defaultUrl: "http://127.0.0.1:11434",
						},
						{
							id: "lmstudio",
							name: "LM Studio",
							defaultUrl: "http://127.0.0.1:1234",
						},
					].map((p) => {
						const isSelected = provider === p.id;
						const detected = providers.find((pr) => pr.id === p.id)?.available;
						return (
							<button
								key={p.id}
								type="button"
								data-testid={`llm-provider-card-${p.id}`}
								onClick={() => setProvider(p.id)}
								className={`p-3 text-left rounded-lg border transition-colors ${
									isSelected
										? "border-amber-500 bg-amber-500/10 text-slate-100"
										: "border-slate-800 bg-slate-900 hover:border-slate-700 text-slate-300"
								}`}
							>
								<div className="flex items-center justify-between">
									<span className="font-medium text-sm">{p.name}</span>
									<span
										className={`inline-block w-2.5 h-2.5 rounded-full ${
											detected ? "bg-emerald-500" : "bg-slate-600"
										}`}
										title={detected ? "Detected online" : "Not detected"}
									/>
								</div>
								<div className="text-xs text-slate-400 mt-1 font-mono">
									{p.defaultUrl}
								</div>
							</button>
						);
					})}
				</div>

				<div className="grid grid-cols-2 gap-4 pt-2">
					<div>
						<label
							htmlFor="llm-provider-select"
							className="block text-xs font-medium text-slate-300 mb-1"
						>
							Selected Provider
						</label>
						<select
							id="llm-provider-select"
							data-testid="llm-provider-select"
							value={provider}
							onChange={(e) => setProvider(e.target.value)}
							className="w-full rounded bg-slate-900 border border-slate-700 px-3 py-1.5 text-sm text-slate-200"
						>
							<option value="ollama">Ollama (Default)</option>
							<option value="lmstudio">LM Studio</option>
							<option value="custom">Custom Endpoint</option>
						</select>
					</div>

					<div>
						<label
							htmlFor="llm-model-select"
							className="block text-xs font-medium text-slate-300 mb-1"
						>
							Inference Model
						</label>
						<select
							id="llm-model-select"
							data-testid="llm-model-select"
							value={model}
							onChange={(e) => setModel(e.target.value)}
							className="w-full rounded bg-slate-900 border border-slate-700 px-3 py-1.5 text-sm text-slate-200"
						>
							{availableModels.map((m) => (
								<option key={m} value={m}>
									{m}
								</option>
							))}
						</select>
					</div>
				</div>

				<div className="flex items-center gap-3 pt-2">
					<button
						type="button"
						data-testid="settings-probe"
						onClick={probe}
						disabled={probing}
						className="rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 disabled:opacity-50 px-4 py-1.5 text-sm font-medium text-slate-200 transition-colors"
					>
						{probing ? "Probing..." : "Test Connection"}
					</button>
					<button
						type="button"
						onClick={discoverProviders}
						className="rounded bg-slate-800/80 hover:bg-slate-700 border border-slate-700 px-3 py-1.5 text-sm text-slate-300 transition-colors"
					>
						Re-probe Providers
					</button>
					{msg && (
						<span
							data-testid="settings-result"
							className="text-xs text-slate-300 font-mono"
						>
							{msg}
						</span>
					)}
				</div>
			</div>

			{gpuDetected && (
				<div className="rounded-lg bg-emerald-950/40 border border-emerald-800/60 p-4 text-sm text-emerald-200">
					<strong>GPU Acceleration Available:</strong> Dedicated graphics
					hardware detected for fast local FastEmbed & LLM token generation.
				</div>
			)}

			<div
				data-testid="settings-health"
				className="rounded-lg bg-slate-900/60 border border-slate-800 p-4 text-sm text-slate-300 space-y-1"
			>
				<div className="font-semibold text-slate-200">System Information</div>
				<div>
					Backend Port:{" "}
					<span className="font-mono text-amber-400">
						{backendPorts ? backendPorts.backend : "..."}
					</span>{" "}
					| Frontend Port:{" "}
					<span className="font-mono text-amber-400">
						{backendPorts ? backendPorts.frontend : "..."}
					</span>
				</div>
				<div className="text-xs text-slate-400">
					Health probe available via{" "}
					<code className="text-slate-300">/api/health</code>. All storage
					persisted locally in SQLite + LanceDB.
				</div>
			</div>
		</div>
	);
}
