# AntiGravity Discord Bridge

A bridge that connects Discord to the AntiGravity Agent running in your AntiGravity IDE.

## How It Works

```
┌────────────┐     paste      ┌─────────────┐
│  Discord   │ ────────────▶  │  IDE Chat   │
│  Message   │  (pyautogui)   │  (Agent)    │
└────────────┘                └─────────────┘
                                    │
                                    │ writes file
                                    ▼
┌────────────┐    watchdog    ┌─────────────┐
│  Discord   │ ◀────────────  │  /outbox/   │
│  Channel   │   sends file   │  folder     │
└────────────┘                └─────────────┘
```

## Setup

### 1. Install Dependencies
```bash
cd d:\autogravity
pip install -r requirements.txt
```

### 2. Create a Discord Bot
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to "Bot" section → Add Bot
4. Enable **Message Content Intent** under Privileged Gateway Intents
5. Copy the Bot Token

### 3. Invite the Bot to Your Server
1. Go to OAuth2 → URL Generator
2. Select scopes: `bot`
3. Select permissions: `Send Messages`, `Read Message History`, `Add Reactions`, `Attach Files`
4. Copy the generated URL and open it in your browser
5. Select your server and authorize

### 4. Get Channel ID
1. Enable Developer Mode in Discord (User Settings → Advanced → Developer Mode)
2. Right-click the channel you want to use → Copy ID

### 5. Configure
1. Copy `.env.example` to `.env`
2. Fill in your secrets in `.env`:
   ```ini
   DISCORD_TOKEN=your_token
   DISCORD_CHANNEL_ID=your_channel_id
   ```

### 6. Calibrate
Running the calibration tools ensures the bot can see your screen correctly.

**Chat Input Calibration:**
```bash
python bridge.py --calibrate
```

**Approval Dialog Calibration:**
```bash
python bridge.py --calibrate-approval
```

## Running

It is recommended to run the bridge using the hot-reload server:

```bash
uvicorn server:app --reload
```
*Port 8000 will be open for API access.*

Alternatively, run the standalone script:
```bash
python bridge.py
```

## Usage

1. **Send a message** in the configured Discord channel
2. The bridge will **paste it** into the IDE chat
3. The Agent will respond by writing to `outbox/`
4. The bridge will **send the response** back to Discord

### Commands
- `!screenshot` - Take a screenshot of the desktop and send it
- `!approve` / `!yes` - Approve a pending CLI command
- `!reject` / `!no` - Reject a pending CLI command
- `!status` - Check bridge status
- `!ping` - Simple ping test

## Remote Command Approval
When the agent needs to run a potentially dangerous command, it may ask for approval. The bridge watches for approval dialogs and will send a screenshot to Discord. Reply with `!approve` to click the approve button remotely.

