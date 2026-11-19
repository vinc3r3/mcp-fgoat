-- Changes "made by hand in the dashboard": present in production, absent from the
-- migration history and from the repo.
alter table public.posts add column pinned boolean not null default false;
update public.posts set pinned = true where title = 'Malerweg, stage four';

create table public.post_reactions (
  post_id bigint not null references public.posts (id) on delete cascade,
  member_id uuid not null references public.profiles (id) on delete cascade,
  emoji text not null,
  created_at timestamptz not null default now(),
  primary key (post_id, member_id, emoji)
);
alter table public.post_reactions enable row level security;
grant select on public.post_reactions to anon, authenticated;
grant insert, delete on public.post_reactions to authenticated;
create policy "Reactions are public" on public.post_reactions for select using (true);
create policy "Members react as themselves" on public.post_reactions
  for insert to authenticated with check ((select auth.uid()) = member_id);
create policy "Members remove their own reactions" on public.post_reactions
  for delete to authenticated using ((select auth.uid()) = member_id);

insert into public.post_reactions (post_id, member_id, emoji)
select p.id, m.id, e.emoji
from (select id from public.posts order by id limit 2) p
cross join (select id from public.profiles where display_name in ('Bob', 'Carol')) m
cross join (values ('🔥')) e (emoji);
