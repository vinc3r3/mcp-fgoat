# Trailhead

A small community site for trip reports. Next.js (App Router) with Supabase for the
database and sign-in.

- `app/` pages. The home page lists posts; `/login` signs a member in.
- `lib/supabase/` Supabase clients for server and browser code.
- `supabase/migrations/` every schema change, in order. Production is built from these.
- `.env.local` project URL and publishable key for the hosted project.

```bash
npm install
npm run dev
```

Test accounts on the hosted project: `alice@example.com`, `bob@example.com` and
`carol@example.com`, all with the password `trailhead-test-1`.
