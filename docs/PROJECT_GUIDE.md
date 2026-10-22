# SyntaxHub — Project Guide

What exists, what each file does, and exactly what to push to GitHub.
Read this alongside the main `README.md` (setup/run/test instructions)
and `docs/TESTING_REPORT.md` (empirical results for the manuscript).

---

## 1. Before you push anything — the 5-minute checklist

1. **`.gitignore` is already in the repo root** — it excludes `.env`,
   `node_modules/`, `__pycache__/`, `.next/`, `.venv/`, and
   `benchmark_result.json`. Don't remove or weaken it.
2. **Never commit `.env`** — only `.env.example` (no real values) goes
   in git. If you ever ran `cp .env.example .env` and put a real
   `OPENAI_API_KEY` in it, double check `git status` doesn't show `.env`
   as untracked-but-about-to-be-added before your first `git add .`.
3. **`apps/web/package-lock.json` SHOULD be committed** (it's not in
   `.gitignore`) — it pins the CVE-patched Next.js/React versions found
   and fixed while building this (see Testing Report / main README).
   Deleting it would let a future `npm install` silently resolve a
   different, potentially vulnerable version.
4. **`apps/web/node_modules/` and `apps/web/.next/`** must NOT be
   committed — they're large, regenerable, and already gitignored.
5. Run `pytest -v` one more time right before you push, so the commit
   you push is the one you know passes 59/59.

```bash
cd syntaxhub
git init
git add .
git status   # sanity check: no .env, no node_modules, no __pycache__ listed
git commit -m "SyntaxHub: Phases 1-12 scaffold, 59 passing tests"
git remote add origin <your-repo-url>
git push -u origin main
```

## 2. Root-level files

| File | Purpose |
|---|---|
| `README.md` | Main entry point — what's real vs. pluggable, setup, run, test instructions, performance notes, known limitations |
| `requirements.txt` | All Python dependencies for every service, pinned to tested versions |
| `pytest.ini` | Test config — enables `asyncio_mode = auto`, defines the `network` marker for tests needing internet |
| `docker-compose.yml` | Local Postgres+pgvector and Redis for Phase 1/2/4 |
| `.env.example` | Every environment variable the project reads, with safe defaults and comments explaining each one — copy to `.env` and fill in real values as needed |
| `.gitignore` | See checklist above |
| `settings.py` | Single source of truth for config — every service imports `settings` from here rather than reading `os.environ` directly |

## 3. `packages/schemas/` — the shared contract

| File | Purpose |
|---|---|
| `models.py` | Every Pydantic model that crosses a service boundary: `DetectedDependency`, `KnowledgeGraphEntry`, `Finding`, `MigrationPlan`, `Patch`, `VerificationResult`, `ConfidenceBreakdown`, `MigrationReport`. If two services need to agree on a shape, it's defined here once — change this file and you're changing the project's API surface, not just one service. |

## 4. `services/ingestion/` — Phase 1 (documentation engine)

| File | Purpose |
|---|---|
| `config.py` | `DocSource` seed list (which URLs to crawl) + `Settings` for chunk size, crawl concurrency, etc. |
| `schema.py` | Ingestion-specific Pydantic models: `DocumentMetadata`, `RawDocument`, `CleanDocument`, `DocumentChunk`, `EmbeddedChunk` |
| `crawler.py` | Async HTTP fetcher with ETag-based conditional re-fetch (cheap re-crawls) |
| `cleaner.py` | Strips nav/footer/ads from raw HTML, converts to markdown |
| `chunker.py` | Splits markdown into retrievable chunks — heading-aware first, then token-count-based for long sections |
| `embedder.py` | Pluggable embedding backend: `fake` (deterministic, offline) or `openai` (real) |
| `db.py` | SQLAlchemy models (`Document`, `DocumentChunk`) + async engine/session setup, with the composite index Phase 2's retrieval depends on |
| `pipeline.py` | Orchestrates crawl→clean→chunk→embed→store, with content-hash-based skip for unchanged pages |
| `requirements.txt` | This service's own dependency list (also rolled into the root `requirements.txt`) |
| `fixtures/sample_doc.html` | Fixture HTML used by the offline tests below |
| `tests/test_cleaner.py`, `test_chunker.py`, `test_embedder.py` | Offline unit tests — no network, no DB |

