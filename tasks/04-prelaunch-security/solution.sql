-- Reference solution (database part).
alter table public.invoices enable row level security;
revoke select on public.invoices from anon;
create policy "Members read their own invoices" on public.invoices
  for select to authenticated using ((select auth.uid()) = customer_id);

alter view public.invoice_totals set (security_invoker = true);
revoke select on public.invoice_totals from anon;

drop policy "Members can read messages" on public.messages;
create policy "Participants read their messages" on public.messages
  for select to authenticated
  using ((select auth.uid()) in (sender_id, recipient_id));

revoke execute on function public.get_contact_email(uuid) from public, anon, authenticated;

alter table public.drafts enable row level security;
