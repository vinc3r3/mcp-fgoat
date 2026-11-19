insert into public.badges (name, description) values
  ('First report', 'Posted a first trip report'),
  ('Winter camper', 'Posted a report from a night below zero'),
  ('Regular', 'Posted in three different months');
insert into public.member_badges (member_id, badge_id)
select p.id, b.id from public.profiles p cross join public.badges b
where p.display_name in ('Alice', 'Bob') and b.name in ('First report', 'Winter camper');
