"""
Seed entries for the API Knowledge Graph, covering Next.js and React as
scoped for Phase 1/4. These reflect genuinely documented framework
changes, but framework changelogs move fast — before relying on this
for real user-facing migrations, cross-check each entry's version
numbers against the current official docs/release notes. Treat this as
a well-researched starting seed, not a guaranteed-current source of truth
(that's exactly why Phase 2's retrieval + citations exist: to back
every claim here with a live, checkable source).

`detection_pattern` is a Python regex matched against raw source lines
by services/analyzer. The middleware->proxy rename is additionally
verified structurally via tree-sitter in the analyzer (see analyzer.py)
since it's the flagship example used throughout this project's spec.
"""
from __future__ import annotations

from packages.schemas.models import ApiStatus, ChangeType, KnowledgeGraphEntry, Severity

NEXTJS_ENTRIES: list[KnowledgeGraphEntry] = [
    KnowledgeGraphEntry(
        framework="nextjs",
        api_name="middleware.ts convention",
        deprecated_in="16",
        status=ApiStatus.DEPRECATED,
        replacement="proxy.ts",
        change_type=ChangeType.RENAMED,
        severity=Severity.HIGH,
        detection_pattern=r"export\s+(default\s+)?function\s+middleware\s*\(",
        migration_hint="Rename middleware.ts to proxy.ts and rename the exported "
                        "function from `middleware(request)` to `proxy(request)`.",
        doc_url="https://nextjs.org/docs/app/guides/upgrading/version-16",
    ),
    KnowledgeGraphEntry(
        framework="nextjs",
        api_name="synchronous dynamic APIs (headers/cookies/params/searchParams)",
        deprecated_in="15",
        status=ApiStatus.DEPRECATED,
        replacement="await headers() / await cookies() / await params / await searchParams",
        change_type=ChangeType.SIGNATURE_CHANGED,
        severity=Severity.HIGH,
        detection_pattern=r"(?<!await\s)(headers|cookies)\(\)\.(get|has|getAll)\(",
        migration_hint="These request-specific APIs are now asynchronous. "
                        "Await them: `const c = await cookies();` before use.",
        doc_url="https://nextjs.org/docs/app/guides/upgrading/version-15",
    ),
    KnowledgeGraphEntry(
        framework="nextjs",
        api_name="next/image domains config",
        deprecated_in="14",
        status=ApiStatus.DEPRECATED,
        replacement="images.remotePatterns",
        change_type=ChangeType.CONFIG_CHANGED,
        severity=Severity.MEDIUM,
        detection_pattern=r"images\s*:\s*\{[^}]*\bdomains\s*:",
        migration_hint="Replace the `images.domains` array in next.config.js with "
                        "`images.remotePatterns`, which lets you scope protocol/path too.",
        doc_url="https://nextjs.org/docs/app/api-reference/components/image#remotepatterns",
    ),
    KnowledgeGraphEntry(
        framework="nextjs",
        api_name="next export command",
        deprecated_in="13.3",
        status=ApiStatus.DEPRECATED,
        replacement="output: 'export' in next.config.js",
        change_type=ChangeType.CONFIG_CHANGED,
        severity=Severity.MEDIUM,
        detection_pattern=r"\"next export\"|'next export'|next\s+export\b",
        migration_hint="Set `output: 'export'` in next.config.js and use the "
                        "regular `next build` command instead of `next export`.",
        doc_url="https://nextjs.org/docs/app/guides/static-exports",
    ),
    KnowledgeGraphEntry(
        framework="nextjs",
        api_name="next/head in App Router",
        deprecated_in="13",
        status=ApiStatus.DEPRECATED,
        replacement="Metadata API (export const metadata / generateMetadata)",
        change_type=ChangeType.BEHAVIOR_CHANGED,
        severity=Severity.LOW,
        detection_pattern=r"from\s+[\"']next/head[\"']",
        migration_hint="In the App Router, replace <Head> usage with the "
                        "Metadata API: export a `metadata` object or `generateMetadata()`.",
        doc_url="https://nextjs.org/docs/app/api-reference/functions/generate-metadata",
    ),
]

