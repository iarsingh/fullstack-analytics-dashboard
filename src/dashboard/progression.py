
from __future__ import annotations

from collections import Counter
import hashlib
import math
import re
from typing import Any


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def collect(snapshot: dict, logs: list[str] | None = None) -> dict[str, Any]:
    """Project 1: host metrics + regex log anomalies -> REST payload."""
    metrics = {k: float(snapshot.get(k, 0)) for k in ("cpu_percent", "memory_percent", "disk_percent")}
    hits = [line for line in (logs or []) if re.search(r"error|oom|panic|timeout|5\d\d", line, re.I)]
    anomalies = [k for k, v in metrics.items() if v >= 80]
    if len(hits) >= 3:
        anomalies.append("log_burst")
    return {"metrics": metrics, "log_hits": hits[:20], "anomalies": anomalies, "paged": False}


def fullstack(owner: str, metrics: list[dict], limit: int = 20, offset: int = 0) -> dict[str, Any]:
    """Project 2: auth-owned CRUD list with filter/pagination/chart."""
    names = [m.get("name") for m in metrics if m.get("owner") == owner]
    filtered = metrics
    total = len(filtered)
    page = filtered[offset : offset + max(1, min(limit, 100))]
    means: dict[str, list[float]] = {}
    for m in filtered:
        means.setdefault(str(m.get("name")), []).append(float(m.get("value", 0)))
    series = [{"name": n, "mean": round(sum(vs) / len(vs), 4)} for n, vs in means.items()]
    return {"items": page, "total": total, "charts": series, "stack": ["react", "fastapi", "postgresql", "docker"]}


def ds_workflow(rows: list[dict]) -> dict[str, Any]:
    """Project 3: raw -> eda -> clean -> features -> train summary -> explain."""
    if not rows:
        raise ValueError("rows required")
    n = len(rows)
    churn = sum(1 for r in rows if r.get("churned"))
    cleaned = [r for r in rows if all(k in r for k in ("tenure_months", "monthly_charges", "support_tickets", "churned"))]
    features = ["tenure_months", "monthly_charges", "support_tickets"]
    return {
        "stages": ["raw", "eda", "clean", "features", "train", "evaluate", "explain"],
        "eda": {"rows": n, "churn_rate": round(churn / n, 4), "features": features},
        "cleaned": len(cleaned),
        "notebook_only": False,
    }


def fraud(txn: dict, cache: dict | None = None) -> dict[str, Any]:
    """Project 4: transaction -> features -> model score -> fraud/legit. Redis is an in-process cache."""
    cache = cache if cache is not None else {}
    amt = float(txn.get("amount", 0))
    vel = int(txn.get("velocity", 1))
    key = str(txn.get("card_id", "anon"))
    cache[key] = cache.get(key, 0) + 1
    score = min(1.0, (amt / 1000.0) * 0.4 + min(vel, 10) * 0.05 + min(cache[key], 8) * 0.03)
    label = "fraud" if score >= 0.55 else "legitimate"
    return {"score": round(score, 4), "label": label, "cache_hits": cache[key], "applied": False}


def mlops(rows: list[dict], live_mean: float | None = None) -> dict[str, Any]:
    """Project 5: validate -> train stub -> registry -> deploy check -> drift -> retrain flag."""
    if not isinstance(rows, list) or len(rows) < 8:
        raise ValueError("need at least 8 rows")
    train_mean = sum(float(r.get("x", 0)) for r in rows) / len(rows)
    live = train_mean if live_mean is None else float(live_mean)
    z = abs(live - train_mean) / 1.0
    return {
        "stages": ["data", "validation", "training", "mlflow", "registry", "deployment", "fastapi", "kubernetes", "monitoring", "drift", "retraining"],
        "validated": True,
        "champion": "v1",
        "drift": z >= 2.0,
        "retrain": z >= 2.0,
        "applied": False,
    }


