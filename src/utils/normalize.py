from __future__ import annotations


def _to_string_list(value) -> list[str]:
    """Convert various formats to a flat list of strings."""
    if isinstance(value, list):
        return [str(item) if not isinstance(item, str) else item for item in value]
    if isinstance(value, str):
        # Split comma-separated strings
        return [s.strip() for s in value.split(",") if s.strip()]
    if isinstance(value, dict):
        return [f"{k}: {v}" for k, v in value.items()]
    return [str(value)]


def _to_string(value) -> str:
    """Convert various formats to a single string."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        parts = []
        for k, v in value.items():
            if isinstance(v, list):
                parts.append(f"{k}: {', '.join(str(i) for i in v)}")
            else:
                parts.append(f"{k}: {v}")
        return ". ".join(parts)
    if isinstance(value, list):
        return ", ".join(str(i) for i in value)
    return str(value)


def normalize_brief(data: dict) -> dict:
    """Normalize Claude's response to match ProjectBrief schema."""
    if isinstance(data.get("constraints"), (dict, str)):
        data["constraints"] = _to_string_list(data["constraints"])
    if data.get("constraints") and isinstance(data["constraints"][0], dict):
        data["constraints"] = [_to_string(c) for c in data["constraints"]]

    if not isinstance(data.get("scope"), str):
        data["scope"] = _to_string(data["scope"])

    if data.get("stakeholders") and not isinstance(data["stakeholders"][0], str):
        data["stakeholders"] = [
            f"{s.get('name', '')} ({s.get('role', '')})" if isinstance(s, dict) else str(s)
            for s in data["stakeholders"]
        ]

    if not isinstance(data.get("suggested_timeline"), str):
        data["suggested_timeline"] = _to_string(data["suggested_timeline"])

    if data.get("risk_flags") and not isinstance(data["risk_flags"][0], str):
        data["risk_flags"] = [
            r.get("risk", r.get("description", _to_string(r))) if isinstance(r, dict) else str(r)
            for r in data["risk_flags"]
        ]

    if data.get("goals") and not isinstance(data["goals"][0], str):
        data["goals"] = [_to_string(g) for g in data["goals"]]

    return data


def _flatten_list_of_dicts(items: list) -> list[str]:
    """Convert a list that may contain dicts into a flat list of strings."""
    result = []
    for item in items:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict):
            # Pick the most descriptive value
            for key in ("action", "description", "name", "risk", "step", "item"):
                if key in item:
                    result.append(str(item[key]))
                    break
            else:
                result.append(_to_string(item))
        else:
            result.append(str(item))
    return result


def normalize_report(data) -> dict:
    """Normalize Claude's response to match FeasibilityReport schema."""
    # If Claude returned a list, take the first dict element
    if isinstance(data, list):
        data = data[0] if data and isinstance(data[0], dict) else {"error": str(data)}

    # Flatten recommended_tech_stack: dict -> list of strings
    if isinstance(data.get("recommended_tech_stack"), dict):
        stack = data["recommended_tech_stack"]
        flat = []
        for k, v in stack.items():
            if isinstance(v, list):
                flat.extend(v)
            elif isinstance(v, str):
                flat.append(v)
            elif isinstance(v, dict):
                flat.extend(v.values())
        data["recommended_tech_stack"] = flat

    # Normalize competitors
    for comp in data.get("competitors", []):
        if isinstance(comp, dict):
            for field in ("strengths", "weaknesses"):
                if isinstance(comp.get(field), str):
                    comp[field] = [s.strip() for s in comp[field].split(",") if s.strip()]

    # Normalize risks
    for risk in data.get("risks", []):
        if isinstance(risk, dict):
            for field in ("category", "description", "severity", "mitigation"):
                if field not in risk:
                    risk[field] = "Not specified"
                elif not isinstance(risk[field], str):
                    risk[field] = str(risk[field])

    # Normalize conditions
    if isinstance(data.get("conditions"), str):
        data["conditions"] = [data["conditions"]]

    # Normalize next_steps
    if isinstance(data.get("next_steps"), str):
        data["next_steps"] = [data["next_steps"]]
    elif isinstance(data.get("next_steps"), list) and data["next_steps"] and isinstance(data["next_steps"][0], dict):
        data["next_steps"] = _flatten_list_of_dicts(data["next_steps"])

    # Default project_title if missing
    if "project_title" not in data:
        data["project_title"] = data.get("title", "Untitled Project")

    return data


def normalize_roadmap(data: dict) -> dict:
    """Normalize Claude's response to match Roadmap schema."""
    for field in ("dependencies", "assumptions", "out_of_scope"):
        if isinstance(data.get(field), str):
            data[field] = [data[field]]

    for milestone in data.get("milestones", []):
        if isinstance(milestone.get("success_criteria"), str):
            milestone["success_criteria"] = [milestone["success_criteria"]]
        for story in milestone.get("stories", []):
            if isinstance(story.get("acceptance_criteria"), str):
                story["acceptance_criteria"] = [story["acceptance_criteria"]]
            if isinstance(story.get("labels"), str):
                story["labels"] = [s.strip() for s in story["labels"].split(",")]
            if isinstance(story.get("priority_score"), (int, str)):
                story["priority_score"] = float(story["priority_score"])

    return data
