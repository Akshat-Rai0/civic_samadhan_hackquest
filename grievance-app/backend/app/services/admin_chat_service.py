"""Read-only tool layer for the authority dashboard assistant.

The language model never receives database credentials.  Instead it can request
only the narrowly scoped functions in this module, whose results are generated
from the current database on every chat turn.
"""

import json
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.completion import CitizenConfirmation, CompletionEvidence
from app.models.department import Department
from app.models.escalation import EscalationLog
from app.models.issue import IssueCluster, IssueImage
from app.models.notification import Notification
from app.models.officer import Assignment, Officer

settings = get_settings()
MAX_TOOL_ROUNDS = 4
MAX_RESULTS = 50


def _iso(value: Any) -> Optional[str]:
    return value.isoformat() if value else None


def _ticket_id(cluster: IssueCluster) -> str:
    return f"GR-{cluster.id}"


def _latest_assignment(db: Session, cluster_id: int) -> Optional[Assignment]:
    return (
        db.query(Assignment)
        .filter(Assignment.cluster_id == cluster_id)
        .order_by(Assignment.assigned_at.desc(), Assignment.id.desc())
        .first()
    )


def _cluster_summary(db: Session, cluster: IssueCluster) -> Dict[str, Any]:
    department = db.query(Department).filter(Department.id == cluster.department_id).first()
    assignment = _latest_assignment(db, cluster.id)
    officer = db.query(Officer).filter(Officer.id == assignment.officer_id).first() if assignment else None
    return {
        "ticket_id": _ticket_id(cluster),
        "date_of_issue": _iso(cluster.created_at),
        "issue_type": cluster.issue_type or cluster.category or "Unclassified",
        "category": cluster.category,
        "place_of_issue": {
            "zone": cluster.zone,
            "postal_code": cluster.postal_code,
            "coordinates": {"latitude": cluster.lat, "longitude": cluster.lng},
        },
        "responsible_department": department.name if department else "Unrouted",
        "assigned_officer": officer.name if officer else "Unassigned",
        "status": cluster.status,
        "priority_score": cluster.priority_score,
        "sla_deadline": _iso(cluster.sla_deadline),
        "escalation_tier": cluster.escalation_tier or 0,
        "affected_reports": cluster.affected_count or 0,
    }


