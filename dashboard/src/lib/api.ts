const API_BASE = "/api/pipeline";

export async function runPipeline(params: {
  raw_input?: string;
  slack_channel_id?: string;
  email_thread_id?: string;
  zoom_meeting_id?: string;
}) {
  const res = await fetch(`${API_BASE}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  return res.json();
}

export async function listProjects() {
  const res = await fetch(`${API_BASE}/projects`);
  return res.json();
}

export async function getProject(id: string) {
  const res = await fetch(`${API_BASE}/projects/${id}`);
  return res.json();
}

export async function syncToLinear(projectId: string, teamId: string) {
  const res = await fetch(`${API_BASE}/sync/linear`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project_id: projectId, team_id: teamId }),
  });
  return res.json();
}

export async function syncToNotion(projectId: string, databaseId: string) {
  const res = await fetch(`${API_BASE}/sync/notion`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project_id: projectId, database_id: databaseId }),
  });
  return res.json();
}
