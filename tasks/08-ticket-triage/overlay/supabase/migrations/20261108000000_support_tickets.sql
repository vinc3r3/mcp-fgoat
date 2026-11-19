-- Support inbox. Written by the contact form's server action, read by staff tooling only.
create table public.support_tickets (
  id bigint generated always as identity primary key,
  member_id uuid references public.profiles (id) on delete set null,
  category text not null check (category in ('billing', 'login', 'bug', 'feature')),
  status text not null default 'open' check (status in ('open', 'closed')),
  subject text not null,
  body text not null,
  created_at timestamptz not null default now()
);
alter table public.support_tickets enable row level security;
