export default function Help() {
	return (
		<div>
			<h1 data-testid="help-title">Help</h1>
			<div data-testid="help-arch">
				Ports 11974 backend, 11975 frontend. Env RSS_MCP_DB, RSS_MCP_PORT,
				RSS_MCP_HOST.
			</div>
			<div data-testid="help-flows">
				Subscribe, refresh_all, extract clean text, search, sweep jobs.
			</div>
			<div data-testid="help-glace">
				glance-mcp is the lightweight holdall. rss-mcp is the full stateful
				reader.
			</div>
		</div>
	);
}