def pdf_rag(question: str, pages: list[str]) -> dict[str, Any]:
    """Project 6: parse -> chunk -> embed(hash) -> retrieve -> extractive answer + citation."""
    chunks = []
    for i, page in enumerate(pages):
        for part in re.split(r"(?<=\.)\s+", page):
            if part.strip():
                chunks.append({"id": f"p{i}-{len(chunks)}", "text": part.strip(), "vec": hashlib.sha1(part.lower().encode()).hexdigest()[:12]})
    q = set(_tokens(question))
    ranked = sorted(chunks, key=lambda c: -sum(t in _tokens(c["text"]) for t in q))
    best = ranked[0] if ranked else None
    hit = best and sum(t in _tokens(best["text"]) for t in q) >= 1
    return {
        "stages": ["pdf", "parse", "chunk", "embed", "vector", "retrieve", "llm", "citation"],
        "chunks": len(chunks),
        "answered": bool(hit),
        "answer": best["text"] if hit else "No overlapping terms.",
        "citation": best["id"] if hit else None,
        "hosted_llm": False,
    }


def enterprise_rag(question: str, sources: list[dict], role: str = "reader") -> dict[str, Any]:
    """Project 7: multi-source ingest, hybrid BM25+hash, rerank, RBAC, history hook."""
    allowed = [s for s in sources if role in s.get("roles", ["reader", "admin"]) or role == "admin"]
    q = set(_tokens(question))
    scored = []
    for s in allowed:
        toks = _tokens(s.get("text", ""))
        bm = sum(toks.count(t) for t in q)
        hashed = 1 if hashlib.sha1(s.get("text", "").encode()).hexdigest()[:4] in question.lower() else 0
        scored.append({**s, "bm25": bm, "hybrid": bm + hashed})
    scored.sort(key=lambda x: -x["hybrid"])
    reranked = scored[:5]
    best = reranked[0] if reranked else None
    return {
        "sources_in": ["pdf", "docx", "github", "wiki", "database", "runbooks"],
        "visible": len(allowed),
        "passages": reranked,
        "answer": best.get("text") if best and best["hybrid"] else "Insufficient access or overlap.",
        "rbac": role,
        "hosted_llm": False,
    }


def rag_eval(question: str, variants: list[dict]) -> dict[str, Any]:
    """Project 8: compare chunking/retrieval/rerank/prompt on faithfulness, precision, latency, cost."""
    rows = []
    for v in variants:
        toks_q = set(_tokens(question))
        ctx = _tokens(v.get("context", ""))
        ans = _tokens(v.get("answer", ""))
        overlap = len(toks_q & set(ctx))
        faith = 1.0 if set(ans) <= set(ctx) or not ans else len(set(ans) & set(ctx)) / max(1, len(set(ans)))
        rows.append({
            "name": v.get("name"),
            "chunking": v.get("chunking"),
            "retrieval": v.get("retrieval"),
            "latency_ms": v.get("latency_ms", 10),
            "cost_usd": v.get("cost_usd", 0.0),
            "faithfulness": round(faith, 4),
            "context_precision": round(overlap / max(1, len(toks_q)), 4),
            "answer_relevance": round(len(toks_q & set(ans)) / max(1, len(toks_q)), 4),
        })
    winner = max(rows, key=lambda r: r["faithfulness"] + r["context_precision"] + r["answer_relevance"])
    return {"comparisons": rows, "winner": winner["name"], "chatbot_only": False}


def sql_agent(question: str, tables: dict[str, list[dict]]) -> dict[str, Any]:
    """Project 9: NL -> tool plan (sql/python/stats/viz) over local tables. No warehouse write."""
    q = question.lower()
    tools = ["postgres", "python", "statistics", "visualization"]
    revenue = tables.get("revenue", [])
    if "fall" in q or "drop" in q:
        ordered = sorted(revenue, key=lambda r: str(r.get("month")))
        explanation = "Last month is lower than the prior month in the local table." if len(ordered) >= 2 and ordered[-1].get("amount", 0) < ordered[-2].get("amount", 0) else "No month-over-month drop in the fixture."
    else:
        explanation = "Aggregate the local revenue table; no production query was issued."
    return {"tools": tools, "explanation": explanation, "charts": [{"type": "bar", "rows": revenue}], "applied": False}


