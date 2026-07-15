# AION Frontend — Setup Instructions

## Quick Start

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

Backend must be running at http://localhost:8000 with all services (PostgreSQL, Neo4j, Qdrant, Redis, Kafka, MinIO).

---

## REQUIRED: Fix Route Conflict Before First Build

**Delete this file** to avoid a Next.js build error (two pages at URL `/`):

```bash
# Windows PowerShell
Remove-Item "src/app/(dashboard)/page.tsx"

# Unix/macOS
rm 'src/app/(dashboard)/page.tsx'
```

**Why:** `src/app/page.tsx` (landing page) and `src/app/(dashboard)/page.tsx` both resolve to URL `/` in Next.js App Router. The `(dashboard)` route group doesn't add a URL segment. You must keep only one — delete the `(dashboard)` one.

---

## Route Map

| URL | Page |
|-----|------|
| `/` | Landing page |
| `/login` | Login |
| `/register` | Registration |
| `/dashboard` | Main dashboard |
| `/dashboard/intelligence` | OII Intelligence Index |
| `/dashboard/mri` | Organizational MRI |
| `/dashboard/diseases` | Disease Detection |
| `/dashboard/simulation` | Future Simulation |
| `/dashboard/healing` | Self-Healing Protocol |
| `/dashboard/decay` | Knowledge Decay Engine |
| `/dashboard/ocsie` | OCSIE Employee List |
| `/dashboard/ocsie/[employeeId]` | Employee Profile |
| `/dashboard/board` | Board Advisor |
| `/dashboard/graph` | Knowledge Graph Explorer |
| `/dashboard/settings` | Settings |

---

## Environment Variables

Copy `.env.local` and configure:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_PREFIX=/api/v1
```

---

## Stack

- Next.js 15 + React 19
- TypeScript (strict mode)
- TailwindCSS + Shadcn UI
- Framer Motion 11
- React Query v5 (TanStack)
- Zustand 5
- Axios + interceptors (token refresh)
- Recharts + HTML5 Canvas (force-directed graph)
- React Hook Form + Zod
- Sonner (toasts)

---

## Auth Flow

1. User visits `/login` → submits email/password
2. Backend returns `access_token` (30min) + `refresh_token` (7 days)
3. Access token stored in `sessionStorage`, refresh token in `localStorage`
4. Axios interceptor auto-refreshes on 401
5. Protected routes: all `/dashboard/*` routes require authentication
6. Unauthenticated users redirected to `/login`
