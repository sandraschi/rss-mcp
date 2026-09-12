export async function probeHealth(): Promise<boolean> {
	try {
		const r = await fetch("/api/health");
		return r.ok;
	} catch {
		return false;
	}
}
export async function probeLlm(provider: string): Promise<string> {
	try {
		const r = await fetch("/api/llm/chat", {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ provider }),
		});
		const j = await r.json();
		return String(j.message ?? "unknown");
	} catch {
		return "unreachable";
	}
}
