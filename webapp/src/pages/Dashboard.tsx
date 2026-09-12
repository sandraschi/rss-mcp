import { useEffect, useState } from "react";
type Stats = {
	feeds: number;
	items: number;
	unread: number;
	starred: number;
	extracts: number;
};
export default function Dashboard({ query }: { query: string }) {
	const [stats, setStats] = useState<Stats | null>(null);
	useEffect(() => {
		fetch("/api/dashboard")
			.then((r) => r.json())
			.then((j) => setStats(j.stats ?? null))
			.catch(() => setStats(null));
	}, []);
	return (
		<div data-testid="dashboard">
			<section
				data-testid="dashboard-hero"
				className="rounded bg-slate-900 p-6"
			>
				<h1 className="text-2xl font-bold text-slate-100">
					Local RSS without ad sites
				</h1>
				<p className="text-slate-300">
					Subscribe, refresh, read clean text. Query: {query}
				</p>
			</section>
			<div data-testid="dashboard-kpis" className="mt-4 grid grid-cols-5 gap-2">
				{(["feeds", "items", "unread", "starred", "extracts"] as const).map(
					(k) => (
						<div
							key={k}
							data-testid={`kpi-${k}`}
							className="rounded bg-slate-900 p-3 text-slate-200"
						>
							<span className="text-slate-300 font-medium">{k}:</span>{" "}
							{stats ? stats[k] : "loading"}
						</div>
					),
				)}
			</div>
			<div data-testid="dashboard-empty" className="mt-4 text-slate-300">
				{stats && stats.feeds === 0
					? "No feeds yet. Add one on the Feeds page."
					: ""}
			</div>
		</div>
	);
}
