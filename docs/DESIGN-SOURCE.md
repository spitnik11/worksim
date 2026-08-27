# WorkSim — Source Design Doc (Company Simulation / Job Card System v0.1)

This is the canonical specification all three agents work from. It defines the role
families, the universal Job Card schema, and detailed templates per role. When
authoring cards under `cards/`, mine the relevant section here for competencies,
tools, workflows, inputs, outputs, KPIs, handoffs, and task archetypes.

> Implementation note: the running schema lives in `worksim/schema.py`. Field names
> there are the contract; this doc is the content source. Two number scales:
> Job Card competencies + Task required_skills are **0.0–1.0**; Employee skills/traits
> are **0–100**.

---

## 1. Core concept

Five separate concepts:

```
JOB CARD          — what a position normally does
   ↓
EMPLOYEE/AGENT    — how good a particular worker is at that job
   ↓
TASK PACKET       — a specific piece of work
   ↓
SCENARIO/EVENT    — the business context that produces tasks
   ↓
OUTPUT + EVALUATION — grade the work vs business/technical/comms/process requirements
```

Don't encode a specific person's skills into a generic role. The Job Card requires
`sql: 0.60`; an *employee* has `sql: 70` (or 92). Cards are data, not prompts.

## 2. Universal Job Card schema (author cards to this shape)

`role_id, title, family, level, department, mission.summary, business_value[],
core_competencies{skill: 0..1}, tools{required[], common[]}, daily_workflows[],
inputs[], outputs[], kpis[], handoffs{receives_from[], sends_to[]},
simulation_permissions{may_request_data, may_modify_production, may_approve_release},
escalation_rules[], task_archetypes[]`.

## 3. Data & Reporting Analyst  (role_id: data_reporting_analyst — DONE, reference card)

Mission: turn operational/business data into trusted information for decisions.
Skills: SQL/Excel/data-validation/reporting/analytical-thinking HIGH; comms MED-HIGH;
Python/APIs/stats MED; visualization MED-HIGH. Tools: SQL, Excel, Power BI, Tableau,
Python/Pandas, CSV/JSON, REST APIs, data warehouse, Jira, SharePoint. Outputs: KPI
dashboard, SQL query, data-quality report, trend analysis, executive summary, metric
dictionary, CSV extract. KPIs: report accuracy, dashboard freshness, analysis
turnaround, data error rate, stakeholder adoption, unresolved discrepancies. Sample
tasks: revenue decline despite rising volume; dashboards disagree 8%; market
opportunity analysis.

## 4. Business Systems Analyst  (role_id: business_systems_analyst — DONE, reference card)

Mission: translate business needs into system/process changes that solve the real
problem. Skills: requirements/process-analysis/comms/documentation HIGH; testing MED;
data-analysis/troubleshooting MED. Tools: Jira, Confluence, SQL, Visio, Excel,
Postman, REST APIs, SharePoint, Git, ERP/CRM. Outputs: BRD, functional requirements,
process map, user stories, acceptance criteria, test plan, UAT results, defect ticket,
change recommendation. Sample tasks: slow claims workflow; duplicate onboarding steps;
new approval process; incomplete API records; move a spreadsheet process into an app.

## 5. Technical Business Analyst  (role_id: technical_business_analyst — TODO)

Mission: translate business requirements into technical specs engineers can implement.
Sits closer to engineering than the BSA. Skills: API concepts HIGH, data structures
MED-HIGH, SQL MED-HIGH, requirements HIGH, system integration HIGH, testing HIGH,
technical documentation HIGH. Work: API requirements, integration mapping, system
diagrams, payload analysis, data mapping, technical user stories, acceptance criteria,
defect reproduction, integration testing. Sample scenario: sync Salesforce customer
records with the billing platform — determine source/target systems, fields,
transformations, endpoints, error handling, auth constraints, sync frequency,
acceptance criteria.

## 6. AI Business / Enablement Analyst  (role_id: ai_business_analyst — TODO)

Mission: determine where AI should be used, how it should work, and whether it
produces business value. Skills: business analysis HIGH, process analysis HIGH, AI
fundamentals HIGH, prompt engineering HIGH, communication HIGH, workflow design HIGH,
change management MED-HIGH, data analysis MED, governance MED-HIGH, ROI analysis
MED-HIGH. Tools: enterprise LLM/ChatGPT, Microsoft Copilot, Copilot Studio, Power
Platform, Power BI, Excel, Teams, SharePoint, APIs, automation platforms, agent
frameworks. Outputs: AI use-case matrix, workflow map, prompt library, agent
specification, AI readiness assessment, adoption report, ROI estimate, training guide,
executive presentation. Sample scenario: support automation — 200 agents, 18k
tickets/mo, 14 min AHT; produce current-state analysis, AI use cases, risk assessment,
human-review policy, agent workflow, productivity impact, roadmap, success metrics.

## 7. AI Quality & Evaluation Analyst  (role_id: ai_quality_analyst — TODO)

