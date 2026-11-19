-- This project predates Supabase's change to API access for new tables. Its original
-- tables were granted to the API roles automatically when they were created, so no
-- migration in the repo mentions those grants. Tables created today get none.
grant select on public.profiles to anon, authenticated;
grant update (display_name) on public.profiles to authenticated;
grant select on public.posts to anon, authenticated;
grant insert, update, delete on public.posts to authenticated;
