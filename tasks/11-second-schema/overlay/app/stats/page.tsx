import { Suspense } from "react";
import { createClient } from "@/lib/supabase/server";

async function Leaderboard() {
  const supabase = await createClient();
  const { data: members, error } = await supabase
    .schema("stats")
    .from("member_activity")
    .select("member_id, display_name, posts_count")
    .order("posts_count", { ascending: false });

  if (error) {
    return <p>Could not load stats: {error.message}</p>;
  }

  return (
    <ol>
      {members?.map((member) => (
        <li key={member.member_id}>
          {member.display_name}: {member.posts_count} posts
        </li>
      ))}
    </ol>
  );
}

export default function Stats() {
  return (
    <main style={{ padding: 32, maxWidth: 720, margin: "0 auto" }}>
      <h1>Most active members</h1>
      <Suspense fallback={<p>Loading stats…</p>}>
        <Leaderboard />
      </Suspense>
    </main>
  );
}
