-- Member stats live in their own schema, away from the app tables.
create schema stats;

-- One row per member, refreshed by a nightly job.
create table stats.member_activity (
  member_id uuid primary key references public.profiles (id) on delete cascade,
  display_name text not null,
  posts_count integer not null default 0,
  updated_at timestamptz not null default now()
);

-- Which posts a member has opened. Private to that member.
create table stats.reading_history (
  id bigint generated always as identity primary key,
  member_id uuid not null references public.profiles (id) on delete cascade,
  post_id bigint not null references public.posts (id) on delete cascade,
  read_at timestamptz not null default now()
);
create index reading_history_member_id_idx on stats.reading_history (member_id);
