import { useEffect, useState } from "react";

type Stats = {
	total_vectors: number;
	model: string;
	dims: number;
	engine: string;
	items: number;
	last_sweep: { at: number | null; chunks: number; mode: string | null };
};

export default function RagOperations() {
	const [stats, setStats] = useState<Stats | null>(null);
	const [jobId, setJobId] = useState("");
	const [status, setStatus] = useState("");
	const [mode, setMode] = useState("incremental");

	const load = async () => {
		const r = await fetch("/api/rag/stats").then((x) => x.json());
		setStats(r);
	};

	// biome-ignore lint/correctness/useExhaustiveDependencies: mount + jobId polling effect
	useEffect(() => {
		void load();
		const t = setInterval(() => {
			if (jobId) {
				fetch(`/api/rag/sweep/${jobId}`)
					.then((x) => x.json())
					.then((j) => setStatus(`${j.status} ${j.chunks}`));
			}
		}, 1200);
		return () => clearInterval(t);
	}, [jobId]);

	const sweep = async () => {
		const r = await fetch("/api/rag/sweep", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ mode, hours: 4 }),
		}).then((x) => x.json());
		setJobId(r.job_id);
		setStatus("queued");
	};

	return (
		<div>
			<h1 data-testid="rag-title" className="text-xl font-bold">
				RAG / Index Operations
			</h1>
			<div className="mt-3 grid grid-cols-4 gap-3">
				<div data-testid="rag-vectors" className="rounded bg-slate-900 p-3">
					Vectors: {stats?.total_vectors ?? "-"}
				</div>
				<div data-testid="rag-engine" className="rounded bg-slate-900 p-3">
					Engine: {stats?.engine ?? "-"}
				</div>
				<div data-testid="rag-model" className="rounded bg-slate-900 p-3">
					Model: {stats?.model ?? "-"}
				</div>
				<div data-testid="rag-items" className="rounded bg-slate-900 p-3">
					Items: {stats?.items ?? "-"}
				</div>
			</div>
			<div className="mt-4 flex gap-2">
				<select
					data-testid="rag-mode"
					value={mode}
					onChange={(e) => setMode(e.target.value)}
					className="rounded bg-slate-900 px-3 py-1"
				>
					<option value="incremental">Incremental (4h)</option>
					<option value="full">Full (rebuild)</option>
				</select>
				<button
					type="button"
					data-testid="rag-sweep"
					onClick={sweep}
					className="rounded bg-amber-600 px-4 py-1 text-black"
				>
					Start sweep
				</button>
				<span data-testid="rag-status">{status}</span>
			</div>
			<p className="mt-3 text-sm text-slate-400">
				Sweeps run as background jobs. This page polls job status every 1.2s, no
				request timeout aborts the backend job.
			</p>
		</div>
	);
}
