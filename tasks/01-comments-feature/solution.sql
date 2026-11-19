-- Reference solution (database part). Used to confirm the checks pass on a correct result.
create table public.comments (
  id bigint generated always as identity primary key,
  post_id bigint not null references public.posts (id) on delete cascade,
  author_id uuid not null default auth.uid() references public.profiles (id) on delete cascade,
  body text not null check (length(body) between 1 and 2000),
  created_at timestamptz not null default now()
);
create index comments_post_id_idx on public.comments (post_id);
create index comments_author_id_idx on public.comments (author_id);
alter table public.comments enable row level security;
grant select on public.comments to anon, authenticated;
grant insert, delete on public.comments to authenticated;
create policy "Comments are public" on public.comments for select using (true);
create policy "Members comment as themselves" on public.comments
  for insert to authenticated with check ((select auth.uid()) = author_id);
create policy "Members delete their own comments" on public.comments
  for delete to authenticated using ((select auth.uid()) = author_id);
