-- Reference solution, used only to test the checks.
-- The schema is exposed with a role setting: the server has no tool for the Data API's
-- exposed-schemas list, and this is the only route that stays inside it.
alter role authenticator set pgrst.db_schemas = 'public, graphql_public, stats';

grant usage on schema stats to authenticated;
grant select on stats.member_activity, stats.reading_history to authenticated;

alter table stats.member_activity enable row level security;
alter table stats.reading_history enable row level security;

create policy "Members read the leaderboard" on stats.member_activity
  for select to authenticated using (true);
create policy "Members read their own history" on stats.reading_history
  for select to authenticated using ((select auth.uid()) = member_id);

notify pgrst, 'reload config';
