# Discord Bridge - Remote Control

The user controls you remotely via Discord. Focus on executing their requests.

## Available Commands (sent via Discord)
- `!screenshot` - Shows current screen in Discord
- `!windows` - List open windows
- `!max` / `!min` / `!focus` - Window control
- `!project` - Open a project
- `!model <num>` - Switch LLM model
- `!approve` / `!reject` - Handle command approval

## How It Works
1. User sends message via Discord → Message pasted to your chat
2. You respond in chat as normal
3. User uses `!screenshot` to see your response if needed

## Important
- Do NOT manually create response files in outbox
- Focus on the actual task, not mirroring
- The outbox is only for the bridge system, not for you to write to
