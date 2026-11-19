-- Short, shareable addresses for posts.
alter table public.posts add column slug text;
create unique index posts_slug_key on public.posts (slug);
