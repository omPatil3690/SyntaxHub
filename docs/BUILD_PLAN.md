# SyntaxHub — Build plan

Two-person split:
- **AI + Intelligence** (Marlon): RAG, embeddings, hybrid retrieval,
  reranking, knowledge graph, version reasoning, LLM/LangGraph, migration
  planner, confidence scoring, documentation ingestion.
- **Platform + DX** (teammate): Next.js, Monaco, dashboard, GitHub OAuth,
  repository interface, FastAPI integration, DB APIs, Docker, CI/CD,
  MCP UI/integration, deployment.
- Shared: AST analysis, migration engine, verification, testing,
  architecture.

## Phases

- [x] **Phase 0 — Architecture** (this scaffold): monorepo, Next.js,
      FastAPI, Postgres+pgvector, Redis, Docker, CI skeleton.
- [x] **Phase 1 — Documentation engine** (wk 1-2): crawler → cleaner →
      chunker → metadata extractor → embedding → Postgres/pgvector.
      Started with React + Next.js docs only. See `docs/PHASE1.md` to run it.
- [x] **Phase 2 — RAG** (wk 2-3): query classification → version filter →
      keyword ("BM25") + vector search → reciprocal rank fusion →
      optional LLM rerank → evidence/citations → synthesized answer.
      See `docs/PHASE2.md` to run it.
- [x] **Phase 3 — Version engine** (wk 3-4): parse package.json /
      package-lock / requirements.txt / pyproject.toml → framework +
      version + dependency detection. See `docs/PHASE3.md` to run it.
- [x] **Phase 4 — API Knowledge Graph** (wk 4-5): framework → version →
      API → status → replacement → migration. Manually seeded React +
      Next.js. See `docs/PHASE4.md` to run it. (Automated ingestion from
      official sources is still future work.)
- [x] **Phase 5 — Repository scanner** (wk 5-6): GitHub URL → clone →
      dependency detection → AST → API extraction → knowledge graph →
      findings. See `docs/PHASE5.md` — includes what was actually
      tested (real git clone, full pipeline, a real bug found and fixed).
- [x] **Phase 6 — Deprecated/breaking detection** (wk 6-7): categorize
      deprecated / removed / renamed / signature-changed /
      behavior-changed / config-changed, with LOW/MEDIUM/HIGH/CRITICAL
      severity. Wired back into Phase 5's findings. See `docs/PHASE6.md`
      (includes two real bugs found and fixed via integration testing).
- [x] **Phase 7 — Migration planner** (wk 7-8): structured Migration Plan
      JSON before any code generation; review UI (detected → plan →
      review → apply). See `docs/PHASE7.md` — integration-tested against
      a real persisted scan (grouping, classification, guard rails all
      verified, not just compiled).
- [x] **Phase 8 — AI transformation** (wk 8-9): old code + migration
      context → LLM → patch/diff. Never silently overwrite the repo.
      See `docs/PHASE8.md` — includes the honest boundary of what was
      tested without a real LLM key vs. what can't be verified that way.
- [ ] **Phase 9 — Verification** (wk 9-10): AST validation → lint →
      typecheck → build → tests, plus a bounded (2-3 retry) repair loop.
- [ ] **Phase 10 — GitHub integration** (wk 10-11): OAuth, repo selection,
      repo scan, PR analysis, issue creation, migration branch creation.
- [ ] **Phase 11 — MCP** (wk 11-12): expose scan_repository,
      find_deprecated_apis, compare_versions, search_documentation,
      plan_migration, generate_patch, verify_patch as MCP tools.
- [ ] **Phase 12 — Polish** (wk 12+): dashboard, repo/migration history,
      confidence UI, evidence viewer, diff viewer, version explorer, risk
      score, dark mode, notifications.

## Guardrails while building

- Limit repair-loop retries (2-3) — an unbounded agent loop burns money.
- Migration output is always a diff, never a direct overwrite.
- Version detection stays deterministic (package metadata), never LLM.
