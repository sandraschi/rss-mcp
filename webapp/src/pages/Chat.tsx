import { useEffect, useState } from "react";
import { useLlm } from "../store/llm";

type Message = {
	role: "user" | "assistant" | "system";
	content: string;
};

const PERSONALITIES = [
	{
		id: "assistant",
		name: "Assistant",
		desc: "Helpful, balanced RSS reader guide",
	},
	{
		id: "scholar",
		name: "Scholar",
		desc: "Academic depth, citations and context",
	},
	{
		id: "journalist",
		name: "Journalist",
		desc: "Fact-focused, inverted pyramid summaries",
	},
	{ id: "concise", name: "Concise", desc: "Short bullet points, zero filler" },
	{ id: "custom", name: "Custom", desc: "User-defined prompt persona" },
];

const EXAMPLE_PROMPTS = [
	"What are the top 3 unread stories in my inbox?",
	"Summarize the latest tech news from my subscribed feeds",
	"Search for articles about artificial intelligence or LLMs",
	"Which feeds haven't published anything in the last 7 days?",
	"Clean and extract the main points of article #1",
	"Trigger an incremental semantic indexing sweep",
];

export default function Chat() {
	const { provider, model } = useLlm();
	const [msgs, setMsgs] = useState<Message[]>([]);
	const [draft, setDraft] = useState("");
	const [personality, setPersonality] = useState("assistant");
	const [skillPrompt, setSkillPrompt] = useState("");
	const [loading, setLoading] = useState(false);

	useEffect(() => {
		fetch("/api/skills")
			.then((r) => r.json())
			.then((j) => {
				const exp = j.skills?.find(
					(s: { name: string }) => s.name === "rss-expert",
				);
				if (exp?.content) setSkillPrompt(exp.content);
			})
			.catch(() => {});

		try {
			const raw = localStorage.getItem("rss-mcp-chat-history");
			if (raw) {
				const parsed = JSON.parse(raw);
				if (Array.isArray(parsed)) setMsgs(parsed.slice(-100));
			}
		} catch {
			/* ignore */
		}
	}, []);

	const saveHistory = (updated: Message[]) => {
		setMsgs(updated);
		try {
			localStorage.setItem(
				"rss-mcp-chat-history",
				JSON.stringify(updated.slice(-100)),
			);
		} catch {
			/* ignore */
		}
	};

	async function send(textToSend?: string) {
		const text = textToSend ?? draft;
		if (!text.trim() || loading) return;

		const userMsg: Message = { role: "user", content: text };
		const next = [...msgs, userMsg].slice(-100);
		saveHistory(next);
		setDraft("");
		setLoading(true);

		try {
			const selectedP = PERSONALITIES.find((p) => p.id === personality);
			const systemInstruction = `You are the rss-mcp AI assistant (${selectedP?.name}). Skill context: ${skillPrompt.slice(0, 1000)}`;

			const res = await fetch("/api/chat", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					provider,
					model,
					messages: [{ role: "system", content: systemInstruction }, ...next],
				}),
			});
			const data = await res.json();
			const replyContent =
				data.message || data.response || "No response received.";
			saveHistory(
				[...next, { role: "assistant" as const, content: replyContent }].slice(
					-100,
				),
			);
		} catch {
			saveHistory(
				[
					...next,
					{
						role: "assistant" as const,
						content:
							"Unable to reach backend chat endpoint. Ensure server is running on :11974.",
					},
				].slice(-100),
			);
		} finally {
			setLoading(false);
		}
	}

	function clearChat() {
		setMsgs([]);
		try {
			localStorage.removeItem("rss-mcp-chat-history");
		} catch {
			/* ignore */
		}
	}

	function exportChat() {
		if (msgs.length === 0) return;
		const content = msgs
			.map((m) => `[${m.role.toUpperCase()}]:\n${m.content}\n`)
			.join("\n---\n\n");
		const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
		const url = URL.createObjectURL(blob);
		const a = document.createElement("a");
		a.href = url;
		a.download = `rss-mcp-chat-${Date.now()}.txt`;
		a.click();
		URL.revokeObjectURL(url);
	}

	return (
		<div data-testid="chat-page" className="flex flex-col h-[calc(100vh-6rem)]">
			<div className="flex items-center justify-between pb-3 border-b border-slate-800">
				<div>
					<h1
						data-testid="chat-title"
						className="text-xl font-bold text-slate-100"
					>
						Chat & Intelligence
					</h1>
					<p className="text-sm text-slate-300">
						Skill-first agent: loads{" "}
						<code className="text-amber-400">rss-expert</code> on mount
					</p>
				</div>
				<div data-testid="chat-controls" className="flex items-center gap-2">
					<span className="text-xs px-2 py-1 rounded bg-slate-900 text-slate-300 border border-slate-700">
						{provider}/{model}
					</span>
					<select
						data-testid="personality-select"
						value={personality}
						onChange={(e) => setPersonality(e.target.value)}
						className="rounded bg-slate-900 border border-slate-700 px-2 py-1 text-sm text-slate-200"
					>
						{PERSONALITIES.map((p) => (
							<option key={p.id} value={p.id}>
								{p.name}
							</option>
						))}
					</select>
					<button
						type="button"
						data-testid="chat-export"
						onClick={exportChat}
						disabled={msgs.length === 0}
						className="rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-50 px-3 py-1 text-sm text-slate-200"
					>
						Export
					</button>
					<button
						type="button"
						data-testid="chat-clear"
						onClick={clearChat}
						disabled={msgs.length === 0}
						className="rounded bg-slate-800 hover:bg-rose-900 disabled:opacity-50 px-3 py-1 text-sm text-slate-200"
					>
						Clear
					</button>
				</div>
			</div>

			<div
				data-testid="chat-messages"
				className="flex-1 overflow-y-auto py-4 space-y-3"
			>
				{msgs.length === 0 ? (
					<div
						data-testid="chat-empty"
						className="rounded-lg bg-slate-900/60 border border-slate-800 p-6 text-center"
					>
						<h2 className="text-lg font-medium text-slate-200">
							Welcome to rss-mcp AI Reader
						</h2>
						<p className="mt-1 text-sm text-slate-300 max-w-lg mx-auto">
							Ask questions about your subscribed feeds, summarize unread
							articles, or perform vector searches over your cached stories.
						</p>
						<div
							data-testid="example-prompts"
							className="mt-4 flex flex-wrap gap-2 justify-center"
						>
							{EXAMPLE_PROMPTS.map((prompt, i) => (
								<button
									key={i}
									type="button"
									onClick={() => send(prompt)}
									className="rounded-full bg-slate-800 hover:bg-slate-700 border border-slate-700 px-3 py-1 text-xs text-slate-200 transition-colors"
								>
									{prompt}
								</button>
							))}
						</div>
					</div>
				) : (
					msgs.map((m, i) => (
						<div
							key={i}
							data-testid="chat-row"
							className={`p-3 rounded-lg max-w-3xl ${
								m.role === "user"
									? "ml-auto bg-amber-600/20 border border-amber-600/40 text-slate-100"
									: "mr-auto bg-slate-900 border border-slate-800 text-slate-200"
							}`}
						>
							<div className="text-xs font-semibold text-slate-400 mb-1">
								{m.role === "user" ? "You" : `rss-mcp (${model})`}
							</div>
							<div className="whitespace-pre-wrap text-sm leading-relaxed">
								{m.content}
							</div>
						</div>
					))
				)}
				{loading && (
					<div className="text-xs text-slate-400 animate-pulse">
						Thinking...
					</div>
				)}
			</div>

			<div
				data-testid="chat-input-row"
				className="pt-2 border-t border-slate-800 flex gap-2"
			>
				<input
					data-testid="chat-input"
					value={draft}
					onChange={(e) => setDraft(e.target.value)}
					onKeyDown={(e) => {
						if (e.key === "Enter" && !e.shiftKey) {
							e.preventDefault();
							send();
						}
					}}
					placeholder="Ask about your RSS feeds or articles..."
					className="flex-1 rounded-lg bg-slate-900 border border-slate-700 px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-amber-500"
				/>
				<button
					type="button"
					data-testid="chat-send"
					onClick={() => send()}
					disabled={!draft.trim() || loading}
					className="rounded-lg bg-amber-600 hover:bg-amber-500 disabled:opacity-50 px-4 py-2 text-sm font-medium text-black transition-colors"
				>
					Send
				</button>
			</div>
		</div>
	);
}
