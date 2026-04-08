# AI SEO Frontend

React + Vite frontend for the AI SEO System. Provides a **Customer Portal** and **Admin Dashboard** backed by a FastAPI service.

## Folder Structure

```
src/
├── components/
│   ├── ui/             # Reusable primitives (Button, Input, Card, Badge, …)
│   ├── customer/       # Customer-facing components
│   │   ├── SiteRegistrationForm.jsx
│   │   └── SnippetResult.jsx
│   └── admin/          # Admin dashboard components
│       ├── SitesTable.jsx
│       └── StatsBar.jsx
├── hooks/
│   └── useAsync.js     # useAsync + usePolling hooks
├── pages/
│   ├── CustomerPage.jsx
│   └── AdminPage.jsx
├── services/
│   └── api.js          # All API calls (customerApi + adminApi)
├── App.jsx             # Root with tab navigation
├── main.jsx
└── index.css           # Global design system
```

## Quick Start

```bash
cp .env.example .env     # set VITE_API_BASE_URL to your FastAPI URL
npm install
npm run dev              # http://localhost:3000
```

## API Contract

### Customer
| Method | Path | Body / Params |
|--------|------|---------------|
| POST | `/api/sites/register` | `{ site_id, domain }` |
| GET  | `/api/sites/:id/snippet` | — |
| GET  | `/api/sites/:id/jsonld-status` | — |

### Admin
| Method | Path | Notes |
|--------|------|-------|
| GET  | `/api/admin/sites` | Returns `{ sites: Site[] }` |
| GET  | `/api/admin/sites/:id/sync` | Sync status |
| POST | `/api/admin/sites/:id/sync` | Trigger sync |
| POST | `/api/admin/sync-all` | Trigger all |

### Site shape
```ts
{
  site_id: string
  domain: string
  sync_status: "synced" | "pending" | "syncing" | "error"
  last_synced: string | null  // ISO datetime
  jsonld_active: boolean
}
```

## Extending

- **Add a new customer step**: create a component in `src/components/customer/`, wire it through `CustomerPage.jsx`
- **Add an admin panel section**: add a component in `src/components/admin/`, import in `AdminPage.jsx`
- **Add an API call**: add a function to `src/services/api.js` (customerApi or adminApi)
- **Add polling**: use `usePolling(fn, intervalMs)` from `src/hooks/useAsync.js`
