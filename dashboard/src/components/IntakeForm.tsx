"use client";

import { useState } from "react";

type InputSource = "raw" | "slack" | "gmail" | "zoom";

export function IntakeForm({ onComplete }: { onComplete: (result: any) => void }) {
  const [source, setSource] = useState<InputSource>("raw");
  const [rawInput, setRawInput] = useState("");
  const [sourceId, setSourceId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");

    const body: Record<string, string> = {};
    if (source === "raw") body.raw_input = rawInput;
    if (source === "slack") body.slack_channel_id = sourceId;
    if (source === "gmail") body.email_thread_id = sourceId;
    if (source === "zoom") body.zoom_meeting_id = sourceId;

    try {
      const res = await fetch("/api/pipeline/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();

      if (!res.ok) {
        setError(data.error || "Pipeline failed");
      } else {
        onComplete(data);
      }
    } catch {
      setError("Failed to connect to pipeline");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ maxWidth: 640 }}>
      <h2 style={{ fontSize: "1.25rem", marginBottom: "1.5rem" }}>New Project Intake</h2>

      <div style={{ marginBottom: "1.5rem" }}>
        <label style={labelStyle}>Input Source</label>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          {(["raw", "slack", "gmail", "zoom"] as InputSource[]).map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setSource(s)}
              style={{
                padding: "0.5rem 1rem",
                borderRadius: 6,
                border: "1px solid #333",
                background: source === s ? "#1a1a2e" : "transparent",
                color: source === s ? "#fff" : "#888",
                cursor: "pointer",
                fontSize: "0.8rem",
                textTransform: "capitalize",
              }}
            >
              {s === "raw" ? "Paste Text" : s}
            </button>
          ))}
        </div>
      </div>

      {source === "raw" ? (
        <div style={{ marginBottom: "1.5rem" }}>
          <label style={labelStyle}>Client Input</label>
          <textarea
            value={rawInput}
            onChange={(e) => setRawInput(e.target.value)}
            placeholder="Paste client email, meeting notes, Slack conversation..."
            rows={10}
            style={inputStyle}
            required
          />
        </div>
      ) : (
        <div style={{ marginBottom: "1.5rem" }}>
          <label style={labelStyle}>
            {source === "slack" && "Slack Channel ID"}
            {source === "gmail" && "Gmail Thread ID"}
            {source === "zoom" && "Zoom Meeting ID"}
          </label>
          <input
            type="text"
            value={sourceId}
            onChange={(e) => setSourceId(e.target.value)}
            placeholder={
              source === "slack" ? "C0123456789" :
              source === "gmail" ? "thread-id" :
              "meeting-id"
            }
            style={inputStyle}
            required
          />
        </div>
      )}

      {error && (
        <p style={{ color: "#ef4444", fontSize: "0.875rem", marginBottom: "1rem" }}>
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={loading}
        style={{
          padding: "0.75rem 2rem",
          borderRadius: 6,
          border: "none",
          background: loading ? "#333" : "#3b82f6",
          color: "#fff",
          fontSize: "0.875rem",
          cursor: loading ? "not-allowed" : "pointer",
          fontWeight: 600,
        }}
      >
        {loading ? "Running Pipeline..." : "Run Pipeline"}
      </button>
    </form>
  );
}

const labelStyle: React.CSSProperties = {
  display: "block",
  marginBottom: "0.5rem",
  fontSize: "0.8rem",
  color: "#888",
  textTransform: "uppercase",
  letterSpacing: "0.05em",
};

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: "0.75rem",
  borderRadius: 6,
  border: "1px solid #333",
  background: "#111",
  color: "#ededed",
  fontSize: "0.875rem",
  fontFamily: "inherit",
  boxSizing: "border-box",
};
