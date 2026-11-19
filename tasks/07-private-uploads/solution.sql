-- Reference solution (database part).
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('tracks', 'tracks', false, 5242880, array['application/gpx+xml']);

create policy "Members download tracks" on storage.objects
  for select to authenticated using (bucket_id = 'tracks');
create policy "Members upload into their own folder" on storage.objects
  for insert to authenticated
  with check (bucket_id = 'tracks' and (storage.foldername(name))[1] = (select auth.uid())::text);
create policy "Uploaders replace their own tracks" on storage.objects
  for update to authenticated
  using (bucket_id = 'tracks' and owner_id = (select auth.uid())::text)
  with check (bucket_id = 'tracks' and (storage.foldername(name))[1] = (select auth.uid())::text);
create policy "Uploaders delete their own tracks" on storage.objects
  for delete to authenticated
  using (bucket_id = 'tracks' and owner_id = (select auth.uid())::text);
