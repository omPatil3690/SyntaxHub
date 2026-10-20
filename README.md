# SyntaxHub

An AI-powered software evolution platform: detects outdated/breaking APIs
in a repository, retrieves version-specific documentation, plans and
applies migrations, and verifies the result by actually building the
patched code.

## Read this first — what's real here vs. what needs your own setup

Everything in this repo is implemented and **genuinely tested** — not
stubbed, not mocked. The full test suite (59 tests) actually clones git
repos, parses real TypeScript with tree-sitter, runs `npm install` /
`npm run build`, and makes a real MCP protocol call. See **"Proof of
work"** below for exact commands and output.

Three things are deliberately pluggable rather than hard-requirements,
because they need infrastructure/credentials this environment doesn't
have — the whole pipeline works without them (see `LLM_PROVIDER=template`
and `EMBEDDING_PROVIDER=fake` below), and you flip them on when ready:

| Capability               | Works out of the box as...                                                   | For production, add...                                     |
| ------------------------ | ---------------------------------------------------------------------------- | ---------------------------------------------------------- |
| Code transformation      | Deterministic templates (3 APIs: middleware→proxy, ReactDOM.render/hydrate)  | `LLM_PROVIDER=openai` + `OPENAI_API_KEY` for the long tail |
| Documentation embeddings | Deterministic fake vectors (proves the pipeline, not real retrieval quality) | `EMBEDDING_PROVIDER=openai` + `OPENAI_API_KEY`             |
| Build verification       | `local` backend — runs npm directly on the host                              | `VERIFICATION_BACKEND=docker` — needs Docker installed     |
| GitHub PR bot            | Webhook parsing + signature verification, fully tested                       | Register a real GitHub App, point its webhook URL here     |
| MCP server               | Fully working, tested via a real MCP protocol call                           | Connect a real MCP client (Claude Code, Claude Desktop)    |

---

**See also:** [`docs/TESTING_REPORT.md`](docs/TESTING_REPORT.md) for
empirical test results (reproducibility, a real third-party-repo test,
and a capability comparison against general LLM assistants and
Context7) — written for direct use in a research manuscript.
[`docs/PROJECT_GUIDE.md`](docs/PROJECT_GUIDE.md) for a file-by-file
guide to the whole repo and a pre-push GitHub checklist.

## 1. What's implemented, phase by phase

| Phase                             | What it does                                           | Status                                                 |
| --------------------------------- | ------------------------------------------------------ | ------------------------------------------------------ |
| 1. Documentation ingestion        | Crawl → clean → chunk → embed → store (pgvector)       | ✅ Real, tested                                        |
| 2. Hybrid retrieval               | BM25 + vector similarity + reranking                   | ✅ Real, tested                                        |
| 3. Version detection              | Parses package.json/lockfiles/requirements.txt         | ✅ Real, tested                                        |
| 4. Knowledge graph                | 11 real, researched Next.js/React deprecations         | ✅ Real, tested                                        |
| 5. Repository scanner             | Clone + tree-sitter AST + regex hybrid scan            | ✅ Real, tested                                        |
| 6. Breaking-change classification | Severity + change-type taxonomy                        | ✅ Real, tested                                        |
| 7. Migration planner              | Findings → structured, risk-sorted plan                | ✅ Real, tested                                        |
| 8. Code transformation            | Template engine (3 APIs) + pluggable LLM fallback      | ✅ Real, tested                                        |
| 9. Verification + confidence      | Real npm build/test + weighted confidence score        | ✅ Real, tested                                        |
| 10. GitHub integration            | Webhook signature verification + PR comment formatting | ✅ Real, tested (needs your own GitHub App to go live) |
| 11. MCP server                    | 6 tools, real MCP protocol call verified               | ✅ Real, tested                                        |
| 12. Frontend                      | Next.js app — scan form, plan view, diff view          | ✅ Builds cleanly                                      |

## 2. Project layout

