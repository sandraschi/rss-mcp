import { useEffect, useState } from "react";
import { useLlm } from "../store/llm";
export default function Chat() {
	const { provider, model } = useLlm();
	const [msgs, setMsgs] = useState<string[]>([]);
	const [draft, setDraft] = useState("");
	useEffect(() => {
		try {
			const raw = localStorage.getItem("rss-mcp-chat-history");
			if (raw) setMsgs(JSON.parse(raw).slice(-100));
		} catch {
			/* empty */
		}
	}, []);
	function send() {
		const next = [...msgs, `${provider}/${model}: ${draft}`].slice(-100);
		setMsgs(next);
		try {
			localStorage.setItem("rss-mcp-chat-history", JSON.stringify(next));
		} catch {
			/* ignore */
		}
		setDraft("");
	}
	return (
		<div>
			<h1 data-testid="chat-title">Chat (skill-first)</h1>
			<div data-testid="chat-list">
				{msgs.map((m, i) => (
					<div key={i} data-testid="chat-row">
						{m}
					</div>
				))}
			</div>
			<div data-testid="chat-input-row">
				<input
					data-testid="chat-input"
					value={draft}
					onChange={(e) => setDraft(e.target.value)}
					className="rounded bg-slate-900 px-2"
				/>
				<button
					type="button"
					data-testid="chat-send"
					onClick={send}
					className="rounded bg-slate-800 px-2"
				>
					Send
				</button>
			</div>
			<div data-testid="chat-hint">
				Start from rss-expert skill. History capped at 100 in localStorage.
			</div>
		</div>
	);
}
