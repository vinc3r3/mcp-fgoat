// Forwards each new order to the fulfilment partner, signed with our shared secret.
// Called by the orders_forward_new_order database trigger.
//
// The secret is a function secret named PARTNER_SECRET. It is never stored in this file.

const PARTNER_URL = `${Deno.env.get("SUPABASE_URL")}/functions/v1/fulfilment-partner`;

Deno.serve(async (req: Request) => {
  const secret = Deno.env.get("PARTNER_SECRET");
  if (!secret) return new Response("PARTNER_SECRET is not set", { status: 500 });

  const order = await req.json();
  const reply = await fetch(PARTNER_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-partner-secret": secret,
      "x-forwarded-by": "notify-partner",
    },
    body: JSON.stringify(order),
  });
  console.log(`order ${order.id}: partner replied ${reply.status}`);
  return new Response(await reply.text(), { status: reply.status });
});
