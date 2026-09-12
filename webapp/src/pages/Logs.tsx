import { useEffect, useState } from "react";
export default function Logs() {
	const [logs, setLogs] = useState<string[]>([]);
	useEffect(() => {
		fetch("/api/logs")
			.then((r) => r.json())
			.then((j) => setLogs(j.logs ?? []))
			.catch(() => {});
	}, []);
	return (
		<div>
			<h1 data-testid="logs-title">Logs</h1>
			<div data-testid="logs-tail">
				{logs.map((l, i) => (
					<div key={i} data-testid="logs-row">
						{l}
					</div>
				))}
			</div>
			<div data-testid="logs-empty">
				{logs.length === 0 ? "No logs yet" : ""}
			</div>
		</div>
	);
}
