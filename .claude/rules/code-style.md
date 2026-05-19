# Code style

## Python (backend/)
- Python 3.11. Type-hint every function signature.
- Format with `black` (default config, line-length 100).
- Imports sorted by `ruff` / `isort` — stdlib, third-party, local.
- Pydantic v2 syntax (`model_config = ConfigDict(...)`, not v1 `class Config`).
- SQLAlchemy 2.x style: `Mapped[T]`, `mapped_column(...)`. No legacy `Column()` declarations.
- Pandas/openpyxl: never trust auto-inferred dtypes for date columns — convert explicitly (see PRD §14.1, §14.2, §27).
- Always `.strip()` biometric `status` values. Preserve U+00BD (½).

## JavaScript / React (frontend/)
- Functional components only. Hooks for state. No class components.
- Format with `prettier` (default config). Tailwind classes ordered by Prettier's tailwindcss plugin if available.
- Axios via the `src/api/` layer — components must not call axios directly.
- All API URLs through the shared base path `/api/v1`; never hard-code `http://backend:8000`.

## Naming
- Python: `snake_case` for vars/functions, `PascalCase` for classes, `SCREAMING_SNAKE_CASE` for module-level constants.
- React: `PascalCase` for components, `camelCase` for hooks (`useFoo`), `kebab-case` for filenames where the file is not a component.
- Routers: one router per resource (`auth.py`, `upload.py`, …) — no monolithic `routes.py`.

## Comments
Default to none. Only add a comment when the WHY is non-obvious — a hidden constraint, a workaround for a PRD §27 quirk, an invariant a future reader would otherwise miss.
