import { useEffect, useState } from "react";
export default function Tools() {
	const [tools, setTools] = useState<{ name: string; ops: string[] }[]>([]);
	const [sel, setSel] = useState("");
	useEffect(() => {
		fetch("/api/tools")
			.then((r) => r.json())
			.then((j) => setTools(j.tools ?? []))
			.catch(() => {});
	}, []);
	return (
		<div>
			<h1 data-testid="tools-title">Tools</h1>
			<div data-testid="tools-list">
				{tools.map((t) => (
					<button
						type="button"
						key={t.name}
						data-testid={`tool-${t.name}`}
						onClick={() => setSel(t.name)}
						className="mr-2 rounded bg-slate-800 px-2"
					>
						{t.name}
					</button>
				))}
			</div>
			<div data-testid="tools-detail">
				{sel
					? tools.find((t) => t.name === sel)?.ops.join(", ")
					: "Pick a tool (discovered live, never hardcoded)"}
			</div>
			<div data-testid="tools-note">Dynamic discovery from /api/tools.</div>
		</div>
	);
}
