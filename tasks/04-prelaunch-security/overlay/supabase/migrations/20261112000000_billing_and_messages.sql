-- Paid memberships and direct messages.

create table public.invoices (
  id bigint generated always as identity primary key,
  customer_id uuid not null references public.profiles (id) on delete cascade,
  description text not null,
  amount_cents integer not null,
  issued_at timestamptz not null default now()
);
create index invoices_customer_id_idx on public.invoices (customer_id);
grant select on public.invoices to anon, authenticated;

create view public.invoice_totals as
  select customer_id, count(*) as invoices, sum(amount_cents) as total_cents
  from public.invoices group by customer_id;
grant select on public.invoice_totals to anon, authenticated;

create table public.messages (
  id bigint generated always as identity primary key,
  sender_id uuid not null references public.profiles (id) on delete cascade,
  recipient_id uuid not null references public.profiles (id) on delete cascade,
  body text not null,
  sent_at timestamptz not null default now()
);
create index messages_sender_id_idx on public.messages (sender_id);
create index messages_recipient_id_idx on public.messages (recipient_id);
alter table public.messages enable row level security;
grant select, insert on public.messages to authenticated;
create policy "Members can read messages" on public.messages
  for select to authenticated using (true);
create policy "Members send as themselves" on public.messages
  for insert to authenticated with check ((select auth.uid()) = sender_id);

-- Used by the notification emailer to look up where to send.
create function public.get_contact_email(member_id uuid)
returns text language sql security definer set search_path = '' as $$
  select email from auth.users where id = member_id;
$$;

-- Unpublished posts. Only ever touched by a background job, never through the API.
create table public.drafts (
  id bigint generated always as identity primary key,
  author_id uuid not null references public.profiles (id) on delete cascade,
  body text not null,
  updated_at timestamptz not null default now()
);
create index drafts_author_id_idx on public.drafts (author_id);
