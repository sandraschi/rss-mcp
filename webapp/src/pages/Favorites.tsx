import { useEffect, useState } from "react";

type Collection = {
	id: number;
	name: string;
	description: string;
	color: string;
	item_count: number;
};

type StarredItem = {
	id: number;
	title: string;
	link: string;
	feed_title?: string;
	published: number;
	summary: string;
	note?: string;
	collections?: { id: number; name: string; color: string }[];
};

export default function Favorites() {
	const [items, setItems] = useState<StarredItem[]>([]);
	const [collections, setCollections] = useState<Collection[]>([]);
	const [selectedCollection, setSelectedCollection] = useState<number | null>(
		null,
	);
	const [activeNoteItem, setActiveNoteItem] = useState<StarredItem | null>(
		null,
	);
	const [noteText, setNoteText] = useState("");
	const [newCollName, setNewCollName] = useState("");
	const [newCollDesc, setNewCollDesc] = useState("");
	const [newCollColor, setNewCollColor] = useState("#3b82f6");
	const [promoteStatus, setPromoteStatus] = useState<string | null>(null);

	async function loadCollections() {
		try {
			const res = await fetch("/api/faves/collections");
			const data = await res.json();
			if (data.collections) setCollections(data.collections);
		} catch {
			/* ignore */
		}
	}

	async function loadStarred(collId: number | null) {
		try {
			const url = collId ? `/api/faves?collection_id=${collId}` : "/api/faves";
			const res = await fetch(url);
			const data = await res.json();
			if (data.items) setItems(data.items);
		} catch {
			/* ignore */
		}
	}

	// biome-ignore lint/correctness/useExhaustiveDependencies: load on collection change
	useEffect(() => {
		loadCollections();
		loadStarred(selectedCollection);
	}, [selectedCollection]);

	async function handleCreateCollection(e: React.FormEvent) {
		e.preventDefault();
		if (!newCollName.trim()) return;
		try {
			const res = await fetch("/api/faves/collections", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					name: newCollName.trim(),
					description: newCollDesc.trim(),
					color: newCollColor,
				}),
			});
			const data = await res.json();
			if (data.success) {
				setNewCollName("");
				setNewCollDesc("");
				await loadCollections();
			}
		} catch {
			/* ignore */
		}
	}

	async function handleDeleteCollection(id: number) {
		try {
			await fetch(`/api/faves/collections/${id}`, { method: "DELETE" });
			if (selectedCollection === id) setSelectedCollection(null);
			await loadCollections();
		} catch {
			/* ignore */
		}
	}

	async function handleSaveNote() {
		if (!activeNoteItem) return;
		try {
			await fetch(`/api/faves/items/${activeNoteItem.id}/note`, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({ note: noteText }),
			});
			setActiveNoteItem(null);
			await loadStarred(selectedCollection);
		} catch {
			/* ignore */
		}
	}

	async function handleToggleItemCollection(
		itemId: number,
		collId: number,
		isMember: boolean,
	) {
		try {
			await fetch(`/api/faves/items/${itemId}/collections`, {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					collection_id: collId,
					action: isMember ? "remove" : "add",
				}),
			});
			await loadStarred(selectedCollection);
			await loadCollections();
		} catch {
			/* ignore */
		}
	}

	async function handlePromoteToAiwatcher(itemId: number) {
		setPromoteStatus("Promoting to AIWatcher...");
		try {
			const res = await fetch(`/api/aiwatcher/promote/${itemId}`, {
				method: "POST",
			});
			const data = await res.json();
			if (data.success) {
				setPromoteStatus(
					data.staged ? "Staged for AIWatcher" : "Promoted to AIWatcher Inbox!",
				);
			} else {
				setPromoteStatus(`Failed: ${data.message || "Unknown error"}`);
			}
			setTimeout(() => setPromoteStatus(null), 4000);
		} catch {
			setPromoteStatus("Failed to contact AIWatcher bridge");
			setTimeout(() => setPromoteStatus(null), 4000);
		}
	}

	function handleExport(format: "markdown" | "json") {
		const url = selectedCollection
			? `/api/faves/export?format=${format}&collection_id=${selectedCollection}`
			: `/api/faves/export?format=${format}`;
		window.open(url, "_blank");
	}

	return (
		<div className="space-y-6" data-testid="favorites-page">
			<div className="flex items-center justify-between border-b border-slate-800 pb-4">
				<div>
					<h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
						<span className="text-amber-400">★</span> Starred & Faves
						Collections
					</h1>
					<p className="text-sm text-slate-400">
						Curate favorite articles into topics, add personal notes, and sync
						high-priority items to AIWatcher.
					</p>
				</div>
				<div className="flex items-center gap-2">
					{promoteStatus && (
						<span className="text-xs px-2.5 py-1 rounded bg-amber-500/20 text-amber-300 font-medium animate-fade">
							{promoteStatus}
						</span>
					)}
					<button
						type="button"
						onClick={() => handleExport("markdown")}
						className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 border border-slate-700 transition-colors"
					>
						Export Markdown
					</button>
					<button
						type="button"
						onClick={() => handleExport("json")}
						className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 border border-slate-700 transition-colors"
					>
						Export JSON
					</button>
				</div>
			</div>

			<div className="grid grid-cols-1 md:grid-cols-4 gap-6">
				{/* Collections Sidebar */}
				<div className="md:col-span-1 space-y-4">
					<div className="rounded-xl border border-slate-800 bg-slate-900/50 p-4 space-y-3">
						<h2 className="text-sm font-semibold text-slate-200">
							Collections
						</h2>
						<div className="space-y-1">
							<button
								type="button"
								onClick={() => setSelectedCollection(null)}
								className={`w-full text-left px-3 py-2 rounded-lg text-xs font-medium flex items-center justify-between transition-colors ${
									selectedCollection === null
										? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
										: "text-slate-300 hover:bg-slate-800/60"
								}`}
							>
								<span>All Starred</span>
								<span className="text-xs opacity-75">{items.length}</span>
							</button>
							{collections.map((c) => (
								<div
									key={c.id}
									className={`group flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
										selectedCollection === c.id
											? "bg-blue-500/20 text-blue-300 border border-blue-500/30"
											: "text-slate-300 hover:bg-slate-800/60"
									}`}
								>
									<button
										type="button"
										onClick={() => setSelectedCollection(c.id)}
										className="flex items-center gap-2 flex-1 text-left truncate"
									>
										<span
											className="w-2.5 h-2.5 rounded-full flex-shrink-0"
											style={{ backgroundColor: c.color }}
										/>
										<span className="truncate">{c.name}</span>
									</button>
									<div className="flex items-center gap-1.5 opacity-60 group-hover:opacity-100">
										<span className="text-[11px] font-mono">
											{c.item_count}
										</span>
										<button
											type="button"
											title="Delete Collection"
											onClick={() => handleDeleteCollection(c.id)}
											className="text-slate-400 hover:text-rose-400 px-1"
										>
											×
										</button>
									</div>
								</div>
							))}
						</div>

						{/* Add Collection Form */}
						<form
							onSubmit={handleCreateCollection}
							className="pt-3 border-t border-slate-800/80 space-y-2"
						>
							<span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
								New Collection
							</span>
							<input
								type="text"
								placeholder="Collection name"
								value={newCollName}
								onChange={(e) => setNewCollName(e.target.value)}
								className="w-full rounded bg-slate-950 border border-slate-800 px-2.5 py-1 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
							/>
							<input
								type="text"
								placeholder="Description (optional)"
								value={newCollDesc}
								onChange={(e) => setNewCollDesc(e.target.value)}
								className="w-full rounded bg-slate-950 border border-slate-800 px-2.5 py-1 text-xs text-slate-200 focus:outline-none focus:border-blue-500"
							/>
							<div className="flex items-center gap-2">
								<input
									type="color"
									value={newCollColor}
									onChange={(e) => setNewCollColor(e.target.value)}
									className="w-7 h-7 rounded border-0 cursor-pointer bg-transparent"
								/>
								<button
									type="submit"
									disabled={!newCollName.trim()}
									className="flex-1 py-1 rounded bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-xs font-medium text-white transition-colors"
								>
									Add Collection
								</button>
							</div>
						</form>
					</div>
				</div>

				{/* Starred Items List */}
				<div className="md:col-span-3 space-y-3">
					{items.length === 0 ? (
						<div className="p-8 text-center rounded-xl border border-dashed border-slate-800 text-slate-400 text-sm">
							No starred items in this collection yet. Star articles in the
							Reader or Inbox!
						</div>
					) : (
						items.map((it) => (
							<div
								key={it.id}
								className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 space-y-3 hover:border-slate-700 transition-colors"
							>
								<div className="flex items-start justify-between gap-4">
									<div className="space-y-1">
										<div className="flex items-center gap-2">
											<span className="text-amber-400">★</span>
											<span className="text-xs font-semibold text-slate-400">
												{it.feed_title || "Feed"}
											</span>
											<span className="text-[11px] text-slate-500">
												{new Date(it.published * 1000).toLocaleDateString()}
											</span>
										</div>
										<a
											href={it.link}
											target="_blank"
											rel="noopener noreferrer"
											className="text-base font-semibold text-slate-100 hover:text-amber-300 transition-colors inline-block"
										>
											{it.title || "Untitled Article"}
										</a>
									</div>
									<div className="flex items-center gap-2">
										<button
											type="button"
											onClick={() => {
												setActiveNoteItem(it);
												setNoteText(it.note || "");
											}}
											className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 border border-slate-700"
										>
											{it.note ? "Edit Note" : "+ Note"}
										</button>
										<button
											type="button"
											title="Send to AIWatcher for morning briefings & TTS alerts"
											onClick={() => handlePromoteToAiwatcher(it.id)}
											className="px-2.5 py-1 rounded bg-purple-950/60 hover:bg-purple-900/80 text-purple-300 border border-purple-800/60 text-xs"
										>
											Promote to AIWatcher
										</button>
									</div>
								</div>

								{/* User Note if present */}
								{it.note && (
									<div className="rounded-lg bg-amber-950/20 border border-amber-900/40 p-2.5 text-xs text-amber-200">
										<span className="font-semibold text-amber-400 block mb-0.5">
											Note:
										</span>
										<p className="whitespace-pre-wrap">{it.note}</p>
									</div>
								)}

								{/* Summary snippet */}
								{it.summary && (
									<p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
										{it.summary}
									</p>
								)}

								{/* Item Collections tags & dropdown */}
								<div className="flex items-center gap-2 pt-2 border-t border-slate-800/60 flex-wrap">
									<span className="text-[11px] text-slate-500 font-medium">
										Collections:
									</span>
									{collections.map((c) => {
										const isMember =
											it.collections?.some((ic) => ic.id === c.id) ?? false;
										return (
											<button
												type="button"
												key={c.id}
												onClick={() =>
													handleToggleItemCollection(it.id, c.id, isMember)
												}
												className={`text-[11px] px-2 py-0.5 rounded-md font-medium transition-all ${
													isMember
														? "text-white border shadow-sm"
														: "text-slate-400 bg-slate-950/60 hover:bg-slate-800 border border-slate-800 opacity-60"
												}`}
												style={
													isMember
														? {
																backgroundColor: `${c.color}33`,
																borderColor: c.color,
																color: c.color,
															}
														: {}
												}
											>
												{isMember ? "✓ " : "+ "}
												{c.name}
											</button>
										);
									})}
								</div>
							</div>
						))
					)}
				</div>
			</div>

			{/* Edit Note Modal */}
			{activeNoteItem && (
				<div className="fixed inset-0 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4 z-50">
					<div className="rounded-xl border border-slate-800 bg-slate-900 p-5 max-w-lg w-full space-y-4 shadow-xl">
						<h3 className="text-sm font-semibold text-slate-200">
							Personal Note:{" "}
							<span className="text-amber-300 font-normal">
								{activeNoteItem.title}
							</span>
						</h3>
						<textarea
							rows={4}
							value={noteText}
							onChange={(e) => setNoteText(e.target.value)}
							placeholder="Add your takeaways, thoughts, or research notes..."
							className="w-full rounded-lg bg-slate-950 border border-slate-800 p-3 text-xs text-slate-200 focus:outline-none focus:border-amber-500"
						/>
						<div className="flex justify-end gap-2">
							<button
								type="button"
								onClick={() => setActiveNoteItem(null)}
								className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300"
							>
								Cancel
							</button>
							<button
								type="button"
								onClick={handleSaveNote}
								className="px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-xs font-semibold text-white"
							>
								Save Note
							</button>
						</div>
					</div>
				</div>
			)}
		</div>
	);
}
