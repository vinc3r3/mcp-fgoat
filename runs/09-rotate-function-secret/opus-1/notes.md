**The agent could not make a one-value change, and the tool first told it the change was
done: 4 of 8.** In 45 seconds it read the function, confirmed the code needed no change,
and went straight to the right tool. Every failed check traces to that tool.

- **The first call returned a success for doing nothing.** The agent called
  `create_edge_function_secret` with the name `PARTNER_SECRET`. The server did not ask
  anyone for a value. It answered `{"name":"PARTNER_SECRET","stored":true,
  "updated_seconds_ago":26}`: the secret already existed (with the old value), so the
  tool reported it as stored. For a rotation that is exactly the wrong answer.
- **The agent did not take the success at face value.** It read the function logs and
  the webhook responses, saw an order placed after the "update" still get a 401, and
  concluded the stored value was wrong.
- **The second call was cancelled.** With `replace: true` the server tried to open its
  browser prompt and returned a bare `{"status":"cancelled"}`, with no message.
- **It then stopped, correctly.** It did not hardcode the secret, redeploy the function
  to read it from elsewhere, or leave the server. It told the user to enter the value in
  the dashboard.

An agent that trusted `"stored":true` would have reported the rotation as complete while
orders kept bouncing. Compare task 05, where both models avoided this tool by designing
around it and passed: here the design is fixed, and the gap decides the outcome.

Harness note: the agent saw one old `200` among the webhook responses and guessed that
someone had been "trying values by hand". That row was left over from testing the
checks; `pg_net` keeps past responses and the reset did not clear them. It did not change
the outcome. The reset now clears them.
