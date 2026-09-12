import { useCallback, useEffect, useState } from "react";
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

const ZOOM_LEVELS = [0.5, 0.6, 0.7, 0.8, 1.0, 1.25, 1.5, 2.0, 3.0];

function useZoom() {
	const [zoom, setZoom] = useState<number>(() => {
		try {
			const saved = localStorage.getItem("tauri-zoom");
			if (saved) {
				const val = Number.parseFloat(saved);
				if (ZOOM_LEVELS.includes(val)) return val;
			}
		} catch {
			/* ignore */
		}
		return 1.0;
	});

	const applyZoom = useCallback((newZoom: number) => {
		setZoom(newZoom);
		try {
			localStorage.setItem("tauri-zoom", String(newZoom));
		} catch {
			/* ignore */
		}
		document.documentElement.style.zoom = String(newZoom);
	}, []);

	useEffect(() => {
		applyZoom(zoom);
		const handleKeyDown = (e: KeyboardEvent) => {
			if (e.ctrlKey && (e.key === "0" || e.key === "Numpad0")) {
				e.preventDefault();
				applyZoom(1.0);
			}
		};

		const handleWheel = (e: WheelEvent) => {
			if (e.ctrlKey) {
				e.preventDefault();
				const currentIdx = ZOOM_LEVELS.indexOf(zoom);
				if (e.deltaY < 0) {
					// Zoom in
					const nextIdx = Math.min(currentIdx + 1, ZOOM_LEVELS.length - 1);
					applyZoom(ZOOM_LEVELS[nextIdx]);
				} else {
					// Zoom out
					const nextIdx = Math.max(currentIdx - 1, 0);
					applyZoom(ZOOM_LEVELS[nextIdx]);
				}
			}
		};

		window.addEventListener("keydown", handleKeyDown);
		window.addEventListener("wheel", handleWheel, { passive: false });
		return () => {
			window.removeEventListener("keydown", handleKeyDown);
			window.removeEventListener("wheel", handleWheel);
		};
	}, [zoom, applyZoom]);

	return { zoom, applyZoom };
}

export default function App() {
	const [open, setOpen] = useState(true);
	const [healthy, setHealthy] = useState<boolean | null>(null);
	const [q, setQ] = useState("");
	const { zoom } = useZoom();

	useEffect(() => {
		let timeoutId: number;
		let delay = 1000;

		const poll = async () => {
			const ok = await probeHealth();
			setHealthy(ok);
			if (ok) {
				delay = 4000;
			} else {
				delay = Math.min(delay * 2, 16000);
			}
			timeoutId = window.setTimeout(poll, delay);
		};

		void poll();
		return () => clearTimeout(timeoutId);
	}, []);

	return (
		<div className="min-h-screen bg-slate-950 text-slate-200">
			<header className="flex items-center gap-3 border-b border-slate-800 p-3">
				<button
					type="button"
					data-testid="sidebar-toggle"
					onClick={() => setOpen(!open)}
					className="rounded bg-slate-800 hover:bg-slate-700 px-3 py-1 text-sm text-slate-200"
				>
					Menu
				</button>
				<span className="font-bold text-slate-100">rss-mcp</span>
				<input
					data-testid="topbar-search"
					value={q}
					onChange={(e) => setQ(e.target.value)}
					placeholder="Search feeds..."
					className="ml-4 rounded-lg bg-slate-900 border border-slate-700 px-3 py-1 text-sm text-slate-200 focus:outline-none focus:border-amber-500"
				/>
				<div className="ml-auto flex items-center gap-3">
					<span
						data-testid="zoom-indicator"
						className="text-xs font-mono text-slate-300 px-2 py-0.5 rounded bg-slate-900 border border-slate-800"
						title="Ctrl+Scroll to zoom, Ctrl+0 to reset"
					>
						{Math.round(zoom * 100)}%
					</span>
					<div
						data-testid="health-dot"
						className="flex items-center gap-1.5 text-xs text-slate-300"
						title={healthy ? "Backend connected" : "Backend probing"}
					>
						<span
							className={`inline-block w-2.5 h-2.5 rounded-full ${
								healthy ? "bg-emerald-500" : "bg-amber-500 animate-pulse"
							}`}
						/>
						<span>{healthy ? "Backend: 11974" : "Connecting..."}</span>
					</div>
				</div>
			</header>
			<div className="flex">
				{open && (
					<nav className="w-52 space-y-1 border-r border-slate-800 p-3">
						{NAV.map((p) => (
							<Link
								key={p}
								to={p === "/" ? "/" : p}
								className="block rounded-lg px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-900 hover:text-slate-100 transition-colors"
							>
								{p === "/"
									? "Dashboard"
									: p.slice(1).charAt(0).toUpperCase() + p.slice(2)}
							</Link>
						))}
					</nav>
				)}
				<main className="flex-1 p-5">
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