Keep SEPARATE from the AI BA. Mission: determine whether an AI system is correct,
reliable, safe, repeatable, and appropriate for release. Skills: analytical judgment
VERY HIGH, attention to detail VERY HIGH, AI evaluation HIGH, prompt testing HIGH, QA
HIGH, documentation HIGH, risk analysis MED-HIGH, communication HIGH. Procedures:
build rubrics from requirements → expected behavior → rubric → test case → golden
result; run eval (prompt → response → compare to ground truth → score → record
defect); regression (change → rerun benchmark → compare → identify regression). Tools:
eval platform, spreadsheets, JSON, Python, prompt libraries, annotation tools,
dashboards, Jira. Outputs: evaluation rubric, golden dataset, test suite, benchmark
report, failure taxonomy, regression report, quality dashboard, release
recommendation. KPIs: eval consistency, defect detection rate, false-pass rate, test
coverage, edge-case coverage, regression rate, release defect rate. Sample event:
support-AI prompt updated (accuracy 92%→95%, policy compliance 98%→?); decide whether
to ship.

## 8. Application Support Analyst  (role_id: application_support_analyst — TODO)

Mission: keep business applications working reliably for users. Workflow: ticket →
impact → symptoms → reproduce → check config/permissions/logs/data → likely cause →
resolve or escalate → validate fix → document. Tools (use fictional equivalents):
SupportDesk (ServiceNow), Jira, SQL, directory, Microsoft 365, logs, ERP/CRM,
PeopleCore (Workday), MediFlow (Epic), ClientSphere (Salesforce), monitoring. KPIs:
MTTR, first-contact resolution, ticket backlog, SLA compliance, reopen rate, user
satisfaction, recurring-incident rate. Sample event: five users report "the app isn't
working" — is it one outage, five problems, permissions, a bad deploy, network, data,
or user error?

## 9. Business Applications Analyst  (role_id: business_applications_analyst — TODO)

One level above basic Application Support. Mission: own the functional health of an
enterprise business system. Responsibilities: configuration analysis, application
workflows, user security, reports, business processes, release testing, patch
validation, implementation coordination, documentation, system recommendations.
Sample task: payroll suddenly excludes one division — diagnose among bad security
config, incorrect business rule, bad data import, integration failure, wrong report
filter.

## 10. Project Coordinator  (role_id: project_coordinator — TODO)

Mission: make sure work moves through the org without getting lost. Responsibilities:
maintain project plan, organize meetings, capture notes, track action items &
milestones, identify dependencies, update docs, monitor risks, escalate, coordinate
teams, support closeout. Tools: Teams, SharePoint, Planner, Jira, Excel, PowerPoint,
Confluence, PSA. Artifacts: Project Charter, Project Plan, Action Register, RAID Log,
Meeting Notes, Milestone Tracker, Status Report, Change Request, Closeout Report.
KPIs: missed milestones, overdue action items, documentation completeness, unresolved
risks, schedule variance, communication latency. Sample task: migrate 500 employees
to a new CRM in six weeks — manage schedule, owners, dependencies, testing, training,
comms, risks, go-live.

## 11. Technology Operations / Resiliency Analyst  (role_id: resiliency_analyst — TODO)

Mission: ensure critical systems survive failures and recover predictably.
Responsibilities: application dependency analysis, recovery-readiness assessments,
infrastructure reviews, recovery exercises, tabletop simulations, incident follow-ups,
lessons learned, risk tracking, resiliency metrics, recovery docs, process
improvement. Concepts: RTO, RPO, dependency mapping, business continuity, disaster
recovery, incident management, recovery testing, risk register. KPIs: RTO/RPO
achievement, exercise completion rate, critical-system coverage, remediation closure,
recovery-test success, unresolved resilience risk. Sample event: cloud region hosting
billing goes down — receive architecture, dependencies, backups, procedures, RTO/RPO,
incident timeline; coordinate and evaluate recovery.

## 12. Business / Program Analyst  (role_id: program_analyst — optional, later)

Broad business-improvement role: business metrics, operational analysis, process
improvement, program tracking, stakeholder interviews, KPI reporting, recommendations,
strategic analysis, executive reporting. Anchors multi-role scenarios (e.g. foreign
market entry).

## 14. Employee / Agent Profile

`employee_id, name, primary_role, secondary_roles[], level, skills{0..100},
traits{0..100} (attention_to_detail, initiative, ambiguity_tolerance, risk_tolerance),
capacity{available_hours}, permissions{}, performance_history{task_success_rate,
average_quality}`. Skills can grow after graded tasks.

## 16. Agent assignment scoring (for assign.py)

`30% role match, 22% skill match, 12% tool match, 10% domain knowledge, 10% capacity,
8% prior performance, 5% project continuity, 3% development opportunity`. Risk > 0.70
→ mandatory independent reviewer; risk > 0.90 → manager approval.

## 17–20. Scenario engine

A scenario seeds company state (cash, employees, customers, markets, products,
projects, risks, competitors). An event mutates the world and generates tasks. Agents
see only role-appropriate info; the engine holds the hidden truth. Info boundaries
force asking questions, requesting docs, escalating, handing off.

## 21. Scoring (for evaluate.py)

Score each 0–100: technical correctness, business reasoning, evidence quality,
communication, documentation, process compliance, risk awareness, timeliness,
collaboration. Apply role-specific weighting for the final grade.

## 23. Canonical role library (9 to build first)

DATA-001 data_reporting_analyst · BA-001 business_systems_analyst ·
BA-002 technical_business_analyst · AI-001 ai_business_analyst ·
AI-002 ai_quality_analyst · SUP-001 application_support_analyst ·
APP-001 business_applications_analyst · PMO-001 project_coordinator ·
OPS-001 resiliency_analyst.

## 24. The architectural rule

Job descriptions are DATA, not prompts. `cards/jobs/*.yaml` → validated by schema.py →
combined with company state + scenario + employee + tools → task generation →
assignment → work → evaluation → company state changes → training record.