## 5. `services/retrieval/` — Phase 2 (hybrid search)

| File | Purpose |
|---|---|
| `hybrid_search.py` | Combines BM25 (keyword) and pgvector cosine similarity (semantic) search over `documentation_chunks`, filtered by framework/version first |
| `tests/test_hybrid_search.py` | Tests the scoring math directly (pure functions) plus a monkeypatched end-to-end ranking test |

## 6. `services/version/` — Phase 3 (version detection)

| File | Purpose |
|---|---|
| `detector.py` | Parses `package.json`/lockfiles (prefers the lockfile's exact resolved version) and `requirements.txt` to deterministically detect framework + dependency versions |
| `tests/test_detector.py` | Tests against fixture manifests, including the lockfile-preference logic |

## 7. `services/knowledge_graph/` — Phase 4 (the API knowledge graph)

| File | Purpose |
|---|---|
| `db.py` | SQLAlchemy model (`ApiEntry`) + upsert/query helpers for the `api_knowledge_graph` table |
| `seed_data.py` | **The actual domain knowledge** — 11 real, researched Next.js/React deprecations, each with a detection regex, severity, replacement, and doc URL. This is the file to edit when adding coverage for a new API or framework. |
| `query.py` | Version-aware filtering (`entries_relevant_to_version`) — decides which graph entries apply at a given framework version |
| `tests/test_query.py` | Tests the version-filtering logic |

## 8. `services/repository/` — Phase 5 (cloning)

| File | Purpose |
|---|---|
| `cloner.py` | Shallow `git clone` wrapper, returns the local path + resolved commit SHA |
| `tests/test_cloner.py` | Tests against a locally-created git repo (CI-reliable) plus one network-marked test against a live GitHub repo |

## 9. `services/analyzer/` — Phase 5/6 (the scanner)

| File | Purpose |
|---|---|
| `scanner.py` | The hybrid detection engine — regex matching for most knowledge-graph entries, plus a tree-sitter structural check specifically for the middleware→proxy rename (proven more precise than regex alone — see Testing Report Section 3) |
| `requirements.txt` | Pinned `tree_sitter`/`tree_sitter_languages` versions (version-sensitive — see comment in file) |
| `fixtures/sample_repo/` | A small fixture "repo" (middleware.ts + React files with planted deprecations) used by the scanner tests |
| `tests/test_scanner.py` | Tests detection accuracy, line numbers, and that a "modern" file correctly produces zero findings |

## 10. `services/migration/` — Phase 7 (the planner)

| File | Purpose |
|---|---|
| `planner.py` | Groups findings by API, decides automatic-vs-manual (via `AUTOMATABLE_APIS`), sorts by severity — turns raw findings into a structured `MigrationPlan` |
| `tests/test_planner.py` | Tests grouping, automatic/manual classification, and severity sorting |

## 11. `services/agent/` — Phase 8 (patch generation)

| File | Purpose |
|---|---|
| `templates.py` | Hand-written, deterministic patch transforms for the 3 APIs SyntaxHub can migrate automatically today (middleware→proxy, `ReactDOM.render`/`hydrate`) — **this is the file to extend when adding automatic-patch coverage for a new API** |
| `llm_provider.py` | Pluggable LLM abstraction — `TemplateOnlyProvider` (default, raises for anything without a template) or `OpenAIProvider` (real LLM calls for the long tail) |
| `orchestrator.py` | For each planned change: try the template first, fall through to the LLM provider, always emit a real unified diff — never a silent overwrite |
| `tests/test_templates.py`, `test_orchestrator.py` | Tests the actual generated diffs against the fixture repo |

## 12. `services/verification/` — Phase 9 (build verification + confidence)

| File | Purpose |
|---|---|
| `runner.py` | Two backends: `LocalRunner` (runs npm/node directly — what the tests use) and `DockerRunner` (isolated container — untested here, no Docker daemon available, see Testing Report) |
| `repair_loop.py` | Control flow for the capped repair loop (retry verification after a fix attempt, bounded by `max_repair_attempts`) |
| `confidence.py` | The weighted confidence formula (35/15/15/10/10/10/5, matching the original spec exactly) |
| `fixtures/buildable_project/`, `fixtures/failing_project/` | Tiny real npm projects used to test both the pass and fail paths |
| `tests/test_runner.py`, `test_confidence.py` | Tests against real `npm install`/`build` calls, and the scoring formula's math |

## 13. `services/github_integration/` — Phase 10

| File | Purpose |
|---|---|
| `webhooks.py` | HMAC signature verification (security-critical — rejects forged webhook payloads), PR event parsing, and the PR comment template |
| `tests/test_webhooks.py` | Tests signature verification (valid/tampered/wrong-secret/missing) and comment formatting |

## 14. `services/mcp_server/` — Phase 11

| File | Purpose |
|---|---|
| `tools.py` | The actual tool logic as plain async functions — no MCP SDK dependency, so they're testable with plain pytest and reusable by the FastAPI app too |
| `server.py` | Wires `tools.py` into the MCP SDK (`MCPServer`, v2 API) so a real MCP client can call them — see the version-compatibility note at the top of this file |
| `tests/test_tools.py` | Tests all 6 tools against the fixture repo |

## 15. `apps/api/` — the orchestration layer

| File | Purpose |
|---|---|
| `main.py` | The FastAPI app — `/health`, `/scan`, `/report`. `/report` is the flagship endpoint: runs the entire Phase 5→9 pipeline in one request |
| `tests/conftest.py` | Builds a real local git repo (Next.js 15 + a middleware.ts) as a pytest fixture, used by every test in this directory |
| `tests/test_main.py` | **The most important test file in the project** — real HTTP calls exercising the complete pipeline end to end |

## 16. `apps/web/` — the frontend

| File | Purpose |
|---|---|
| `package.json` | Next.js 15.5.9 + React 19.1.4 — both versions deliberately pinned past December 2025's critical RCE CVEs (see Testing Report) |
| `package-lock.json` | **Commit this** — see checklist item 3 above |
| `next.config.js` | Rewrites `/api/*` requests to the FastAPI backend (`SYNTAXHUB_API_URL`) |
| `app/layout.jsx` | Root layout — dark theme shell |
| `app/page.jsx` | The actual UI — repo URL form, migration plan display, diff viewer |

## 17. `scripts/` — operational tooling

| File | Purpose |
|---|---|
| `seed_docs.py` | Runs real Phase 1 ingestion against the seed doc sources (Next.js/React) |
| `seed_knowledge_graph.py` | Loads `seed_data.py`'s entries into Postgres |
| `demo.py` | Runs the complete pipeline from the command line, no API server or DB required — the fastest way to see the whole thing work |
| `benchmark_vs_llm.py` | SyntaxHub-vs-LLM comparison harness (needs your own API key to produce live numbers — see Testing Report Section 5) |

## 18. `docs/`

| File | Purpose |
|---|---|
| `TESTING_REPORT.md` | The empirical results — reproducibility test, real third-party repo generalization test (including a genuine found limitation), capability matrix, and the benchmark harness instructions. This is what you'd lift into a manuscript's evaluation section. |
| `PROJECT_GUIDE.md` | This file. |

---

## 19. If you're picking this up fresh (onboarding a teammate)

1. Read the main `README.md` top to bottom — it has the "what's real
   vs. pluggable" table, which is the single most important context.
2. Run `pytest -v` — confirm 59/59 passes on your machine before
   changing anything.
3. Run `PYTHONPATH=. python scripts/demo.py /some/local/repo` to see
   the whole pipeline work without needing Postgres/Docker/API keys.
4. Read `docs/TESTING_REPORT.md` Section 3 — the one confirmed gap
   (async `params`/`searchParams` detection) is a good first real
   contribution: extend `services/knowledge_graph/seed_data.py`'s
   regex, add a fixture reproducing the gap, confirm the new test
   catches it.
5. Decide, as a team, when to flip `LLM_PROVIDER=openai` and
   `EMBEDDING_PROVIDER=openai` on — both are implemented but
   deliberately not live-tested here (no budget was spent on API
   calls building this). Test with a small budget before trusting
   either on a real repo.
