# SyntaxHub — Testing Report

**Purpose:** document what was empirically tested, how, and with what
result — for use as the evaluation section of a research manuscript.
Every number in this report was produced by a command you can re-run
yourself (commands included); nothing is estimated or illustrative
unless explicitly labeled as such.

**Environment:** all tests below were run in a sandboxed Linux
container with Python 3.12, Node 22, git — but **no Docker daemon, no
`OPENAI_API_KEY`/`ANTHROPIC_API_KEY`**. This shapes what could and
couldn't be tested here; Section 5 is explicit about the gap and gives
you the exact commands to close it with your own credentials.

---

## 1. What is and isn't a fair "competitor" comparison

The earlier project spec named three reference points: general-purpose
AI assistants (ChatGPT/Claude used directly), Context7 (a documentation
retrieval MCP server), and SyntaxHub itself. Before presenting numbers,
it's worth being precise about what's comparable:

- **SyntaxHub vs. a general-purpose LLM asked directly** — this is a
  fair, testable comparison: same task ("find deprecated APIs in this
  repo"), different method (deterministic pipeline vs. LLM judgment).
  Section 3 gives a real result on a third-party repo; Section 5 gives
  you a harness to extend this with live LLM calls.
- **SyntaxHub vs. Context7** — these are not substitutable tools.
  Context7 answers "what does the current documentation for library X
  say" (per its own published capabilities — see Section 4). It does
  not scan a repository, does not maintain a deprecation knowledge
  graph, does not generate patches, and does not run a build. A
  head-to-head accuracy benchmark would be comparing a documentation
  lookup tool against a migration pipeline on a task the former was
  never built to do. Section 4 gives a capability-matrix comparison
  instead, which is the methodologically honest framing — and notes
  where SyntaxHub could *use* Context7 as a retrieval backend rather
  than compete with it.

## 2. Test 1 — Reproducibility (determinism)

**Claim being tested:** a rule-based/AST pipeline produces identical
output on identical input, every time — unlike an LLM sampling at
nonzero temperature, where the same prompt can yield different answers
on different calls.

**Method:** ran SyntaxHub's scanner 10 times against the same
repository (a real third-party Next.js project, see Section 3),
hashed each run's findings, and compared.

**Command:**
```bash
python3 -c "
import hashlib, json, time
from pathlib import Path
from services.analyzer.scanner import scan_repository
from services.knowledge_graph.seed_data import ALL_SEED_ENTRIES

repo = Path('/tmp/third_party_repo')  # see Section 3 for how this was obtained
entries = [e for e in ALL_SEED_ENTRIES if e.framework == 'nextjs']
hashes, timings = [], []
for i in range(10):
    t0 = time.time()
    findings, _ = scan_repository(repo, entries)
    timings.append(time.time() - t0)
    s = json.dumps([f.model_dump() for f in findings], sort_keys=True, default=str)
    hashes.append(hashlib.sha256(s.encode()).hexdigest())
print('Unique result hashes:', len(set(hashes)))
print(f'Mean: {sum(timings)/len(timings)*1000:.1f}ms  Stdev: ...')
"
```

**Result:**

| Metric | Value |
|---|---|
| Runs | 10 |
| Unique result hashes | **1** (100% identical) |
| Mean scan time | 7.1 ms |
| Min / Max | 6.3 ms / 12.4 ms |
| Stdev | 1.80 ms |

**Interpretation:** the deterministic scanner is perfectly reproducible
by construction — it's regex + AST matching against a fixed knowledge
graph, with no sampling involved. This is a structural property, not a
statistical one; 10 runs demonstrate it but a single code-read of
`services/analyzer/scanner.py` proves it (no randomness anywhere in the
call path). **A general-purpose LLM asked the same question has no such
guarantee** — this is a well-documented property of autoregressive
sampling, not something that needs re-proving per-repo, but Section 5's
harness lets you measure the actual variance on your own repos if your
manuscript needs an empirical number rather than citing the general
property.

## 3. Test 2 — Generalization to a real, independently-authored repository

**Why this matters:** every fixture repo used in the unit test suite
(`services/analyzer/fixtures/`) was authored by the same process that
wrote the detection rules — testing against them proves internal
consistency, not generalization. A fair test needs a repository
**nobody involved in building SyntaxHub wrote.**

**Method:** cloned a small, real, third-party Next.js project
(`onlineeric/eric-demo-nextjs`, 136 KB, MIT licensed, chosen via web
search with no prior knowledge of its contents) and ran the full scan
against it unmodified.

**Command:**
```bash
git clone --depth 1 https://github.com/onlineeric/eric-demo-nextjs.git /tmp/third_party_repo
python3 -c "
from pathlib import Path
from services.analyzer.scanner import scan_repository
from services.version.detector import detect_dependencies
from services.knowledge_graph.seed_data import ALL_SEED_ENTRIES
repo = Path('/tmp/third_party_repo')
print(detect_dependencies(repo))
entries = [e for e in ALL_SEED_ENTRIES if e.framework == 'nextjs']
findings, n = scan_repository(repo, entries)
print(f'{n} files scanned, {len(findings)} findings')
for f in findings: print(f.file_path, f.line, f.api_name)
"
```

**Result:**

| Metric | Value |
|---|---|
| Framework detected | `nextjs 15.4.6` (correctly resolved from `package-lock.json`, even though `package.json` itself said `"next": "latest"`) |
| Files scanned | 41 |
| Scan time | 12 ms |
| True positive found | `src/middleware.ts:4` — `export function middleware(...)`, correctly identified via the tree-sitter structural check (not just string matching — the file has nested conditionals, type annotations, and multiple other function-like constructs tree-sitter correctly didn't false-positive on) |

**A genuine gap, found and reported honestly:** this repo also contains
`src/app/(dashboard)/dynamic/[id]/page.tsx`, which synchronously
destructures `params: { id: string }` instead of the
`params: Promise<{ id: string }>` shape required since Next.js 15 — a
real instance of the exact deprecation SyntaxHub's knowledge graph
already lists (`"synchronous dynamic APIs"`). **SyntaxHub's scanner did
not flag it.** The regex pattern for that knowledge-graph entry
(`(headers|cookies)\(\)\.(get|has|getAll)\(`) only matches the
`headers()`/`cookies()` call form of the deprecation, not the separate
`params`/`searchParams` prop-typing form. This was confirmed by running
the repo's own `npm run typecheck`, which independently caught it as a
real TypeScript error:
```
error TS2344: Type 'Props' does not satisfy the constraint 'PageProps'.
  Types of property 'params' are incompatible.
    Type '{ id: string; }' is missing the following properties from
    type 'Promise<any>': then, catch, finally, [Symbol.toStringTag]
```

**Interpretation for the manuscript:** this is a real false negative,
found on the first external repo tested, worth citing as a known
limitation rather than omitting. It also demonstrates something useful
methodologically: **the verification stage (Phase 9) caught what the
detection stage (Phase 5/6) missed** — the build/typecheck step is not
redundant with static detection, it's a genuine second line of defense.
The concrete fix (expand the regex to also match bare `params`/
`searchParams` destructuring in page/layout component props, or add a
second tree-sitter structural check analogous to the middleware one) is
a small, well-scoped addition to `services/knowledge_graph/seed_data.py`
— left undone here deliberately, so this report reflects the project's
actual current state rather than a result tuned after the fact.

## 4. Test 3 — Capability matrix vs. named alternatives

Sourced from each tool's own published documentation (Context7: its
official docs and MCP registry listings, retrieved via web search on
2026-10-06; general LLM assistants: documented, well-known properties
of autoregressive chat models, not vendor-specific claims).

| Capability | SyntaxHub | ChatGPT/Claude, used directly | Context7 |
|---|---|---|---|
| Repository-level scanning | ✅ real (tree-sitter + regex, tested Section 3) | ❌ (would require pasting file contents manually) | ❌ (not its function) |
| Deprecation/breaking-change knowledge graph | ✅ 11 seeded entries, versioned | ❌ relies on training data, can be stale | ❌ (doesn't classify changes, only retrieves docs) |
| Version-specific documentation retrieval | ✅ Phase 1/2 (hybrid BM25+vector) | ❌ training-data cutoff, no live retrieval | ✅ this is its core function |
| Automatic patch generation | ✅ 3 APIs via deterministic templates; LLM fallback for the rest (Section 5) | ⚠️ can write code, but without repo context or verification | ❌ (not its function) |
| Build/test verification of generated patches | ✅ real, tested (Section 2 of main README) | ❌ no execution environment by default | ❌ (not its function) |
| Deterministic/reproducible output | ✅ 100% (Section 2 above) | ❌ sampling-based, no reproducibility guarantee | N/A (retrieval, not generation) |
| Confidence scoring tied to verifiable signals | ✅ weighted formula (build result, graph agreement, etc.) | ❌ no structured confidence signal | N/A |
| MCP-accessible from other AI tools | ✅ tested (6 tools, real protocol call — see main README §6) | N/A | ✅ this is Context7's primary distribution model |

**Honest framing for the manuscript:** SyntaxHub's real differentiator
isn't "better than an LLM at reading code" or "better than Context7 at
retrieving docs" — it's combining deterministic repo analysis,
versioned domain knowledge, and build verification into one pipeline,
which neither alternative does end-to-end. A credible manuscript should
present it this way rather than as a head-to-head accuracy win, which
the tools aren't built to compete on. **SyntaxHub could use Context7 as
its retrieval backend** for Phase 1/2 rather than the custom crawler
built here — worth noting as a design alternative, not a competitor.

## 5. What needs your own API key — ready to run

`scripts/benchmark_vs_llm.py` is a complete, tested harness (its
parsing/scoring logic was verified in this environment — see the main
README) that:
1. Runs SyntaxHub's scanner on a repo (real, deterministic, as above)
2. Sends the same repo's file contents to a real LLM (Claude or GPT-4o)
   with a direct "find deprecated APIs" prompt — no tools, no
   knowledge graph, the "ask the assistant directly" baseline
3. Runs the LLM call multiple times at temperature=0 to measure actual
   repeatability (not just the general property — a real number on
   your repo)
4. Reports precision/recall of the LLM's findings against SyntaxHub's

**This was not run live in the environment this project was built in**
(no API key available there). To produce real, citable numbers for
your manuscript:

```bash
export ANTHROPIC_API_KEY=sk-ant-...   # or OPENAI_API_KEY for --provider openai
python scripts/benchmark_vs_llm.py /tmp/third_party_repo --provider anthropic --repeat 5
```

This will write `benchmark_result.json` with the full comparison. **Do
this before citing any SyntaxHub-vs-LLM accuracy number in your
manuscript** — Section 3's finding (a real false negative) means
SyntaxHub is not simply "more accurate" across the board, and the
manuscript should reflect whatever the harness actually reports, not
an assumed result.

For Context7, there is no meaningful accuracy benchmark to run (see
Section 1) — if your manuscript needs a Context7 comparison, frame it
as the capability matrix in Section 4, sourced from Context7's own
documentation (linked in that section's sourcing note).

## 6. Summary table for the manuscript

| Test | Type | Result | Reproducible by reader? |
|---|---|---|---|
| Determinism (10 runs) | Measured here | 100% identical output | Yes — command included |
| Third-party repo generalization | Measured here | 1/2 known-pattern deprecations caught; 1 real gap found and documented | Yes — public repo, command included |
| Scan performance | Measured here | ~7-12ms for a 41-file repo | Yes |
| Full pipeline latency | Measured here | ~68s on a real repo, 99.9% of which is `npm install`/build (not SyntaxHub's own logic) | Yes |
| Capability vs. general LLM assistants | Documented comparison | SyntaxHub adds repo-scanning, a knowledge graph, verification, and determinism that direct LLM use lacks | Matrix sourced, not benchmarked |
| Capability vs. Context7 | Documented comparison | Different problem scope — not a fair accuracy comparison (see §1) | Matrix sourced from Context7's own docs |
| SyntaxHub vs. live LLM accuracy | **Not run — needs your API key** | Harness ready (`scripts/benchmark_vs_llm.py`) | Yes, once you add a key |
