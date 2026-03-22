"use client";

import { useState, useEffect } from "react";

interface Project {
  id: string;
  title: string;
  client: string;
  division: string;
  status: string;
  created_at: string;
}

const STAGE_COLORS: Record<string, string> = {
  intake: "#3b82f6",
  research: "#8b5cf6",
  roadmap: "#f59e0b",
  build: "#10b981",
  qa: "#06b6d4",
  launch: "#ec4899",
  retro: "#6366f1",
  complete: "#22c55e",
};

export function ProjectList({ onSelect }: { onSelect: (project: Project) => void }) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/pipeline/projects")
      .then((res) => res.json())
      .then((data) => {
        setProjects(data.projects || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {
    return <p style={{ color: "#888" }}>Loading projects...</p>;
  }

  if (projects.length === 0) {
    return (
      <div style={{ textAlign: "center", padding: "4rem 0" }}>
        <p style={{ color: "#888", fontSize: "1.1rem" }}>No projects yet</p>
        <p style={{ color: "#666", fontSize: "0.875rem" }}>
          Create a new project to get started with the pipeline.
        </p>
      </div>
    );
  }

  return (
    <div style={{ display: "grid", gap: "1rem" }}>
      {projects.map((project) => (
        <div
          key={project.id}
          onClick={() => onSelect(project)}
          style={{
            padding: "1.25rem",
            border: "1px solid #333",
            borderRadius: 8,
            cursor: "pointer",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            transition: "border-color 0.2s",
          }}
          onMouseEnter={(e) => (e.currentTarget.style.borderColor = "#555")}
          onMouseLeave={(e) => (e.currentTarget.style.borderColor = "#333")}
        >
          <div>
            <h3 style={{ margin: 0, fontSize: "1rem" }}>{project.title}</h3>
            <p style={{ margin: "0.25rem 0 0", color: "#888", fontSize: "0.8rem" }}>
              {project.client} &middot; {project.division}
            </p>
          </div>
          <span
            style={{
              padding: "0.25rem 0.75rem",
              borderRadius: 12,
              fontSize: "0.75rem",
              fontWeight: 600,
              background: STAGE_COLORS[project.status] || "#333",
              color: "#fff",
            }}
          >
            {project.status}
          </span>
        </div>
      ))}
    </div>
  );
}
