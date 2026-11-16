# AWS Amplify deployment

Connect this GitHub repository to Amplify Hosting, select the Next.js SSR preset, and set
`ARES_AI_ENDPOINT`, optional `ARES_AI_TOKEN`, `AWS_REGION`, and optional `DATA_BUCKET` in the
Amplify console. Server variables must be exposed to the SSR compute runtime (do not use
`NEXT_PUBLIC_*` for secrets). Attach only the required data-access permissions to the SSR
compute IAM role. The default AWS SDK credential chain is used; keys are never committed.