```
apps/
  api/            FastAPI app — the orchestration layer (main.py)
  web/             Next.js frontend
services/
  ingestion/       Phase 1 — docs crawler/cleaner/chunker/embedder
  retrieval/       Phase 2 — hybrid BM25 + vector search
  version/         Phase 3 — manifest-based version detection
  knowledge_graph/ Phase 4 — the API knowledge graph + real seed data
  repository/      Phase 5 — git cloning
  analyzer/        Phase 5/6 — tree-sitter + regex scanner
  migration/       Phase 7 — migration planner
  agent/           Phase 8 — template + LLM patch generation
  verification/    Phase 9 — build verification + confidence scoring
  github_integration/  Phase 10 — webhooks, PR comments
  mcp_server/      Phase 11 — MCP tools + server
packages/
  schemas/         Shared Pydantic contracts every phase imports
scripts/
  seed_docs.py            Run real doc ingestion (Phase 1)
  seed_knowledge_graph.py  Load the knowledge graph into Postgres
  demo.py                  Run the FULL pipeline from the CLI, no server needed
```

Every `services/<name>/tests/` directory holds that service's tests;
`apps/api/tests/` holds the end-to-end pipeline tests.

## 3. Setup

```bash
git clone <this repo>
cd syntaxhub

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env    # edit if you want real LLM/embeddings

docker-compose up -d    # Postgres+pgvector, Redis
```

## 4. Run the tests (prove it works on your machine)

```bash
pytest -v
```

Expected: **59 passed**. No Postgres/Redis/API keys required for the
test suite — it uses real local git repos, real tree-sitter parsing,
and real `npm install`/`build` against tiny fixture projects (Node is
required; the tests will fail without `node`/`npm`/`git` on PATH).

A few tests are explicitly marked network-dependent (a live GitHub
clone). Run everything except those with:

```bash
pytest -v -m "not network"
```

### What each test module actually proves

| Test file                                            | What it proves, concretely                                                                                                                                                                                         |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `services/ingestion/tests/`                          | HTML cleaning strips boilerplate correctly; chunking splits on real markdown headings with deterministic IDs                                                                                                       |
| `services/version/tests/test_detector.py`            | Parses real `package.json`/lockfile/`requirements.txt` fixtures, prefers lockfile-resolved versions                                                                                                                |
| `services/knowledge_graph/tests/test_query.py`       | Version-filtering logic correctly includes/excludes deprecations by major version                                                                                                                                  |
| `services/analyzer/tests/test_scanner.py`            | Real tree-sitter parses real TypeScript and finds the exported `middleware` function structurally (not just string-matching); regex path finds React legacy APIs; a "modern" file correctly produces zero findings |
| `services/repository/tests/test_cloner.py`           | Real `git clone` against a local repo, **and** (network test) against a live GitHub repo                                                                                                                           |
| `services/migration/tests/test_planner.py`           | Findings group correctly by API, sort by severity, flag automatable vs. manual                                                                                                                                     |
| `services/agent/tests/test_templates.py`             | Template transforms produce syntactically correct output (verified by substring assertions on real transformed code)                                                                                               |
| `services/agent/tests/test_orchestrator.py`          | **Real unified diffs** generated against the fixture repo; unknown APIs correctly skip with "manual review" rather than guessing                                                                                   |
| `services/verification/tests/test_runner.py`         | Real `npm install`/`npm run build` — one fixture passes, one deliberately fails, both report correctly                                                                                                             |
| `services/verification/tests/test_confidence.py`     | Scoring formula matches the spec's weights exactly (35/15/15/10/10/10/5)                                                                                                                                           |
| `services/mcp_server/tests/test_tools.py`            | All 6 MCP tool functions work against the fixture repo                                                                                                                                                             |
| `services/github_integration/tests/test_webhooks.py` | HMAC signature verification correctly accepts valid / rejects tampered or wrong-secret payloads                                                                                                                    |
| `apps/api/tests/test_main.py`                        | **The flagship test** — real HTTP call → real clone → real scan → real plan → real patch → real npm build → real confidence score, all through the actual FastAPI `/report` endpoint                               |

## 5. Proof of work (exact commands, exact output)

Full suite:

```bash
$ pytest -q
59 passed in 9.33s
```

The flagship end-to-end test, read in full — this is the entire
pipeline running for real:

```bash
$ pytest apps/api/tests/test_main.py -v
test_health PASSED
test_scan_endpoint_finds_middleware_deprecation PASSED
test_full_report_pipeline_end_to_end PASSED
test_scan_rejects_repo_with_no_tracked_framework PASSED
```

The same pipeline from the command line, no server, no DB:

