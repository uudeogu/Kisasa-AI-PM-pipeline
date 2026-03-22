"use client";

const STAGES = [
  { key: "intake", label: "Intake" },
  { key: "research", label: "Research" },
  { key: "roadmap", label: "Roadmap" },
  { key: "build", label: "Build" },
  { key: "qa", label: "QA" },
  { key: "launch", label: "Launch" },
  { key: "retro", label: "Retro" },
];

const STAGE_ORDER = STAGES.map((s) => s.key);

function getStageState(stageKey: string, currentStatus: string) {
  const current = STAGE_ORDER.indexOf(currentStatus);
  const stage = STAGE_ORDER.indexOf(stageKey);

  if (stage < current) return "complete";
  if (stage === current) return "active";
  return "pending";
}

export function PipelineStatus({ project }: { project: any }) {
  const status = project.status || project.stage || "intake";
  const brief = project.brief;
  const report = project.report;
  const roadmap = project.roadmap;

  return (
    <div>
      <h2 style={{ fontSize: "1.25rem", marginBottom: "0.5rem" }}>
        {brief?.title || project.title || "Project"}
      </h2>
      <p style={{ color: "#888", fontSize: "0.875rem", marginBottom: "2rem" }}>
        {brief?.client || project.client} &middot; {brief?.division || project.division}
      </p>

      {/* Pipeline progress bar */}
      <div style={{ display: "flex", gap: "0.25rem", marginBottom: "2.5rem" }}>
        {STAGES.map((stage) => {
          const state = getStageState(stage.key, status);
          return (
            <div key={stage.key} style={{ flex: 1, textAlign: "center" }}>
              <div
                style={{
                  height: 4,
                  borderRadius: 2,
                  marginBottom: "0.5rem",
                  background:
                    state === "complete" ? "#22c55e" :
                    state === "active" ? "#3b82f6" :
                    "#333",
                }}
              />
              <span
                style={{
                  fontSize: "0.7rem",
                  color:
                    state === "complete" ? "#22c55e" :
                    state === "active" ? "#3b82f6" :
                    "#555",
                  fontWeight: state === "active" ? 600 : 400,
                }}
              >
                {stage.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Brief summary */}
      {brief && (
        <Section title="Project Brief">
          <Field label="Problem" value={brief.problem_statement} />
          <Field label="Goals" value={brief.goals?.join(", ")} />
          <Field label="Constraints" value={brief.constraints?.join(", ")} />
          <Field label="Timeline" value={brief.suggested_timeline} />
          <Field label="Confidence" value={`${(brief.confidence_score * 100).toFixed(0)}%`} />
          {brief.risk_flags?.length > 0 && (
            <Field label="Risk Flags" value={brief.risk_flags.join(", ")} />
          )}
        </Section>
      )}

      {/* Feasibility report */}
      {report && (
        <Section title="Feasibility Report">
          <Field label="Recommendation" value={report.go_no_go_recommendation} />
          <Field label="Complexity" value={report.estimated_complexity} />
          <Field label="Tech Stack" value={report.recommended_tech_stack?.join(", ")} />
          {report.risks?.length > 0 && (
            <div style={{ marginTop: "0.75rem" }}>
              <span style={fieldLabelStyle}>Risks</span>
              {report.risks.map((risk: any, i: number) => (
                <div key={i} style={{ padding: "0.5rem 0", borderBottom: "1px solid #222", fontSize: "0.8rem" }}>
                  <span style={{ color: risk.severity === "critical" ? "#ef4444" : risk.severity === "high" ? "#f59e0b" : "#888" }}>
                    [{risk.severity}]
                  </span>{" "}
                  {risk.description}
                </div>
              ))}
            </div>
          )}
        </Section>
      )}

      {/* Roadmap */}
      {roadmap && (
        <Section title="Roadmap">
          <Field label="Duration" value={roadmap.total_duration} />
          <Field label="Milestones" value={String(roadmap.milestones?.length)} />
          {roadmap.milestones?.map((milestone: any, i: number) => (
            <div key={i} style={{ marginTop: "1rem", padding: "1rem", border: "1px solid #222", borderRadius: 6 }}>
              <h4 style={{ margin: 0, fontSize: "0.9rem" }}>{milestone.name}</h4>
              <p style={{ margin: "0.25rem 0", color: "#888", fontSize: "0.75rem" }}>
                Target: {milestone.target_date} &middot; {milestone.stories?.length} stories
              </p>
              {milestone.stories?.map((story: any, j: number) => (
                <div key={j} style={{ padding: "0.5rem 0", borderTop: "1px solid #1a1a1a", fontSize: "0.8rem" }}>
                  <span style={{ color: "#ededed" }}>{story.title}</span>
                  <span style={{ color: "#555", marginLeft: "0.5rem" }}>
                    [{story.effort_estimate}]
                  </span>
                </div>
              ))}
            </div>
          ))}
        </Section>
      )}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: "2rem", padding: "1.25rem", border: "1px solid #333", borderRadius: 8 }}>
      <h3 style={{ margin: "0 0 1rem", fontSize: "1rem", color: "#aaa" }}>{title}</h3>
      {children}
    </div>
  );
}

function Field({ label, value }: { label: string; value?: string }) {
  if (!value) return null;
  return (
    <div style={{ marginBottom: "0.5rem", fontSize: "0.8rem" }}>
      <span style={fieldLabelStyle}>{label}: </span>
      <span style={{ color: "#ededed" }}>{value}</span>
    </div>
  );
}

const fieldLabelStyle: React.CSSProperties = {
  color: "#666",
  fontWeight: 500,
};
