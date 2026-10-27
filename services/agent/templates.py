"""
Template-based patch generation for the APIs marked `automatic=True` in
services/migration/planner.py's AUTOMATABLE_APIS. These are hand-written,
deterministic transforms — not LLM output — which is exactly why they're
trustworthy enough to apply automatically without a human reviewing each
line. Add a template here only when the transform is genuinely mechanical;
anything requiring judgment belongs in the LLM path (llm_provider.py)
instead, reviewed as "manual" in the plan.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class TemplateResult:
    new_content: str
    explanation: str
    suggested_new_filename: str | None = None  # set when the API change requires a file rename


def _rename_middleware_to_proxy(content: str) -> TemplateResult:
    new_content = re.sub(
        r"export\s+(default\s+)?function\s+middleware\s*\(",
        lambda m: f"export {m.group(1) or ''}function proxy(",
        content,
    )
    return TemplateResult(
        new_content=new_content,
        explanation="Renamed exported function `middleware` to `proxy` per the "
                    "Next.js 16 middleware->proxy convention change.",
        suggested_new_filename="proxy.ts",
    )


def _reactdom_render_to_createroot(content: str) -> TemplateResult:
    # Add the createRoot import if not already present.
    if "react-dom/client" not in content:
        if re.search(r"^import\s+ReactDOM\s+from\s+[\"']react-dom[\"'];?\s*$", content, re.MULTILINE):
            content = re.sub(
                r"^import\s+ReactDOM\s+from\s+[\"']react-dom[\"'];?\s*$",
                'import { createRoot } from "react-dom/client";',
                content, flags=re.MULTILINE,
            )
        else:
            content = 'import { createRoot } from "react-dom/client";\n' + content

    new_content = re.sub(
        r"ReactDOM\.render\s*\(\s*(.+?),\s*(.+?)\s*\)\s*;",
        lambda m: f"createRoot({m.group(2)}).render({m.group(1)});",
        content, flags=re.DOTALL,
    )
    return TemplateResult(
        new_content=new_content,
        explanation="Replaced `ReactDOM.render(element, container)` with "
                    "`createRoot(container).render(element)` per the React 18 upgrade guide.",
    )


def _reactdom_hydrate_to_hydrateroot(content: str) -> TemplateResult:
    if "react-dom/client" not in content:
        content = re.sub(
            r"^import\s+ReactDOM\s+from\s+[\"']react-dom[\"'];?\s*$",
            'import { hydrateRoot } from "react-dom/client";',
            content, flags=re.MULTILINE,
        )
    new_content = re.sub(
        r"ReactDOM\.hydrate\s*\(\s*(.+?),\s*(.+?)\s*\)\s*;",
        lambda m: f"hydrateRoot({m.group(2)}, {m.group(1)});",
        content, flags=re.DOTALL,
    )
    return TemplateResult(
        new_content=new_content,
        explanation="Replaced `ReactDOM.hydrate(element, container)` with "
                    "`hydrateRoot(container, element)` per the React 18 upgrade guide.",
    )


TEMPLATES = {
    "middleware.ts convention": _rename_middleware_to_proxy,
    "ReactDOM.render": _reactdom_render_to_createroot,
    "ReactDOM.hydrate": _reactdom_hydrate_to_hydrateroot,
}


def has_template(api_name: str) -> bool:
    return api_name in TEMPLATES


def apply_template(api_name: str, content: str) -> TemplateResult:
    if api_name not in TEMPLATES:
        raise KeyError(f"no template registered for '{api_name}'")
    return TEMPLATES[api_name](content)
