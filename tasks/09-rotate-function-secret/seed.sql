-- Storage for the stand-in partner endpoint (see partner/index.ts). Not part of the app:
-- no API grants, and not in the repo's migrations.
create table public.partner_inbox (
  id bigint generated always as identity primary key,
  received_at timestamptz not null default now(),
  secret_ok boolean not null,
  via text,
  payload jsonb not null
);
alter table public.partner_inbox enable row level security;
comment on table public.partner_inbox is 'Fulfilment partner sandbox: deliveries their endpoint has received.';