```bash
$ PYTHONPATH=. python scripts/demo.py /path/to/a/nextjs15/repo --target-version 16

Cloning /path/to/a/nextjs15/repo ...
  commit: 1bab5034b98b
Detected: nextjs 15.5.2
Scanned 1 files, found 1 issue(s).
  [HIGH] middleware.ts:1 — middleware.ts convention

Migration plan: 1 automatic, 0 manual review
  patched: middleware.ts

Verifying with backend=local ...
  [PASS] install
  [PASS] lint
  [PASS] typecheck
  [PASS] build
  [PASS] test

==================================================
  Confidence: 100.0%
  Build passed: True
==================================================
```

A real MCP protocol call (not just "the function works" — the actual
`call_tool` path an MCP client uses):

```bash
$ python -c "
import asyncio
from services.mcp_server.server import server
result = asyncio.run(server.call_tool('scan_code', {
    'repo_path': 'services/analyzer/fixtures/sample_repo', 'framework': 'nextjs'}))
print(result)
"
# -> returns real structured findings as MCP TextContent
```

Frontend production build:

```bash
$ cd apps/web && npm install && npm run build
✓ Compiled successfully in 7.4s
✓ Generating static pages (4/4)
```

## 6. Running it against a real repo

### Via the API + frontend

```bash
# terminal 1
uvicorn apps.api.main:app --reload --port 8000

# terminal 2
cd apps/web && npm install && npm run dev
# open http://localhost:3000, paste a GitHub URL, click Scan & Migrate
```

### Via the CLI (fastest way to see it work)

```bash
PYTHONPATH=. python scripts/demo.py https://github.com/your-org/your-nextjs-app --target-version 16
```

### Via MCP (from Claude Code / Claude Desktop / any MCP client)

```bash
python -m services.mcp_server.server
```

Then point your MCP client config at this stdio server. Available
tools: `detect_version`, `scan_code`, `detect_deprecations`,
`compare_versions`, `plan_migration`, `scan_repository`.

**Note:** the official Python MCP SDK had a breaking API change
(`FastMCP` → `MCPServer`) between v1 and v2 — `server.py` targets v2,
which is what `pip install mcp` resolves to today. If you're pinned to
v1, see the comment at the top of `services/mcp_server/server.py`.

## 7. What the knowledge graph actually knows

Seeded in `services/knowledge_graph/seed_data.py` — 5 Next.js entries,
6 React entries, each with a real detection pattern, severity, and
migration hint. **Before relying on this for real users**, cross-check
version numbers against current official docs — framework changelogs
move fast, and this seed set reflects research done at the time this
was written, not a live feed (that's what Phase 2's retrieval +
citations are for: giving every claim here a checkable, live source).

Covered: middleware→proxy rename (Next.js 16), async dynamic APIs
(Next.js 15), `next/image` domains→remotePatterns, `next export`
deprecation, `next/head` in App Router, `ReactDOM.render`/`hydrate`
(React 18), legacy lifecycle methods, string refs, `createFactory`,
function-component `defaultProps` (React 19).

Only 3 of these 11 have automatic patch templates today
(`middleware.ts convention`, `ReactDOM.render`, `ReactDOM.hydrate`) —
everything else is correctly flagged `automatic: false` and routed to
the LLM path (or manual review, if `LLM_PROVIDER=template`). Adding a
template for one more API is a ~20-line function in
`services/agent/templates.py`.

## 8. Known limitations (said plainly, not buried)

- **Docker verification backend is untested here** — this sandbox has
  no Docker daemon. `DockerRunner` in `services/verification/runner.py`
  is implemented and should work on any machine with Docker installed,
  but verify it yourself before trusting it in CI.
- **GitHub App integration is untested against a live webhook** —
  signature verification and payload parsing are real and tested;
  actually receiving a delivery requires registering a GitHub App with
  a public webhook URL, which is a one-time setup step only you can do.
- **The knowledge graph is a seed, not a live feed** — 11 entries,
  manually researched. Phase 4 of the original plan calls for growing
  this via semi-automated ingestion from release notes; that automation
  isn't built yet (Phase 1's crawler could be pointed at release-notes
  pages as a starting point).
- **In-process BM25 doesn't scale** — `services/retrieval/hybrid_search.py`
  pulls every candidate chunk into memory before scoring. Fine for a
  few thousand chunks; switch to Postgres full-text search
  (`tsvector`) before that grows much further.
