import { useEffect, useState } from "react";
import { Link, Route, Routes } from "react-router-dom";
import { probeHealth } from "./lib/provider";
import Chat from "./pages/Chat";
import Dashboard from "./pages/Dashboard";
import Feeds from "./pages/Feeds";
import Help from "./pages/Help";
import Inbox from "./pages/Inbox";
import Logs from "./pages/Logs";
import RagOperations from "./pages/RagOperations";
import Reader from "./pages/Reader";
import Settings from "./pages/Settings";
import Skills from "./pages/Skills";
import Tools from "./pages/Tools";

const NAV = [
	"/",
	"/reader",
	"/feeds",
	"/inbox",
	"/tools",
	"/rag",
	"/skills",
	"/chat",
	"/settings",
	"/help",
	"/logs",
];

export default function App() {
	const [open, setOpen] = useState(true);
	const [healthy, setHealthy] = useState<boolean | null>(null);
	const [q, setQ] = useState("");
	useEffect(() => {
		probeHealth().then(setHealthy);
	}, []);
	return (
		<div className="min-h-screen bg-slate-950 text-slate-200">
			<header className="flex items-center gap-3 border-b border-slate-800 p-3">
				<button
					type="button"
					data-testid="sidebar-toggle"
					onClick={() => setOpen(!open)}
					className="rounded bg-slate-800 px-3 py-1"
				>
					Menu
				</button>
				<span className="font-bold">rss-mcp</span>
				<input
					data-testid="topbar-search"
					value={q}
					onChange={(e) => setQ(e.target.value)}
					placeholder="Search feeds"
					className="ml-4 rounded bg-slate-900 px-3 py-1"
				/>
				<span data-testid="health-dot" title={healthy ? "healthy" : "unknown"}>
					{healthy ? "OK" : "..."}
				</span>
			</header>
			<div className="flex">
				{open && (
					<nav className="w-48 space-y-1 border-r border-slate-800 p-3">
						{NAV.map((p) => (
							<Link
								key={p}
								to={p === "/" ? "/" : p}
								className="block rounded px-2 py-1 hover:bg-slate-800"
							>
								{p === "/" ? "Dashboard" : p.slice(1)}
							</Link>
						))}
					</nav>
				)}
				<main className="flex-1 p-4">
					<Routes>
						<Route path="/" element={<Dashboard query={q} />} />
						<Route path="/reader" element={<Reader />} />
						<Route path="/feeds" element={<Feeds />} />
						<Route path="/inbox" element={<Inbox />} />
						<Route path="/tools" element={<Tools />} />
						<Route path="/rag" element={<RagOperations />} />
						<Route path="/skills" element={<Skills />} />
						<Route path="/chat" element={<Chat />} />
						<Route path="/settings" element={<Settings />} />
						<Route path="/help" element={<Help />} />
						<Route path="/logs" element={<Logs />} />
					</Routes>
				</main>
			</div>
		</div>
	);
}
