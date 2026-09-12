import { useEffect, useState } from "react";
type Feed = { id: number; url: string; title: string };
type Item = { id: number; title: string; link: string; summary: string };
export default function Reader() {
	const [feeds, setFeeds] = useState<Feed[]>([]);
	const [items, setItems] = useState<Item[]>([]);
	const [text, setText] = useState("");
	const [fid, setFid] = useState<number | null>(null);
	useEffect(() => {
		fetch("/api/feeds")
			.then((r) => r.json())
			.then((j) => setFeeds(j.feeds ?? []))
			.catch(() => {});
		fetch("/api/inbox")
			.then((r) => r.json())
			.then((j) => setItems(j.items ?? []))
			.catch(() => {});
	}, []);
	async function openItem(id: number) {
		const r = await fetch("/api/readability/extract", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ item_id: id }),
		}).then((x) => x.json());
		setText(String(r.text ?? r.message ?? ""));
	}
	return (
		<div data-testid="reader-page" className="grid grid-cols-3 gap-2">
			<div data-testid="reader-feeds" className="rounded bg-slate-900 p-2">
				{feeds.map((f) => (
					<button
						type="button"
						key={f.id}
						data-testid={`feed-${f.id}`}
						onClick={() => setFid(f.id)}
						className="block w-full text-left hover:bg-slate-800"
					>
						{f.title || f.url}
					</button>
				))}
				{feeds.length === 0 ? "No feeds" : ""}
				<span>{fid ?? ""}</span>
			</div>
			<div data-testid="reader-items" className="rounded bg-slate-900 p-2">
				{items.map((i) => (
					<button
						type="button"
						key={i.id}
						data-testid={`item-${i.id}`}
						onClick={() => openItem(i.id)}
						className="block w-full text-left hover:bg-slate-800"
					>
						{i.title}
					</button>
				))}
				{items.length === 0 ? "Inbox empty" : ""}
			</div>
			<div
				data-testid="reader-text"
				className="whitespace-pre-wrap rounded bg-slate-900 p-2"
			>
				{text || "Pick an item for clean text"}
			</div>
		</div>
	);
}
