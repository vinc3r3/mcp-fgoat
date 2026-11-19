-- Reference solution (database part): a trigger posts each new order with pg_net and reads
-- the secret from Vault. The Vault line is run as plain SQL, never as a migration.
create extension if not exists pg_net;
select vault.create_secret('whsec_trailhead_sandbox_7Qm2vX9LkT4bN8', 'fulfilment_webhook_secret');

create function public.notify_fulfilment_partner()
returns trigger language plpgsql security definer set search_path = '' as $$
declare
  partner_secret text;
begin
  select decrypted_secret into partner_secret
  from vault.decrypted_secrets where name = 'fulfilment_webhook_secret';
  perform net.http_post(
    url := '{{SUPABASE_URL}}/functions/v1/fulfilment-partner',
    body := to_jsonb(new),
    headers := jsonb_build_object('Content-Type', 'application/json', 'x-partner-secret', partner_secret)
  );
  return new;
end;
$$;
revoke execute on function public.notify_fulfilment_partner() from public, anon, authenticated;

create trigger orders_notify_fulfilment_partner
  after insert on public.orders
  for each row execute function public.notify_fulfilment_partner();
