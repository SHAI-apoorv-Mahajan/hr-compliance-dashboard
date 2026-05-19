# src/ui — React frontend

Maps to `frontend/src/` (PRD §22). React 18 + Vite, Tailwind, React Router v6, Axios, Recharts.

## Layout
```
frontend/src/
├── main.jsx                 # React entry, mounts App, sets up router
├── App.jsx                  # Routes + AuthProvider
├── api/
│   ├── client.js            # Axios instance + interceptors
│   ├── auth.js              # login, me
│   ├── upload.js            # 3 upload endpoints, history, delete
│   ├── pipeline.js
│   ├── employees.js
│   ├── attendance.js
│   ├── leave.js
│   ├── flags.js
│   ├── email.js             # send, templates, logs, config-status
│   ├── settings.js
│   └── analytics.js
├── components/              # Shared: Layout, ProtectedRoute, Banner, etc.
├── pages/
│   ├── Login.jsx
│   ├── Dashboard.jsx
│   ├── Upload.jsx
│   ├── Employees.jsx
│   ├── Attendance.jsx
│   ├── Leave.jsx
│   ├── Flags.jsx
│   ├── EmailCenter.jsx
│   └── Settings.jsx
├── context/
│   └── AuthContext.jsx      # token + user state, login/logout
└── utils/                   # date formatters, status → color mapping, etc.
```

## Hard rules
- **Functional components only.** Hooks for state. No class components.
- **Pages never call axios directly.** All API access goes through `src/api/`.
- **No hard-coded backend URLs.** Use the `/api/v1` relative path — nginx proxies to `http://backend:8000` (PRD §23 nginx.conf).
- **Auth flow:**
  - JWT stored in `localStorage` as `access_token`.
  - Axios request interceptor in `api/client.js` injects `Authorization: Bearer <token>`.
  - Response interceptor on 401 clears `localStorage` and redirects to `/login`.
- **Charts use Recharts.** No D3, Chart.js, ECharts, or alternates.
- **Calendar heatmap colors are exact** (FR-011): green=Present, red=Absent, yellow=½Present, grey=WeeklyOff, blue=Approved Leave. Permanent WFH NS-shift Absent renders neutral/grey, not red.
- **Email Center banner.** Always check `GET /api/v1/email/config-status` on mount. If `configured === false`, render a non-dismissable yellow banner with the exact text from PRD §19 Page 8.
- **Settings → System Config** shows `Set ✓` / `Not Set ✗` only — **never** the actual GRAPH_* values.

## Styling
- Tailwind utility classes only. No external CSS beyond `index.css` and `tailwind.config.js`.
- Mobile-responsive design is **out of scope** for v1 — design for desktop browsers (PRD §3 non-goal).

## State management
- Local state with `useState`/`useReducer`. AuthContext for auth-scoped state.
- No Redux / Zustand / Recoil. If you reach for one, you've over-scoped.

## What never goes here
- Business logic that belongs in the backend (flag evaluation, parsing, threshold checks).
- API URL construction outside `src/api/`.
- Direct DOM manipulation (`document.querySelector`, `getElementById`).