REACT_ENTRIES: list[KnowledgeGraphEntry] = [
    KnowledgeGraphEntry(
        framework="react",
        api_name="ReactDOM.render",
        deprecated_in="18",
        status=ApiStatus.DEPRECATED,
        replacement="createRoot(container).render(...)",
        change_type=ChangeType.SIGNATURE_CHANGED,
        severity=Severity.HIGH,
        detection_pattern=r"ReactDOM\.render\s*\(",
        migration_hint="Replace `ReactDOM.render(<App/>, el)` with "
                        "`createRoot(el).render(<App/>)` from 'react-dom/client'.",
        doc_url="https://react.dev/blog/2022/03/08/react-18-upgrade-guide",
    ),
    KnowledgeGraphEntry(
        framework="react",
        api_name="ReactDOM.hydrate",
        deprecated_in="18",
        status=ApiStatus.DEPRECATED,
        replacement="hydrateRoot(container, <App/>)",
        change_type=ChangeType.SIGNATURE_CHANGED,
        severity=Severity.HIGH,
        detection_pattern=r"ReactDOM\.hydrate\s*\(",
        migration_hint="Replace `ReactDOM.hydrate(<App/>, el)` with "
                        "`hydrateRoot(el, <App/>)` from 'react-dom/client'.",
        doc_url="https://react.dev/blog/2022/03/08/react-18-upgrade-guide",
    ),
    KnowledgeGraphEntry(
        framework="react",
        api_name="componentWillMount / componentWillReceiveProps / componentWillUpdate",
        deprecated_in="16.3",
        status=ApiStatus.DEPRECATED,
        replacement="UNSAFE_componentWillMount / constructor+getDerivedStateFromProps / componentDidUpdate",
        change_type=ChangeType.RENAMED,
        severity=Severity.MEDIUM,
        detection_pattern=r"\b(componentWillMount|componentWillReceiveProps|componentWillUpdate)\s*\(",
        migration_hint="These lifecycle methods are unsafe under concurrent rendering. "
                        "Migrate to the recommended replacements documented per-method.",
        doc_url="https://react.dev/reference/react/Component#unsafe_componentwillmount",
    ),
    KnowledgeGraphEntry(
        framework="react",
        api_name="String refs",
        deprecated_in="16",
        status=ApiStatus.DEPRECATED,
        replacement="useRef() or callback refs",
        change_type=ChangeType.BEHAVIOR_CHANGED,
        severity=Severity.LOW,
        detection_pattern=r"ref\s*=\s*[\"'][a-zA-Z_][\w]*[\"']",
        migration_hint="String refs are legacy and will be removed. Use `useRef()` "
                        "in function components or a callback ref instead.",
        doc_url="https://react.dev/reference/react/Component#refs",
    ),
    KnowledgeGraphEntry(
        framework="react",
        api_name="React.createFactory",
        deprecated_in="16.13",
        status=ApiStatus.DEPRECATED,
        replacement="JSX or React.createElement",
        change_type=ChangeType.REMOVED,
        severity=Severity.LOW,
        detection_pattern=r"React\.createFactory\s*\(",
        migration_hint="Replace `React.createFactory(Component)` calls with JSX "
                        "or direct `React.createElement(Component, ...)` calls.",
        doc_url="https://react.dev/reference/react/createFactory",
    ),
    KnowledgeGraphEntry(
        framework="react",
        api_name="defaultProps on function components",
        deprecated_in="19",
        status=ApiStatus.DEPRECATED,
        replacement="JavaScript default parameters",
        change_type=ChangeType.BEHAVIOR_CHANGED,
        severity=Severity.LOW,
        detection_pattern=r"function\s+\w+\.defaultProps\s*=|\w+\.defaultProps\s*=\s*\{",
        migration_hint="Function components no longer support `defaultProps`. Use "
                        "default parameter values in the function signature instead.",
        doc_url="https://react.dev/blog/2024/04/25/react-19-upgrade-guide",
    ),
]

ALL_SEED_ENTRIES: list[KnowledgeGraphEntry] = NEXTJS_ENTRIES + REACT_ENTRIES
