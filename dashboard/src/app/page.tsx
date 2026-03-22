"use client";

import { useState } from "react";
import { PipelineStatus } from "@/components/PipelineStatus";
import { IntakeForm } from "@/components/IntakeForm";
import { ProjectList } from "@/components/ProjectList";

type View = "projects" | "new" | "detail";

export default function Home() {
  const [view, setView] = useState<View>("projects");
  const [selectedProject, setSelectedProject] = useState<any>(null);

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto", padding: "2rem" }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem", borderBottom: "1px solid #333", paddingBottom: "1rem" }}>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 600 }}>
          Kisasa AI PM Pipeline
        </h1>
        <nav style={{ display: "flex", gap: "1rem" }}>
          <button
            onClick={() => setView("projects")}
            style={navStyle(view === "projects")}
          >
            Projects
          </button>
          <button
            onClick={() => setView("new")}
            style={navStyle(view === "new")}
          >
            New Project
          </button>
        </nav>
      </header>

      <main>
        {view === "projects" && (
          <ProjectList
            onSelect={(project) => {
              setSelectedProject(project);
              setView("detail");
            }}
          />
        )}
        {view === "new" && (
          <IntakeForm
            onComplete={(result) => {
              setSelectedProject(result);
              setView("detail");
            }}
          />
        )}
        {view === "detail" && selectedProject && (
          <PipelineStatus project={selectedProject} />
        )}
      </main>
    </div>
  );
}

function navStyle(active: boolean): React.CSSProperties {
  return {
    padding: "0.5rem 1rem",
    borderRadius: 6,
    border: "1px solid #333",
    background: active ? "#1a1a2e" : "transparent",
    color: active ? "#fff" : "#888",
    cursor: "pointer",
    fontSize: "0.875rem",
  };
}
