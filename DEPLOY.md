# Amplify deployment

Connect this GitHub repository to Amplify Hosting and select the Next.js SSR preset. Add
`GOOGLE_AI_API_KEY` and, optionally, `GOOGLE_AI_MODEL` in the Amplify environment variables.
Server variables must be exposed to the SSR runtime; never use `NEXT_PUBLIC_*` for secrets.
The API key is used only by `/api/ask` and is never sent to the browser.
The `amplify.yml` build step copies only these server variables into `.env.production`, which
is required for Next.js SSR to read Amplify environment variables at runtime.

Before deploying, create the key in Google AI Studio and restrict it where possible.
If a key has been shared in a screenshot, chat, commit, or log, revoke it and create
a replacement before adding the replacement to Amplify.
