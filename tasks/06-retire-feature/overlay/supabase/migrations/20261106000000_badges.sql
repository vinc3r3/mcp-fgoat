-- Achievement badges (launched early November, since retired).
create table public.badges (
  id bigint generated always as identity primary key,
  name text not null unique,
  description text not null
);
create table public.member_badges (
  member_id uuid not null references public.profiles (id) on delete cascade,
  badge_id bigint not null references public.badges (id) on delete cascade,
  awarded_at timestamptz not null default now(),
  primary key (member_id, badge_id)
);
create index member_badges_badge_id_idx on public.member_badges (badge_id);
alter table public.badges enable row level security;
alter table public.member_badges enable row level security;
grant select on public.badges, public.member_badges to anon, authenticated;
create policy "Badges are public" on public.badges for select using (true);
create policy "Awarded badges are public" on public.member_badges for select using (true);
