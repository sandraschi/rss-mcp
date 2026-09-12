import { useEffect, useState } from "react";
export default function Inbox() {
	const [items, setItems] = useState<{ id: number; title: string }[]>([]);
	useEffect(() => {
		fetch("/api/inbox")
			.then((r) => r.json())
			.then((j) => setItems(j.items ?? []))
			.catch(() => {});
	}, []);
	return (
		<div>
			<h1 data-testid="inbox-title">Inbox</h1>
			<div data-testid="inbox-list">
				{items.map((i) => (
					<div key={i.id} data-testid="inbox-row">
						{i.title}
					</div>
				))}
			</div>
			<div data-testid="inbox-empty">
				{items.length === 0 ? "All caught up" : ""}
			</div>
		</div>
	);
}