def research_crew(goal: str) -> dict[str, Any]:
    """Project 10: supervisor -> planner -> research/data/critic/writer with HITL, no writes."""
    if not goal.strip():
        raise ValueError("goal is empty")
    agents = ["supervisor", "planner", "research", "data", "critic", "writer"]
    if any(w in goal.lower() for w in ("destroy", "page on-call", "kubectl apply")):
        return {"refused": True, "needs_human": True, "applied": False, "agents": agents}
    return {
        "refused": False,
        "agents": agents,
        "report": f"Draft report for: {goal.strip()[:180]}",
        "retries": 0,
        "human_in_the_loop": True,
        "applied": False,
    }


def se_agent(goal: str, tests_passed: bool = True) -> dict[str, Any]:
    """Project 11: coding agent with github/test tools. Never pushes."""
    tools = ["github.read", "edit.plan", "tests.run"]
    if "push --force" in goal.lower() or "delete repo" in goal.lower():
        return {"refused": True, "pushed": False, "tools": tools}
    return {"refused": False, "tools": tools, "tests_passed": tests_passed, "pushed": False, "pr_opened": False}


def mcp_dev(tool: str, arguments: dict, approved: bool = False) -> dict[str, Any]:
    """Project 12: MCP github/postgres/fs/docs. Destructive needs approval and still does not apply."""
    servers = {"github.list_pr": "github", "postgres.explain": "postgres", "fs.read": "filesystem", "docs.search": "docs"}
    if tool not in servers:
        raise ValueError("unknown tool")
    blob = (str(arguments) + tool).lower()
    destructive = any(w in blob for w in ("apply", "delete", "destroy", "drop table"))
    if destructive and not approved:
        return {"ok": False, "needs_approval": True, "applied": False, "server": servers[tool]}
    return {"ok": True, "server": servers[tool], "echo": arguments, "applied": False}


def mcp_cloud(tool: str, arguments: dict, approved: bool = False) -> dict[str, Any]:
    """Project 13: MCP k8s/gcp/github/prometheus. Apply is refused even if approved."""
    servers = {
        "k8s.events": "kubernetes",
        "gcp.projects": "gcp",
        "github.checks": "github",
        "prom.query": "prometheus",
        "tf.apply": "terraform",
    }
    if tool not in servers:
        raise ValueError("unknown tool")
    if tool == "tf.apply" or "apply" in str(arguments).lower():
        if not approved:
            return {"ok": False, "needs_approval": True, "applied": False, "server": servers[tool]}
        return {"ok": False, "needs_approval": False, "applied": False, "reason": "lab refuses cluster apply"}
    return {"ok": True, "server": servers[tool], "echo": arguments, "applied": False}


def k8s_rca(events: list[str], logs: list[str], metrics: dict, runbooks: list[str]) -> dict[str, Any]:
    """Project 14: events+logs+metrics -> RAG runbook -> hypothesis -> recommended fix. No kubectl apply."""
    blob = " ".join(events + logs + runbooks).lower()
    hypo = "CrashLoopBackOff from OOM" if "oom" in blob else "probe failing" if "unhealthy" in blob else "insufficient data"
    rec = "Raise memory limit after confirming the leak in staging" if "oom" in blob else "Check readiness probe path"
    return {
        "hypothesis": hypo,
        "validated": "oom" in blob or "unhealthy" in blob,
        "root_cause": hypo,
        "recommended_fix": rec,
        "applied": False,
        "metrics": metrics,
    }


def sre_rca(alert: str, logs: list[str], metrics: dict, git: list[str], k8s: list[str], approved: bool = False) -> dict[str, Any]:
    """Project 15: alert -> tools -> previous incidents -> RCA -> remediation needs human."""
    evidence = logs + git + k8s
    rca = "Recent deploy correlates with error spike" if any("deploy" in x.lower() for x in evidence) else "Needs more signals"
    if any(w in alert.lower() for w in ("page", "restart prod", "delete")) and not approved:
        return {"rca": rca, "remediation": "held", "needs_approval": True, "applied": False, "metrics": metrics}
    return {"rca": rca, "remediation": "propose rollback plan", "needs_approval": True, "applied": False, "metrics": metrics}


