# SyntaxHub — Architecture

## Pipeline

```
GitHub Repo / Local Project / Snippet
              ↓
      Repository Analyzer
              ↓
   ┌──────────┴──────────┐
   ↓                     ↓
Version Detection    AST Analysis
   └──────────┬──────────┘
              ↓
      API Knowledge Graph
              ↓
     Version-Aware Retrieval
              ↓
      Breaking Change Engine
              ↓
       Migration Planner
              ↓
     AI Code Transformation
              ↓
      Static Analysis / Lint
              ↓
    Build + Test Verification
              ↓
   ┌──────────┴──────────┐
   ↓                     ↓
Migration Report    Confidence + Citations
```

## Three intelligence layers (do not blur these)

1. **Deterministic** — package manifests, AST, version rules, static
   analysis, build/test results. This is ground truth.
2. **Retrieval** — official documentation, migration guides, release
   notes, GitHub. This is evidence.
3. **Generative** — LLM reasoning: migration planning, code
   transformation, explanation, repair.

The LLM is never the source of truth. Hierarchy: official docs → structured
API knowledge → static analysis → LLM reasoning.

## Data model (Postgres + pgvector)

`users, repositories, frameworks, versions, packages, apis, api_changes,
migrations, documentation, documentation_chunks, embeddings, scans,
findings, migration_results, verification_results`

## Service layer (apps/api/app/services)

`repository, version, documentation, retrieval, api_intelligence,
migration, verification, agent` — one package per service, wired together
by a LangGraph state machine in `agent`.

## What NOT to use (and why)

- ChromaDB / Pinecone — pgvector already covers vector search alongside
  relational metadata in one database.
- MongoDB — the data is highly relational.
- Multiple agent frameworks — LangGraph only; it's built for stateful,
  branching, resumable workflows, unlike a flat LangChain agent chain.
- LLM for AST parsing, version detection, or deprecated-API detection —
  use deterministic parsing (Tree-sitter / TS Compiler API / Python ast)
  and structured API metadata; the LLM reasons over that, it doesn't
  replace it.
