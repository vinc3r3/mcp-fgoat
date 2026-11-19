-- Gear shop orders, forwarded to the fulfilment partner by the notify-partner edge function.
create extension if not exists pg_net;

create table public.orders (
  id bigint generated always as identity primary key,
  member_id uuid not null references public.profiles (id) on delete cascade,
  item text not null,
  quantity integer not null default 1 check (quantity > 0),
  created_at timestamptz not null default now()
);
create index orders_member_id_idx on public.orders (member_id);
alter table public.orders enable row level security;
grant select, insert on public.orders to authenticated;
create policy "Members read their own orders" on public.orders
  for select to authenticated using ((select auth.uid()) = member_id);
create policy "Members place their own orders" on public.orders
  for insert to authenticated with check ((select auth.uid()) = member_id);

-- Per-environment settings, filled in outside migrations (URLs differ per project).
create table public.integration_settings (
  key text primary key,
  value text not null
);
alter table public.integration_settings enable row level security;

-- Every new order is posted to the notify-partner edge function, which signs it with
-- the shared secret and passes it on to the partner.
create function public.forward_new_order()
returns trigger language plpgsql security definer set search_path = '' as $$
declare
  target text;
begin
  select value into target from public.integration_settings where key = 'notify_partner_url';
  if target is not null then
    perform net.http_post(
      url := target,
      body := to_jsonb(new),
      headers := jsonb_build_object('Content-Type', 'application/json')
    );
  end if;
  return new;
end;
$$;
revoke execute on function public.forward_new_order() from public, anon, authenticated;

create trigger orders_forward_new_order
  after insert on public.orders
  for each row execute function public.forward_new_order();
