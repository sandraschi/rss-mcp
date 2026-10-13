import { useEffect, useState } from "react";

type DiscoveredFeed = {
	url: string;
	title: string;
};

type CatalogFeed = {
	title: string;
	url: string;
	description: string;
	tags: string[];
};

type CatalogCategory = {
	category: string;
	feeds: CatalogFeed[];
};

type AiwatcherSource = {
	name: string;
	url: string;
	type: string;
};

type AiwatcherBundle = {
	id: string;
	name: string;
	description: string;
	interests: string[];
	sources: AiwatcherSource[];
};

export default function Discover() {
	const [probeUrl, setProbeUrl] = useState("");
	const [probing, setProbing] = useState(false);
	const [discovered, setDiscovered] = useState<DiscoveredFeed[]>([]);
	const [probeError, setProbeError] = useState<string | null>(null);

	const [catalog, setCatalog] = useState<CatalogCategory[]>([]);
	const [bundles, setBundles] = useState<AiwatcherBundle[]>([]);
	const [selectedCategory, setSelectedCategory] = useState<string>("All");

	const [subscribeStatus, setSubscribeStatus] = useState<{
		[key: string]: string;
	}>({});

	async function loadCatalogAndBundles() {
		try {
			const catRes = await fetch("/api/discover/catalog");
			const catData = await catRes.json();
			if (catData.categories) setCatalog(catData.categories);

			const bundleRes = await fetch("/api/aiwatcher/bundles");
			const bundleData = await bundleRes.json();
			if (bundleData.bundles) setBundles(bundleData.bundles);
		} catch {
			/* ignore */
		}
	}

	// biome-ignore lint/correctness/useExhaustiveDependencies: initial fetch
	useEffect(() => {
		loadCatalogAndBundles();
	}, []);

	async function handleProbe(e: React.FormEvent) {
		e.preventDefault();
		if (!probeUrl.trim()) return;
		setProbing(true);
		setProbeError(null);
		setDiscovered([]);

		try {
			const res = await fetch(
				`/api/discover?url=${encodeURIComponent(probeUrl.trim())}`,
			);
			const data = await res.json();
			if (data.success && data.feeds && data.feeds.length > 0) {
				setDiscovered(data.feeds);
			} else {
				setProbeError("No RSS or Atom feeds auto-detected on this website.");
			}
		} catch (err) {
			setProbeError(`Probe failed: ${String(err)}`);
		} finally {
			setProbing(false);
		}
	}

	async function handleSubscribe(url: string, title: string) {
		setSubscribeStatus((prev) => ({ ...prev, [url]: "Subscribing..." }));
		try {
			const res = await fetch("/mcp", {
				method: "POST",
				headers: { "Content-Type": "application/json" },
				body: JSON.stringify({
					jsonrpc: "2.0",
					id: 1,
					method: "tools/call",
					params: {
						name: "feeds_ops",
						arguments: { operation: "subscribe", url, title },
					},
				}),
			});
			const data = await res.json();
			if (data.result && !data.error) {
				setSubscribeStatus((prev) => ({ ...prev, [url]: "Subscribed!" }));
			} else {
				setSubscribeStatus((prev) => ({ ...prev, [url]: "Failed" }));
			}
		} catch {
			setSubscribeStatus((prev) => ({ ...prev, [url]: "Error" }));
		}
	}

	async function handleImportBundle(bundleId: string) {
		setSubscribeStatus((prev) => ({
			...prev,
			[`bundle_${bundleId}`]: "Importing...",
		}));
		try {
			const res = await fetch(`/api/aiwatcher/bundles/${bundleId}/import`, {
				method: "POST",
			});
			const data = await res.json();
			if (data.success) {
				setSubscribeStatus((prev) => ({
					...prev,
					[`bundle_${bundleId}`]: `Imported (${data.added_count} feeds)`,
				}));
			} else {
				setSubscribeStatus((prev) => ({
					...prev,
					[`bundle_${bundleId}`]: `Failed: ${data.message || "Error"}`,
				}));
			}
		} catch {
			setSubscribeStatus((prev) => ({
				...prev,
				[`bundle_${bundleId}`]: "Import failed",
			}));
		}
	}

	const categoriesList = ["All", ...catalog.map((c) => c.category)];
	const filteredCatalog =
		selectedCategory === "All"
			? catalog
			: catalog.filter((c) => c.category === selectedCategory);

	return (
		<div className="space-y-8" data-testid="discover-page">
			{/* Page Header */}
			<div className="border-b border-slate-800 pb-4">
				<h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
					<span className="text-indigo-400">⚡</span> RSS Feed Discovery & Fleet
					Hub
				</h1>
				<p className="text-sm text-slate-400">
					Discover feeds automatically from any website URL, explore curated
					tech & AI recommenders, or sync fleet bundles with AIWatcher.
				</p>
			</div>

			{/* URL Feed Finder Probe Section */}
			<div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
				<div>
					<h2 className="text-base font-semibold text-slate-100">
						Live Website URL Feed Finder
					</h2>
					<p className="text-xs text-slate-400">
						Enter any blog, news site, or publication URL. We probe HTML headers
						and known RSS/Atom endpoints to find direct feed links.
					</p>
				</div>
				<form onSubmit={handleProbe} className="flex gap-2">
					<input
						type="text"
						placeholder="e.g. simonwillison.net, nytimes.com, arstechnica.com..."
						value={probeUrl}
						onChange={(e) => setProbeUrl(e.target.value)}
						className="flex-1 rounded-lg bg-slate-950 border border-slate-700 px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
					/>
					<button
						type="submit"
						disabled={probing || !probeUrl.trim()}
						className="px-5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-sm font-semibold text-white transition-colors"
					>
						{probing ? "Probing..." : "Discover Feeds"}
					</button>
				</form>

				{probeError && (
					<div className="rounded-lg bg-rose-950/40 border border-rose-900/60 p-3 text-xs text-rose-300">
						{probeError}
					</div>
				)}

				{discovered.length > 0 && (
					<div className="space-y-2 pt-2">
						<h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
							Found {discovered.length} Feeds
						</h3>
						<div className="space-y-2">
							{discovered.map((feed) => (
								<div
									key={feed.url}
									className="flex items-center justify-between p-3 rounded-lg bg-slate-950/80 border border-slate-800"
								>
									<div className="truncate mr-4">
										<div className="text-sm font-medium text-slate-200">
											{feed.title}
										</div>
										<div className="text-xs text-slate-400 font-mono truncate">
											{feed.url}
										</div>
									</div>
									<button
										type="button"
										onClick={() => handleSubscribe(feed.url, feed.title)}
										disabled={subscribeStatus[feed.url] === "Subscribed!"}
										className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:bg-emerald-600/30 disabled:text-emerald-300 text-xs font-medium text-white transition-colors flex-shrink-0"
									>
										{subscribeStatus[feed.url] || "+ Subscribe"}
									</button>
								</div>
							))}
						</div>
					</div>
				)}
			</div>

			{/* AIWatcher Fleet Bundles Section */}
			{bundles.length > 0 && (
				<div className="rounded-xl border border-purple-900/40 bg-purple-950/10 p-5 space-y-4">
					<div className="flex items-center justify-between">
						<div>
							<h2 className="text-base font-semibold text-purple-200 flex items-center gap-2">
								<span>🌐</span> Fleet Bundles (AIWatcher Bridge)
							</h2>
							<p className="text-xs text-slate-400">
								Import curated fleet intelligence feeds defined in{" "}
								<code>bundles.json</code> directly into your RSS subscriptions.
							</p>
						</div>
					</div>
					<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
						{bundles.map((bundle) => {
							const statusKey = `bundle_${bundle.id}`;
							return (
								<div
									key={bundle.id}
									className="rounded-xl border border-purple-800/40 bg-slate-900/60 p-4 space-y-3"
								>
									<div className="flex items-start justify-between">
										<div>
											<h3 className="text-sm font-semibold text-purple-100">
												{bundle.name}
											</h3>
											<p className="text-xs text-slate-400 mt-0.5">
												{bundle.description}
											</p>
										</div>
										<button
											type="button"
											onClick={() => handleImportBundle(bundle.id)}
											disabled={subscribeStatus[statusKey]?.startsWith(
												"Imported",
											)}
											className="px-3 py-1 rounded bg-purple-600 hover:bg-purple-500 disabled:bg-purple-900/40 disabled:text-purple-300 text-xs font-medium text-white transition-colors flex-shrink-0"
										>
											{subscribeStatus[statusKey] || "Import Bundle"}
										</button>
									</div>
									<div className="flex items-center gap-1.5 flex-wrap">
										{bundle.interests.map((interest) => (
											<span
												key={interest}
												className="text-[10px] px-2 py-0.5 rounded bg-purple-950/80 border border-purple-800/50 text-purple-300 font-mono"
											>
												{interest}
											</span>
										))}
										<span className="text-[10px] text-slate-500 ml-auto font-mono">
											{bundle.sources.length} sources
										</span>
									</div>
								</div>
							);
						})}
					</div>
				</div>
			)}

			{/* Curated Recommenders Directory */}
			<div className="space-y-4">
				<div className="flex items-center justify-between flex-wrap gap-2">
					<h2 className="text-lg font-bold text-slate-100">
						Curated Topic Recommenders
					</h2>
					<div className="flex items-center gap-1.5 overflow-x-auto pb-1">
						{categoriesList.map((cat) => (
							<button
								key={cat}
								type="button"
								onClick={() => setSelectedCategory(cat)}
								className={`px-3 py-1 rounded-full text-xs font-medium transition-colors whitespace-nowrap ${
									selectedCategory === cat
										? "bg-indigo-600 text-white"
										: "bg-slate-900 hover:bg-slate-800 text-slate-400"
								}`}
							>
								{cat}
							</button>
						))}
					</div>
				</div>

				<div className="space-y-6">
					{filteredCatalog.map((cat) => (
						<div key={cat.category} className="space-y-3">
							<h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-2">
								<span className="w-2 h-2 rounded-full bg-indigo-500" />
								{cat.category}
							</h3>
							<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
								{cat.feeds.map((feed) => (
									<div
										key={feed.url}
										className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 space-y-2.5 hover:border-slate-700 transition-colors flex flex-col justify-between"
									>
										<div className="space-y-1">
											<div className="font-medium text-sm text-slate-200">
												{feed.title}
											</div>
											<p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
												{feed.description}
											</p>
										</div>
										<div className="space-y-2 pt-2 border-t border-slate-800/60">
											<div className="flex items-center gap-1 flex-wrap">
												{feed.tags.map((tag) => (
													<span
														key={tag}
														className="text-[10px] px-1.5 py-0.5 rounded bg-slate-950 border border-slate-800 text-slate-400"
													>
														{tag}
													</span>
												))}
											</div>
											<div className="flex items-center justify-between pt-1">
												<a
													href={feed.url}
													target="_blank"
													rel="noopener noreferrer"
													className="text-[11px] text-slate-500 hover:text-slate-300 font-mono truncate max-w-[140px]"
												>
													Feed URL
												</a>
												<button
													type="button"
													onClick={() => handleSubscribe(feed.url, feed.title)}
													disabled={subscribeStatus[feed.url] === "Subscribed!"}
													className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 disabled:bg-emerald-600/30 disabled:text-emerald-300 text-xs font-medium text-slate-200 transition-colors"
												>
													{subscribeStatus[feed.url] || "+ Subscribe"}
												</button>
											</div>
										</div>
									</div>
								))}
							</div>
						</div>
					))}
				</div>
			</div>
		</div>
	);
}
