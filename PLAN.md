Phase 1 — Documentation Engine (Week 1–2)

Goal: Get real, version-tagged docs into the DB as searchable chunks.

🧠 Build the docs crawler for React + Next.js official docs, migration guides, release notes
🧠 Cleaner/normalizer (strip nav, ads, boilerplate → clean markdown)
🧠 Chunker (semantic/section-based chunking, not fixed-size)
🧠 Metadata extractor (framework, version, doc_type, source_authority, url, last_updated)
🧠 Embedding pipeline (batch embed + store in pgvector)
🛠️ documentation and documentation_chunks DB schema + migrations
🛠️ Admin/internal endpoint to trigger re-crawl and view ingestion status
🤝 Agree on the final metadata schema (this becomes the contract everyone downstream relies on)
Phase 2 — RAG / Hybrid Retrieval (Week 2–3)

Goal: Working retrieval with citations — this is the first real "demo."

🧠 Query classifier (what's being asked: API lookup, migration question, general)
🧠 Version filter logic (restrict search to relevant framework version)
🧠 BM25 + vector search, combined
🧠 Reranker
🧠 Citation formatting (map chunks back to source doc + URL)
🛠️ retrieval service API endpoints (FastAPI routes calling into 🧠's retrieval logic)
🛠️ Frontend: simple query UI + answer + citation list rendering
🤝 Test retrieval quality on ~20 hand-picked Next.js/React questions before moving on
Phase 3 — Version Engine (Week 3–4)

Goal: Deterministic detection of what a repo is actually running.

🛠️ Parsers for package.json, package-lock.json/pnpm-lock.yaml/yarn.lock
🛠️ Parsers for requirements.txt, pyproject.toml, poetry.lock (stub, low priority if focusing JS first)
🛠️ version service: framework + dependency version resolution logic
🧠 Define the version normalization scheme (e.g. semver ranges → resolved version) so the knowledge graph in Phase 4 can key off it cleanly
🤝 Schema for frameworks, versions, packages tables
Phase 4 — API Knowledge Graph (Week 4–5)

Goal: The core differentiator — structured API → status → replacement data.

🧠 Design the graph schema: Framework → Version → API → Status → Replacement → Migration → Docs
🧠 Manually seed it for Next.js + React (start with ~30–50 known deprecations/breaking changes, e.g. middleware → proxy)
🧠 Build the lookup/query layer (given API name + version, return status + replacement)
🛠️ api_intelligence service DB tables + CRUD/query endpoints
🛠️ Simple internal admin UI to add/edit graph entries (so seeding isn't raw SQL)
🤝 Later: plan for semi-automated ingestion from release notes (not required yet)
Phase 5 — Repository Scanner (Week 5–6)

Goal: Point at a GitHub repo, get back real findings.

🛠️ GitHub OAuth + repo selection UI
🛠️ Clone/fetch logic (repository service), file walking, ignoring node_modules etc.
🧠 Tree-sitter integration for AST extraction (imports, calls, components, config)
🧠 TypeScript Compiler API integration for deeper TS/JS-specific analysis
🧠 API extraction: map AST nodes → candidate API usages to check against the knowledge graph
🛠️ Findings storage (scans, findings tables) + results API
🤝 Frontend: repo scan results view (list of findings by severity)
Phase 6 — Deprecated / Breaking Change Detection (Week 6–7)

Goal: Classify findings properly instead of just "deprecated."

🧠 Change taxonomy engine: DEPRECATED / REMOVED / RENAMED / SIGNATURE_CHANGED / BEHAVIOR_CHANGED / CONFIG_CHANGED / FILE_STRUCTURE_CHANGED / DEFAULT_CHANGED / DEPENDENCY_CHANGED
🧠 Severity scoring (LOW/MEDIUM/HIGH/CRITICAL) based on graph data + usage frequency in repo
🛠️ Semgrep integration: write/maintain framework-specific rules (e.g. nextjs/no-deprecated-middleware)
🛠️ Merge Semgrep findings + 🧠's AST-based findings into one unified findings list
🤝 Findings UI: filter/sort by category and severity
Phase 7 — Migration Planner (Week 7–8)

Goal: Structured plan before any code is touched.

🧠 Migration plan generator: findings → structured JSON plan (api, replacement, risk, files, migration_type)
🧠 Ordering/dependency logic between changes (some migrations must happen before others)
🛠️ migration_results schema + plan storage/versioning
🛠️ Frontend: plan review UI (Detected → Plan → Review → Apply flow), user can approve/skip individual items
🤝 Define the plan JSON schema together — this is what LLM generation in Phase 8 consumes
Phase 8 — AI Code Transformation (Week 8–9)

Goal: Actually generate patches, safely.

🧠 LangGraph workflow: Detect → Retrieve → Plan → Generate → (Verify happens in Phase 9)
🧠 LLM router (cheap model for classification, stronger model for planning, strongest for code gen)
🧠 Prompt design + structured output (JSON schema/Pydantic) for patches, forcing diff-style output, never full-file rewrites
🛠️ Monaco-based diff viewer in frontend (old vs new, inline highlighting)
🛠️ Patch storage + "never auto-overwrite repo" safeguard (patches are proposals, applied only on explicit user action)
🤝 Explanation text generation (changed/reason/source) — attach to each patch
Phase 9 — Verification (Week 9–10)

Goal: Prove the migration actually works, with a repair loop.

🛠️ Docker sandbox orchestration: install deps → lint → typecheck → build → test, isolated per migration run
🛠️ Result capture/parsing (pass/fail per stage, error logs)
🧠 Repair agent: on failure, feed error back into LangGraph → retrieve relevant docs → regenerate patch
🧠 Retry limit logic (cap at 2–3 attempts, hard stop to avoid runaway cost)
🧠 Confidence scoring engine (weighted: official source %, version certainty %, graph agreement %, static analysis %, rule match %, build result %, tests %)
🤝 Final report UI (the "Migration Report" card: files analyzed, deprecated APIs, breaking changes, auto vs manual, build/test status, confidence %)
Phase 10 — GitHub Integration (Week 10–11)

Goal: Make it live inside a real dev workflow.

🛠️ GitHub App setup, webhooks, PR event handling
🛠️ PR comment bot (post migration analysis summary on PRs)
🛠️ "Create migration branch" feature (push generated patches to a new branch)
🧠 Support: ensure scan/plan/generate pipeline can run headless (no UI) for webhook-triggered runs
🤝 Decide scope: read-only analysis first, branch creation as a follow-up toggle
Phase 11 — MCP Integration (Week 11–12)

Goal: Make SyntaxHub usable from other AI coding tools, not just your site.

🛠️ MCP server setup (Python MCP SDK), transport/auth
🧠 Expose tools: detect_version, search_docs, scan_code, detect_deprecations, compare_versions, plan_migration, generate_migration, verify_migration — each just a thin wrapper around existing services
🤝 Test against an actual MCP client (e.g. Claude Desktop/Code) end-to-end
🤝 Write MCP usage docs (this becomes part of your differentiation story)
Phase 12 — Polish (Week 12+)

Goal: Turn a working pipeline into a demo-ready product.

🛠️ Dashboard: repo/migration history, saved scans
🛠️ Version explorer (compare React 18 → 19 style browsing UI)
🛠️ Dark mode, notifications, general UX polish
🧠 Evidence/citation click-through polish (click a claim → jump to exact source)
🧠 Risk score feature + "Why is my code outdated?" demo feature (both are cheap wins using data you already have from Phases 4–6)
🤝 Record the final demo flow: paste repo → detect → scan → plan → generate → verify → report

---

Main Features
Version Detection — automatically identifies React, Next.js, Python packages, etc. and their versions from project files.
Documentation Retrieval — retrieves the correct, version-specific official documentation, migration guides, release notes, and API references.

API Knowledge Graph — maintains relationships such as:

API → Framework → Version → Status → Replacement → Migration
Deprecated API Detection — scans the actual codebase and identifies APIs that are deprecated.
Breaking Change Detection — detects removed APIs, renamed APIs, changed parameters, configuration changes, behavior changes, etc.

Version Comparison — e.g.:

Next.js 15 → Next.js 16

and shows what changed.

Migration Planning — creates a structured migration plan before modifying code.
AI Code Transformation — generates actual code changes/diffs.
Static Analysis — AST + tools such as Tree-sitter, TypeScript analysis and Semgrep validate the changes.
Build/Test Verification — runs linting, type checking, builds and tests in an isolated Docker environment.
Evidence & Citations — every important recommendation is backed by authoritative documentation.
Confidence Scoring — combines evidence, version certainty, static analysis and verification results to calculate migration confidence.
GitHub Repository Scanner — connects to a repository and analyzes the entire codebase rather than just a pasted snippet.
MCP Integration — exposes SyntaxHub's capabilities to AI coding assistants through tools such as:
scan_repository()
find_deprecated_apis()
compare_versions()
plan_migration()
generate_patch()
verify_patch()
Research Benchmark — eventually provides a standardized dataset/evaluation framework for measuring how accurately AI systems detect and migrate framework changes.
Project Structure
SyntaxHub
│
├── Frontend
│ └── Next.js + TypeScript
│ ├── Dashboard
│ ├── Code Editor
│ ├── Version Explorer
│ ├── Migration Diff
│ └── Reports
│
├── Backend
│ └── FastAPI
│ ├── Version Service
│ ├── Documentation Service
│ ├── Repository Scanner
│ ├── Analysis Engine
│ ├── Migration Engine
│ └── Verification Engine
│
├── AI Layer
│ ├── LangGraph
│ ├── LLM
│ ├── RAG
│ ├── Embeddings
│ └── Reranking
│
├── Knowledge Layer
│ ├── PostgreSQL
│ ├── pgvector
│ └── API Knowledge Graph
│
├── Code Intelligence
│ ├── Tree-sitter
│ ├── TypeScript Compiler
│ ├── Python AST
│ └── Semgrep
│
├── Verification
│ └── Docker Sandbox
│ ├── Lint
│ ├── Typecheck
│ ├── Build
│ └── Tests
│
└── Integrations
├── GitHub
└── MCP
What makes it novel?

The novelty is not simply "AI + RAG for coding."

The important combination is:

Version-aware documentation + repository-level code intelligence + API evolution knowledge + automated migration + executable verification.

Most AI coding systems can generate a solution, but SyntaxHub's goal is to establish:

"What version am I using?"
↓
"What changed?"
↓
"Does my code use the affected API?"
↓
"How should it be migrated?"
↓
"Can AI modify it?"
↓
"Does the modified project actually build and pass tests?"
↓
"Can I prove why this change is correct?"

That closed-loop detect → reason → transform → verify system is the strongest part of the idea.

Research Direction — Later

When you eventually turn this into a research project, the central research problem could be:

Reliable Automated Framework Migration using Version-Aware Retrieval and Code Verification

You could investigate:

Can a version-aware RAG + API knowledge graph + static analysis + verification loop improve the accuracy and reliability of LLM-generated framework migrations compared with conventional LLM/RAG approaches?

You could evaluate:

deprecated API detection accuracy
breaking-change detection
migration correctness
compilation/build success
test success
hallucination rate
citation/evidence accuracy
number of manual fixes required
confidence calibration

So the product is SyntaxHub, while the eventual research contribution is the methodology for reliable, evidence-grounded and verifiable automated software migration.
