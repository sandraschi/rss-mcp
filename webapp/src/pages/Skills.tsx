import { useEffect, useState } from "react";
export default function Skills() {
	const [skills, setSkills] = useState<{ name: string; content: string }[]>([]);
	useEffect(() => {
		fetch("/api/skills")
			.then((r) => r.json())
			.then((j) => setSkills(j.skills ?? []))
			.catch(() => {});
	}, []);
	return (
		<div>
			<h1 data-testid="skills-title">Skills</h1>
			<div data-testid="skills-list">
				{skills.map((s) => (
					<div key={s.name} data-testid="skills-row">
						<b>{s.name}</b>
						<pre>{s.content.slice(0, 2000)}</pre>
					</div>
				))}
			</div>
			<div data-testid="skills-empty">
				{skills.length === 0 ? "No skills" : ""}
			</div>
		</div>
	);
}
