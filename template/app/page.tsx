import { Suspense } from "react";
import { createClient } from "@/lib/supabase/server";

async function Account() {
  const supabase = await createClient();
  const { data } = await supabase.auth.getUser();
  return data.user ? <p>Signed in as {data.user.email}</p> : <p><a href="/login">Sign in</a></p>;
}

async function Posts() {
  const supabase = await createClient();
  const { data: posts, error } = await supabase
    .from("posts")
    .select("id, title, body, created_at, profiles(display_name)")
    .order("created_at", { ascending: false });

  if (error) {
    return <p>Could not load posts: {error.message}</p>;
  }

  return (
    <>
      {posts?.map((post) => (
        <article key={post.id} style={{ margin: "24px 0" }}>
          <h2>{post.title}</h2>
          <small>
            {(post.profiles as unknown as { display_name: string } | null)?.display_name ?? "Unknown"} ·{" "}
            {new Date(post.created_at).toLocaleDateString("en-GB")}
          </small>
          <p>{post.body}</p>
        </article>
      ))}
    </>
  );
}

export default function Home() {
  return (
    <main style={{ padding: 32, maxWidth: 720, margin: "0 auto" }}>
      <h1>Trailhead</h1>
      <p>Trip reports from the community.</p>
      <Suspense fallback={null}>
        <Account />
      </Suspense>
      <Suspense fallback={<p>Loading posts…</p>}>
        <Posts />
      </Suspense>
    </main>
  );
}
