from __future__ import annotations

"""JSON schemas passed to Claude to enforce exact output structure."""

BRIEF_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "client": {"type": "string"},
        "division": {"type": "string", "enum": ["ventures", "labs", "strategy"]},
        "problem_statement": {"type": "string"},
        "goals": {"type": "array", "items": {"type": "string"}},
        "constraints": {"type": "array", "items": {"type": "string"}},
        "scope": {"type": "string"},
        "stakeholders": {"type": "array", "items": {"type": "string"}},
        "suggested_timeline": {"type": "string"},
        "risk_flags": {"type": "array", "items": {"type": "string"}},
        "confidence_score": {"type": "number"},
    },
    "required": ["title", "client", "division", "problem_statement", "goals",
                  "constraints", "scope", "stakeholders", "suggested_timeline",
                  "risk_flags", "confidence_score"],
}

REPORT_SCHEMA = {
    "type": "object",
    "properties": {
        "project_title": {"type": "string"},
        "market_overview": {"type": "string"},
        "competitors": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "strengths": {"type": "array", "items": {"type": "string"}},
                    "weaknesses": {"type": "array", "items": {"type": "string"}},
                    "relevance": {"type": "string"},
                },
                "required": ["name", "description", "strengths", "weaknesses", "relevance"],
            },
        },
        "technical_feasibility": {"type": "string"},
        "recommended_tech_stack": {"type": "array", "items": {"type": "string"}},
        "risks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "description": {"type": "string"},
                    "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                    "mitigation": {"type": "string"},
                },
                "required": ["category", "description", "severity", "mitigation"],
            },
        },
        "go_no_go_recommendation": {"type": "string", "enum": ["go", "conditional_go", "no_go"]},
        "conditions": {"type": "array", "items": {"type": "string"}},
        "estimated_complexity": {"type": "string", "enum": ["low", "medium", "high"]},
        "next_steps": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["project_title", "market_overview", "competitors", "technical_feasibility",
                  "recommended_tech_stack", "risks", "go_no_go_recommendation", "conditions",
                  "estimated_complexity", "next_steps"],
}

ROADMAP_SCHEMA = {
    "type": "object",
    "properties": {
        "project_title": {"type": "string"},
        "client": {"type": "string"},
        "total_duration": {"type": "string"},
        "milestones": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "target_date": {"type": "string"},
                    "stories": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "description": {"type": "string"},
                                "acceptance_criteria": {"type": "array", "items": {"type": "string"}},
                                "effort_estimate": {"type": "string", "enum": ["small", "medium", "large", "xlarge"]},
                                "priority_score": {"type": "number"},
                                "labels": {"type": "array", "items": {"type": "string"}},
                            },
                            "required": ["title", "description", "acceptance_criteria", "effort_estimate", "priority_score", "labels"],
                        },
                    },
                    "success_criteria": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["name", "target_date", "stories", "success_criteria"],
            },
        },
        "dependencies": {"type": "array", "items": {"type": "string"}},
        "assumptions": {"type": "array", "items": {"type": "string"}},
        "out_of_scope": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["project_title", "client", "total_duration", "milestones",
                  "dependencies", "assumptions", "out_of_scope"],
}


def schema_instruction(schema: dict) -> str:
    """Generate a clear instruction string from a JSON schema for the prompt."""
    import json
    return f"\n\nYou MUST respond with a single JSON object (no markdown, no code blocks, no extra text) matching this exact schema:\n{json.dumps(schema, indent=2)}"
