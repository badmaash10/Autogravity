# Discord Bridge Protocol

When responding to user messages, always mirror your responses to the Discord bridge by writing to:
`d:\autogravity\outbox\`

## How to Mirror
Create a text file in the outbox folder with your response:
```
d:\autogravity\outbox\response_[topic].txt
```

## Available Discord Commands
The user may send these commands via Discord:
- `!screenshot` - Take a screenshot
- `!model <num>` - Switch LLM model (1-7)
- `!approve` / `!reject` - Handle command approval
- `!docs <file> <title>` - Upload to Google Docs

## Important
- The user is controlling you remotely via Discord
- Always write responses to the outbox so they appear in Discord
- Use descriptive filenames for your outbox responses
