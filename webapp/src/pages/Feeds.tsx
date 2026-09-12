import { useEffect, useState } from "react";
export default function Feeds() {
	const [feeds, setFeeds] = useState<
		{ id: number; url: string; title: string }[]
	>([]);
	const [url, setUrl] = useState("");
	async function load() {
		const j = await fetch("/api/feeds").then((r) => r.json());
		setFeeds(j.feeds ?? []);
	}
	// biome-ignore lint/correctness/useExhaustiveDependencies: load is a stable local fetch wrapper
	useEffect(() => {
		load();
	}, []);
	async function refresh() {
		await fetch("/api/feeds/refresh", { method: "POST" });
		await load();
	}
	return (
		<div>
			<h1 data-testid="feeds-title">Feeds manager</h1>
			<div data-testid="feeds-add" className="flex gap-2">
				<input
					data-testid="feeds-url"
					value={url}
					onChange={(e) => setUrl(e.target.value)}
					placeholder="https://..."
					className="rounded bg-slate-900 px-2"
				/>
				<button
					type="button"
					data-testid="feeds-refresh"
					onClick={refresh}
					className="rounded bg-slate-800 px-3"
				>
					Refresh all
				</button>
				<span>{url ? "" : ""}</span>
			</div>
			<div data-testid="feeds-list">
				{feeds.map((f) => (
					<div key={f.id} data-testid="feeds-row">
						{f.title || f.url}
					</div>
				))}
				{feeds.length === 0 ? "No feeds yet" : ""}
			</div>
			<div data-testid="feeds-opml">
				OPML import/export via MCP tools feeds_ops.
			</div>
		</div>
	);
}
