"""Persona prompts — built FROM cards, never hardcoded per role.

The one safety rule: a worker persona must never see `hidden_truth`. Task content
always goes through `TaskPacket.worker_view()`. `test_personas.py` enforces that the
hidden truth cannot leak into any persona-facing string.
"""

from worksim.schema import EmployeeProfile, JobCard, TaskPacket


def _top(d: dict[str, float], n: int) -> list[str]:
    return [k for k, _ in sorted(d.items(), key=lambda kv: kv[1], reverse=True)[:n]]


def worker_system(job: JobCard, employee: EmployeeProfile) -> str:
    """System prompt: this employee playing this role. Data-driven from both cards."""
    strengths = _top(employee.skills, 4) or _top(job.core_competencies, 4)
    tools = ", ".join(job.tools.required + job.tools.common) or "standard business tools"
    return (
        f"You are {employee.name}, a {employee.level} {job.title} "
        f"({job.department or job.family}).\n"
        f"Mission: {job.mission.summary.strip()}\n"
        f"Your strongest skills: {', '.join(strengths)}.\n"
        f"Tools you work with: {tools}.\n\n"
        "You do NOT have omniscient knowledge of the situation. When you need evidence, "
        "request the named documents available to you; if something is missing or blocked, "
        "say what you need and escalate to the requester rather than inventing facts. "
        "Reason from the evidence, quantify your findings, and deliver exactly what the task "
        "asks for in a clear, professional form suitable to present to a stakeholder."
    )


def task_prompt(task: TaskPacket) -> str:
    """The first user message describing the task. Built from worker_view() — the
    engine-only hidden_truth is stripped by construction."""
    v = task.worker_view()
    lines = [
        f"TASK: {v['title']}",
        f"Requested by: {v['requester']}  (priority: {v['priority']}, deadline: {v['deadline']})",
        "",
        f"Context: {v['business_context']}".rstrip(),
    ]
    if v.get("acceptance_criteria"):
        lines += ["", "You will be evaluated on:"]
        lines += [f"  - {c}" for c in v["acceptance_criteria"]]
    if v.get("deliverables"):
        lines += ["", f"Produce these deliverables: {', '.join(v['deliverables'])}."]
    if v.get("inputs"):
        lines += ["", f"Evidence you may request by name: {', '.join(v['inputs'])}."]
    return "\n".join(lines)
