insert into stats.member_activity (member_id, display_name, posts_count)
select p.id, p.display_name, (select count(*) from public.posts where author_id = p.id)
from public.profiles p;

-- Alice has read two posts, Bob and Carol one each.
insert into stats.reading_history (member_id, post_id)
select m.id, po.id
from public.profiles m
join public.posts po on (m.display_name, po.title) in (
  ('Alice', 'Malerweg, stage four'),
  ('Alice', 'Three days on the Rennsteig'),
  ('Bob', 'Winter overnighter in the Harz'),
  ('Carol', 'Malerweg, stage four'));
