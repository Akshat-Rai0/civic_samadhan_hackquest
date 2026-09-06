import math
import json

BASE_SEVERITY = {
    "exposed wiring": 95,
    "open manhole": 90,
    "sewage overflow": 85,
    "water contamination": 85,
    "broken streetlight": 70,
    "pothole": 60,
    "road damage": 55,
    "broken curb": 40,
    "garbage pile": 35,
    "graffiti": 15,
    "default": 50,
}

# Moondream returns natural-language labels (for example, "pothole on asphalt
# surface"), while the rubric is deliberately keyed by stable, policy-managed
# defect types. This bridge keeps the score attached to the actual defect—not
# the broad routing category such as "roads" or "electrical".
ISSUE_TYPE_SIGNALS = {
    "exposed wiring": ("exposed wiring", "exposed wire", "live wire", "wiring", "wire"),
    "open manhole": ("open manhole", "uncovered manhole", "manhole"),
    "sewage overflow": ("sewage overflow", "sewage", "drain overflow", "overflow"),
    "water contamination": ("water contamination", "contaminated water", "contamination"),
    "broken streetlight": ("broken streetlight", "streetlight", "street light", "flickering light", "pole light"),
    "pothole": ("pothole", "crater"),
    "road damage": ("road damage", "damaged road", "road crack", "cracked road", "asphalt"),
    "broken curb": ("broken curb", "damaged curb", "curb"),
    "garbage pile": ("garbage pile", "uncollected garbage", "garbage", "waste", "trash", "litter"),
    "graffiti": ("graffiti",),
}

def affected_count_multiplier(count: int) -> float:
    """Diminishing returns so a popular minor issue does not outrank a rare serious one."""
    if count <= 1:
        return 1.0
    return 1.0 + 0.4 * math.log2(count)

def compute_priority(issue_type: str, affected_count: int) -> float:
    base = BASE_SEVERITY.get((issue_type or "").lower(), BASE_SEVERITY["default"])
    multiplier = affected_count_multiplier(affected_count)
    return round(base * multiplier, 1)


def resolve_issue_type(detected_issues: list[str] | None, category: str | None = None) -> str:
    """Map vision labels to the highest-severity matching rubric defect."""
    labels = detected_issues or []
    combined = " ".join(str(label).lower() for label in labels)
    matches = [
        issue_type
        for issue_type, signals in ISSUE_TYPE_SIGNALS.items()
        if any(signal in combined for signal in signals)
    ]
    if matches:
        return max(matches, key=lambda issue_type: BASE_SEVERITY[issue_type])

    # A broad category is retained only as an auditable fallback when vision
    # cannot identify a rubric defect. It intentionally receives default score.
    return (category or "default").lower()


def backfill_issue_types_and_priorities(db) -> None:
    """Upgrade existing clusters after the rubric fields are introduced."""
    from app.models.issue import IssueCluster

    changed = False
    for cluster in db.query(IssueCluster).filter(IssueCluster.issue_type.is_(None)).all():
        detected_issues = []
        for image in cluster.images:
            if not image.moondream_output:
                continue
            try:
                value = json.loads(image.moondream_output)
                detected_issues.extend(value if isinstance(value, list) else [str(value)])
            except (TypeError, ValueError):
                detected_issues.append(image.moondream_output)

        cluster.issue_type = resolve_issue_type(detected_issues, cluster.category)
        if cluster.priority_override is None:
            cluster.priority_score = compute_priority(cluster.issue_type, cluster.affected_count or 1)
        changed = True

    if changed:
        db.commit()