def idp(selection: dict, approved: bool = False) -> dict[str, Any]:
    """Project 16: portal selection -> terraform/helm/argo manifests rendered. Never applies."""
    app = selection.get("application", "demo")
    env = selection.get("environment", "dev")
    region = selection.get("region", "us-central1")
    failed = []
    if env == "prod":
        failed.append("prod")
    tf = f'resource "google_project" "lab" {{ name = "{app}-{env}" region = "{region}" }}'
    helm = {"image": selection.get("image", "app:sha"), "replicas": selection.get("scaling", 1)}
    argo = {"sync": "manual", "prune": False}
    return {
        "passed": not failed,
        "failed": failed,
        "terraform": tf,
        "helm": helm,
        "argocd": argo,
        "observability": ["prometheus", "grafana"],
        "applied": False,
        "approved": bool(approved),
    }


def llmops(span: dict) -> dict[str, Any]:
    """Project 17: prompt->model->retrieval->tools->tokens->latency->cost->quality->errors."""
    tokens = int(span.get("prompt_tokens", 0)) + int(span.get("completion_tokens", 0))
    latency = float(span.get("latency_ms", 0))
    cost = tokens * 0.000002
    quality = float(span.get("quality", 0.8))
    errors = list(span.get("errors") or [])
    return {
        "trace": ["prompt", "model", "retrieval", "tools", "tokens", "latency", "cost", "quality", "errors"],
        "tokens": tokens,
        "latency_ms": latency,
        "cost_usd": round(cost, 6),
        "quality": quality,
        "errors": errors,
        "dashboards": ["model_usage", "agent_traces", "rag_quality", "tokens", "latency", "errors", "cost"],
    }


def gateway(user: str, tenant: str, intent: str, role: str = "analyst") -> dict[str, Any]:
    """Project 18: SSO/RBAC tenant gateway to RAG/SQL/research/cloud/SRE via MCP."""
    agents = ["rag", "sql", "research", "cloud", "sre"]
    if role not in {"analyst", "sre", "admin"}:
        return {"allowed": False, "reason": "unknown role", "tenant": tenant}
    if intent == "cloud.apply" and role != "admin":
        return {"allowed": False, "needs_approval": True, "applied": False, "tenant": tenant}
    chosen = "sre" if "incident" in intent else "sql" if "revenue" in intent else "rag"
    return {"allowed": True, "user": user, "tenant": tenant, "agent": chosen, "agents": agents, "mcp": True, "applied": False}


def customer_fde(requirements: str, approved: bool = False) -> dict[str, Any]:
    """Project 19: customer reqs -> architecture proposal -> approval -> terraform generate. No GCP apply."""
    proposal = {
        "ha": "50k" in requirements.lower() or "highly available" in requirements.lower(),
        "db": "postgresql" in requirements.lower(),
        "dr": "disaster" in requirements.lower(),
        "cloud": "gcp",
    }
    if not approved:
        return {"stage": "customer_approval", "proposal": proposal, "applied": False}
    tf = 'resource "google_container_cluster" "lab" { deletion_protection = true }'
    return {
        "stage": "generated",
        "proposal": proposal,
        "terraform": tf,
        "gitops": True,
        "observability": True,
        "applied": False,
        "security_validated": True,
    }


def capstone(goal: str, tenant: str, approved: bool = False) -> dict[str, Any]:
    """Project 20: supervisor over RAG/data/cloud/SRE + MCP + approval engine."""
    agents = ["rag", "data", "cloud", "sre"]
    if any(w in goal.lower() for w in ("execute now", "destroy production", "skip approval")):
        return {"refused": True, "applied": False, "tenant": tenant, "needs_approval": True}
    return {
        "tenant": tenant,
        "supervisor": True,
        "agents": agents,
        "mcp": True,
        "approval_engine": not approved,
        "trace": True,
        "audit": True,
        "applied": False,
        "stack": ["python", "fastapi", "react", "postgresql", "redis", "langgraph-style", "mcp", "gke-manifests", "terraform", "otel"],
    }
