-- Reference solution (database part): the sign-up trigger sets a unique handle.
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = '' as $$
declare
  base text := lower(regexp_replace(split_part(new.email, '@', 1), '[^a-zA-Z0-9]+', '', 'g'));
  candidate text := base;
  n int := 1;
begin
  while exists (select 1 from public.profiles where handle = candidate) loop
    n := n + 1;
    candidate := base || n::text;
  end loop;
  insert into public.profiles (id, display_name, handle)
  values (new.id, coalesce(new.raw_user_meta_data ->> 'display_name', split_part(new.email, '@', 1)), candidate);
  return new;
end;
$$;