def search_issues(db: Session, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Search live tickets using non-sensitive operational filters."""
    query = db.query(IssueCluster)
    ticket_id = str(arguments.get("ticket_id") or "").strip().upper()
    if ticket_id.startswith("GR-") and ticket_id[3:].isdigit():
        query = query.filter(IssueCluster.id == int(ticket_id[3:]))
    elif ticket_id.isdigit():
        query = query.filter(IssueCluster.id == int(ticket_id))
    if arguments.get("status"):
        query = query.filter(IssueCluster.status == str(arguments["status"]))
    if arguments.get("department_id") is not None:
        query = query.filter(IssueCluster.department_id == int(arguments["department_id"]))
    if arguments.get("zone"):
        query = query.filter(IssueCluster.zone.ilike(f"%{str(arguments['zone']).strip()}%"))
    if arguments.get("issue_type"):
        term = f"%{str(arguments['issue_type']).strip()}%"
        query = query.filter((IssueCluster.issue_type.ilike(term)) | (IssueCluster.category.ilike(term)))
    if arguments.get("date_from"):
        query = query.filter(IssueCluster.created_at >= datetime.fromisoformat(arguments["date_from"]))
    if arguments.get("date_to"):
        query = query.filter(IssueCluster.created_at <= datetime.fromisoformat(arguments["date_to"]))
    if arguments.get("min_priority") is not None:
        query = query.filter(IssueCluster.priority_score >= float(arguments["min_priority"]))

    limit = min(max(int(arguments.get("limit", 20)), 1), MAX_RESULTS)
    clusters = query.order_by(IssueCluster.priority_score.desc(), IssueCluster.created_at.desc()).limit(limit).all()
    return {"count": len(clusters), "issues": [_cluster_summary(db, cluster) for cluster in clusters]}


def get_issue_detail(db: Session, arguments: Dict[str, Any]) -> Dict[str, Any]:
    ticket_id = str(arguments.get("ticket_id") or "").strip().upper().replace("GR-", "")
    if not ticket_id.isdigit():
        return {"error": "Provide a valid ticket id such as GR-42."}
    cluster = db.query(IssueCluster).filter(IssueCluster.id == int(ticket_id)).first()
    if not cluster:
        return {"error": f"No ticket exists with id GR-{ticket_id}."}

    data = _cluster_summary(db, cluster)
    images = db.query(IssueImage).filter(IssueImage.cluster_id == cluster.id).order_by(IssueImage.created_at.asc()).all()
    assignments = db.query(Assignment).filter(Assignment.cluster_id == cluster.id).order_by(Assignment.assigned_at.desc()).all()
    escalations = db.query(EscalationLog).filter(EscalationLog.cluster_id == cluster.id).order_by(EscalationLog.logged_at.desc()).all()
    evidence = db.query(CompletionEvidence).filter(CompletionEvidence.cluster_id == cluster.id).order_by(CompletionEvidence.id.desc()).all()
    confirmations = db.query(CitizenConfirmation).filter(CitizenConfirmation.cluster_id == cluster.id).order_by(CitizenConfirmation.submitted_at.desc()).all()
    notifications = db.query(Notification).filter(Notification.cluster_id == cluster.id).order_by(Notification.sent_at.desc()).limit(10).all()

    officer_names = {}
    for assignment in assignments:
        officer = db.query(Officer).filter(Officer.id == assignment.officer_id).first()
        officer_names[assignment.officer_id] = officer.name if officer else "Unknown officer"
    data.update({
        "image_reports": [
            {"reported_at": _iso(image.created_at), "description": image.description, "vision_analysis": image.moondream_output}
            for image in images
        ],
        "assignment_history": [
            {"officer": officer_names.get(a.officer_id), "assigned_at": _iso(a.assigned_at)} for a in assignments
        ],
        "escalation_history": [
            {"reason": item.reason, "from_tier": item.from_tier, "to_tier": item.to_tier, "logged_at": _iso(item.logged_at)}
            for item in escalations
        ],
        "completion_evidence": [
            {"passed_automated_checks": item.passed_automated_checks, "diff_score": item.diff_score, "object_delta": item.object_delta}
            for item in evidence
        ],
        "citizen_confirmations": [
            {"status": item.status, "submitted_at": _iso(item.submitted_at)} for item in confirmations
        ],
        "recent_notification_statuses": [
            {"template": item.template, "status": item.status, "sent_at": _iso(item.sent_at)} for item in notifications
        ],
    })
    return data


def summarize_issues(db: Session, _: Dict[str, Any]) -> Dict[str, Any]:
    clusters = db.query(IssueCluster).all()
    departments = {dept.id: dept.name for dept in db.query(Department).all()}
    return {
        "total_tickets": len(clusters),
        "by_status": dict(Counter((cluster.status or "unknown") for cluster in clusters)),
        "by_responsible_department": dict(Counter(departments.get(cluster.department_id, "Unrouted") for cluster in clusters)),
        "by_issue_type": dict(Counter((cluster.issue_type or cluster.category or "Unclassified") for cluster in clusters)),
        "critical_priority_tickets": [
            _cluster_summary(db, cluster)
            for cluster in sorted(clusters, key=lambda item: item.priority_score or 0, reverse=True)[:10]
        ],
    }


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_issues",
            "description": "Find current civic issue tickets by operational filters. Use this before answering a question about a set of tickets.",
            "parameters": {"type": "object", "properties": {
                "ticket_id": {"type": "string"}, "status": {"type": "string"},
                "department_id": {"type": "integer"}, "zone": {"type": "string"},
                "issue_type": {"type": "string"}, "date_from": {"type": "string", "description": "ISO date or datetime"},
                "date_to": {"type": "string", "description": "ISO date or datetime"},
                "min_priority": {"type": "number"}, "limit": {"type": "integer"},
            }},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_issue_detail",
            "description": "Get all available operational details for one ticket, including reports, places, responsibility, assignment, escalation, evidence, and notification statuses.",
            "parameters": {"type": "object", "properties": {"ticket_id": {"type": "string"}}, "required": ["ticket_id"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_issues",
            "description": "Get a live aggregate view of all issue tickets and the highest priority tickets.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


def _execute_tool(db: Session, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    try:
        if name == "search_issues":
            return search_issues(db, arguments)
        if name == "get_issue_detail":
            return get_issue_detail(db, arguments)
        if name == "summarize_issues":
            return summarize_issues(db, arguments)
        return {"error": f"Unknown tool: {name}"}
    except (TypeError, ValueError) as exc:
        return {"error": f"Invalid tool arguments: {exc}"}


SYSTEM_PROMPT = """You are the CivicSamadhaan Authority Issue Assistant. Answer authority staff using only the live data returned by your tools. For ticket-specific or factual questions, call a tool before responding. Be clear about the ticket ID and include dates, place, responsible department, assigned officer, status, priority, SLA, and escalation details whenever they matter. If a field is missing, say it is unavailable or unassigned; never invent data. You are read-only: do not claim to assign, close, dispatch, contact, or modify an issue. Do not expose citizen identities, contact details, image URLs, or internal credentials. Keep responses concise and operationally useful."""


def ask_authority_assistant(db: Session, question: str, history: List[Dict[str, str]]) -> Dict[str, Any]:
    if not settings.GROQ_API_KEY:
        raise RuntimeError("Groq is not configured. Set GROQ_API_KEY in the backend .env file.")

    clean_history = []
    for message in history[-10:]:
        role, content = message.get("role"), message.get("content")
        if role in {"user", "assistant"} and isinstance(content, str) and content.strip():
            clean_history.append({"role": role, "content": content.strip()[:4000]})
    messages: List[Dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}, *clean_history, {"role": "user", "content": question.strip()}]
    endpoint = f"{settings.GROQ_API_BASE_URL.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}", "Content-Type": "application/json"}
    used_tools: List[str] = []

    with httpx.Client(timeout=settings.GROQ_CHAT_TIMEOUT_SECONDS) as client:
        for _ in range(MAX_TOOL_ROUNDS):
            response = client.post(endpoint, headers=headers, json={
                "model": settings.GROQ_MODEL,
                "messages": messages,
                "tools": TOOL_DEFINITIONS,
                "tool_choice": "auto",
                "temperature": 0.1,
                "max_completion_tokens": 1200,
                "reasoning_effort": "low",
            })
            if response.is_error:
                try:
                    detail = response.json().get("error", {}).get("message", response.text)
                except ValueError:
                    detail = response.text
                raise RuntimeError(f"Groq request failed ({response.status_code}): {detail}")
            payload = response.json()
            choices = payload.get("choices") or []
            if not choices:
                raise RuntimeError("Groq returned no completion.")
            assistant_message = choices[0].get("message") or {}
            tool_calls = assistant_message.get("tool_calls") or []
            if not tool_calls:
                answer = (assistant_message.get("content") or "I could not produce an answer from the available issue data.").strip()
                return {"answer": answer, "sources": used_tools}

            messages.append({
                "role": "assistant",
                "content": assistant_message.get("content"),
                "tool_calls": tool_calls,
            })
            for call in tool_calls:
                function = call.get("function", {})
                name = function.get("name", "")
                try:
                    arguments = json.loads(function.get("arguments") or "{}")
                except json.JSONDecodeError:
                    arguments = {}
                result = _execute_tool(db, name, arguments)
                used_tools.append(name)
                messages.append({"role": "tool", "tool_call_id": call.get("id"), "content": json.dumps(result, default=str)})

    return {"answer": "I reached the data lookup limit before completing that answer. Please ask about a specific ticket or narrower group.", "sources": used_tools}
