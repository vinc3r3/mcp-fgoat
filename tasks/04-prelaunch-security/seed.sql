insert into public.invoices (customer_id, description, amount_cents)
select id, d.description, d.amount_cents from public.profiles
cross join (values ('Trailhead Plus, October', 900), ('Trailhead Plus, November', 900)) d (description, amount_cents)
where display_name in ('Alice', 'Bob');

insert into public.messages (sender_id, recipient_id, body)
select a.id, c.id, 'Want to do the Harz loop in January? Keep it between us for now.'
from public.profiles a, public.profiles c where a.display_name = 'Alice' and c.display_name = 'Carol';
insert into public.messages (sender_id, recipient_id, body)
select c.id, a.id, 'Yes. I will bring the stove this time.'
from public.profiles a, public.profiles c where a.display_name = 'Alice' and c.display_name = 'Carol';

insert into public.drafts (author_id, body)
select id, 'Notes for a post about the Kammweg' from public.profiles where display_name = 'Bob';
