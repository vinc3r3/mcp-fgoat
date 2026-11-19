-- Public @handles for members. Released 18 November.
alter table public.profiles add column handle text;
update public.profiles set handle = lower(display_name);
alter table public.profiles alter column handle set not null;
create unique index profiles_handle_key on public.profiles (handle);
grant update (handle) on public.profiles to authenticated;
