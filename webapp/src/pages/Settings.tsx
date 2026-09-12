import { useState } from "react";
import { probeLlm } from "../lib/provider";
import { useLlm } from "../store/llm";
export default function Settings() {
	const { provider, model, setProvider, setModel } = useLlm();
	const [msg, setMsg] = useState("");
	async function probe() {
		setMsg(await probeLlm(provider));
	}
	return (
		<div>
			<h1 data-testid="settings-title">Settings</h1>
			<div data-testid="settings-llm">
				<input
					data-testid="settings-provider"
					value={provider}
					onChange={(e) => setProvider(e.target.value)}
					className="rounded bg-slate-900 px-2"
				/>
				<input
					data-testid="settings-model"
					value={model}
					onChange={(e) => setModel(e.target.value)}
					className="rounded bg-slate-900 px-2"
				/>
				<button
					type="button"
					data-testid="settings-probe"
					onClick={probe}
					className="rounded bg-slate-800 px-2"
				>
					Probe
				</button>
				<span data-testid="settings-result">{msg}</span>
			</div>
			<div data-testid="settings-health">
				Backend :11974 Frontend :11975. Health via /api/health.
			</div>
		</div>
	);
}
