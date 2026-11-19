-- Profiles: one row per signed-up user, created by a trigger on auth.users.
create table public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  display_name text not null,
  created_at timestamptz not null default now()
);

-- Posts: public trip reports.
create table public.posts (
  id bigint generated always as identity primary key,
  author_id uuid not null references public.profiles (id) on delete cascade,
  title text not null,
  body text not null,
  created_at timestamptz not null default now()
);
create index posts_author_id_idx on public.posts (author_id);

alter table public.profiles enable row level security;
alter table public.posts enable row level security;

grant select on public.profiles to anon, authenticated;
grant update (display_name) on public.profiles to authenticated;
grant select on public.posts to anon, authenticated;
grant insert, update, delete on public.posts to authenticated;

create policy "Profiles are public" on public.profiles
  for select using (true);
create policy "Users edit their own profile" on public.profiles
  for update to authenticated
  using ((select auth.uid()) = id) with check ((select auth.uid()) = id);

create policy "Posts are public" on public.posts
  for select using (true);
create policy "Authors insert their own posts" on public.posts
  for insert to authenticated with check ((select auth.uid()) = author_id);
create policy "Authors update their own posts" on public.posts
  for update to authenticated
  using ((select auth.uid()) = author_id) with check ((select auth.uid()) = author_id);
create policy "Authors delete their own posts" on public.posts
  for delete to authenticated using ((select auth.uid()) = author_id);

-- Create a profile whenever someone signs up.
create function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
  insert into public.profiles (id, display_name)
  values (new.id, coalesce(new.raw_user_meta_data ->> 'display_name', split_part(new.email, '@', 1)));
  return new;
end;
$$;
revoke execute on function public.handle_new_user() from public, anon, authenticated;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();