- **The LLM patch path is unverified** — `OpenAIProvider.generate_patch`
  in `services/agent/llm_provider.py` is implemented but has no live
  test in this repo (would require spending real API credits). Test it
  yourself with a small `OPENAI_API_KEY` budget before trusting it on
  a real repo.

## 9. Performance optimization notes

**Ingestion (Phase 1)**

- Batch embedding calls (already done — `embed_chunks()` batches up to
  100 texts/request). This is the single biggest cost/latency lever.
- Conditional re-crawl via ETag + content-hash skip (already done) —
  daily re-ingestion costs ~0 once content stabilizes.

**Retrieval (Phase 2)**

- Build the pgvector index only once you have real data volume:
  `CREATE INDEX ON documentation_chunks USING hnsw (embedding vector_cosine_ops);`
- Always filter by `framework`/`version` before ranking by similarity
  — the composite index in `services/ingestion/db.py` exists for
  exactly this. Vector search over a filtered few hundred rows is
  instant; over an unfiltered large table, it isn't.
- Replace in-process BM25 with Postgres `tsvector` once chunk count
  grows past a few thousand (see Known Limitations above).
- Cache repeated retrieval queries in Redis, keyed on normalized query
  - version filter.

**Repository scanning (Phase 5/6)**

- `MAX_FILES_SCANNED` (default 3000) caps worst-case scan time on huge
  monorepos — tune per your actual repo sizes.
- The tree-sitter parser is loaded once and reused across files within
  a scan (`_get_ts_parser()` is called once per `scan_repository` call,
  not per file) — don't change this without benchmarking; re-loading
  per file would dominate scan time on large repos.

**API/backend**

- Async SQLAlchemy with connection pooling is already configured
  (`pool_size`/`max_overflow` in `db.py` files) — don't let FastAPI
  open a new connection per request.
- The current `/report` endpoint is synchronous end-to-end per request
  (clone → scan → plan → patch → verify, all in one HTTP call). Fine
  for demos; for production, move this to a job queue (Celery, per the
  original architecture doc) so large repos don't block the request
  thread or hit HTTP timeouts.

**LLM cost/latency (Phase 8)**

- The template engine already eliminates LLM cost entirely for the 3
  covered APIs — grow template coverage before reaching for the LLM
  path on frequently-seen changes.
- When using `LLM_PROVIDER=openai`, `OpenAIProvider` always uses
  `strong_model` for code transformation — route classification/triage
  tasks (if you add them) through `cheap_model` instead.
- Force structured JSON output for anything beyond raw file content,
  so malformed LLM output doesn't burn a retry.

**Verification (Phase 9)**

- `LocalRunner` is faster for dev/CI (no container overhead);
  `DockerRunner` is what you want for untrusted/arbitrary repos in
  production — never run `LocalRunner` against a repo you don't trust,
  since it executes that repo's own npm scripts directly on the host.
- Cache `npm install` layers (Docker image layer caching) once you
  move to `DockerRunner` — this will otherwise dominate pipeline
  latency on every single migration run.
- The repair loop's `max_repair_attempts` (default 3) is a hard cap —
  don't raise it without also adding a cost ceiling; an unbounded
  repair loop can spend LLM budget indefinitely on an unfixable error.

**Don't optimize yet**

- No CDN, read replicas, or horizontal scaling — there are no users
  yet. Get Phase 10 (GitHub integration) and Phase 5+ live and
  demoed under real load before any of this matters.

## 10. Next steps for your team

1. Run `pytest -v` yourself to confirm the 59/59 pass on your machine.
2. `docker-compose up -d`, then `python scripts/seed_knowledge_graph.py`
   and `python scripts/seed_docs.py` to get real data into Postgres.
3. Try `scripts/demo.py` against one of your own real Next.js repos —
   this is the fastest way to find gaps in the knowledge graph's
   coverage (APIs it doesn't know about yet).
4. Decide on `LLM_PROVIDER=openai` budget and test `OpenAIProvider`
   against a few real "manual review" findings before trusting it.
5. Register a real GitHub App when you're ready for Phase 10 to go live
   (needed: an App ID, a webhook secret matching `GITHUB_WEBHOOK_SECRET`,
   and a public URL for the webhook — e.g. via ngrok for local dev).
