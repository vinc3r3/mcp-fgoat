-- Gear shop orders.
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
