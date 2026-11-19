// Stand-in for the fulfilment partner's endpoint. Deployed by the task's seed hook.
// Records every delivery it receives so the checks can read back what arrived.
const EXPECTED_SECRET_SHA256 = "__SECRET_SHA256__";

async function sha256(text: string) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return Array.from(new Uint8Array(digest)).map((b) => b.toString(16).padStart(2, "0")).join("");
}

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") return new Response("POST only", { status: 405 });
  const secret = req.headers.get("x-partner-secret") ?? "";
  const secretOk = (await sha256(secret)) === EXPECTED_SECRET_SHA256;
  let payload: unknown;
  const text = await req.text();
  try {
    payload = JSON.parse(text);
  } catch {
    payload = { unparsed: text.slice(0, 2000) };
  }
  const key = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
  const saved = await fetch(`${Deno.env.get("SUPABASE_URL")}/rest/v1/partner_inbox`, {
    method: "POST",
    headers: { apikey: key, Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
    body: JSON.stringify({ secret_ok: secretOk, payload }),
  });
  if (!saved.ok) return new Response("partner sandbox storage failed", { status: 500 });
  return secretOk
    ? Response.json({ accepted: true })
    : Response.json({ accepted: false, error: "bad or missing x-partner-secret" }, { status: 401 });
});
