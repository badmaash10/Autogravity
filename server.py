"""
AntiGravity Bridge Server
=========================
A uvicorn-compatible server wrapper for the Discord Bridge.
Run with: uvicorn server:app --reload

This allows hot-reloading during development.
"""

import asyncio
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn

# Import the bridge module
import bridge


# Global references
discord_thread = None
stop_event = None


def run_discord_bot():
    """Run the Discord bot in a separate thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(bridge.bot.start(bridge.DISCORD_TOKEN))
    except Exception as e:
        print(f"[ERROR] Discord bot crashed: {e}")
    finally:
        loop.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events for the FastAPI app."""
    global discord_thread
    
    print("[SERVER] Starting Discord Bridge Server...")
    
    # Start Discord bot in a background thread
    discord_thread = threading.Thread(target=run_discord_bot, daemon=True)
    discord_thread.start()
    print("[SERVER] Discord bot thread started.")
    
    # Start the outbox watcher
    from watchdog.observers import Observer
    handler = bridge.OutboxHandler(bridge.bot, bridge.DISCORD_CHANNEL_ID)
    observer = Observer()
    observer.schedule(handler, str(bridge.OUTBOX_PATH), recursive=False)
    observer.start()
    print("[SERVER] Outbox watcher started.")
    
    yield  # Server is running
    
    # Shutdown
    print("[SERVER] Shutting down...")
    observer.stop()
    observer.join()
    await bridge.bot.close()


app = FastAPI(
    title="AntiGravity Bridge",
    description="Discord <-> IDE Bridge with hot-reload support",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "running",
        "bot_user": str(bridge.bot.user) if bridge.bot.user else "connecting...",
        "channel_id": bridge.DISCORD_CHANNEL_ID,
        "outbox_path": str(bridge.OUTBOX_PATH)
    }


@app.get("/health")
async def health():
    """Health check for monitoring."""
    return {"status": "ok"}


@app.post("/send")
async def send_message(message: str):
    """
    Send a message to Discord via the outbox.
    Useful for testing or programmatic access.
    """
    from pathlib import Path
    from datetime import datetime
    
    filename = f"api_{datetime.now().strftime('%H%M%S')}.txt"
    filepath = bridge.OUTBOX_PATH / filename
    filepath.write_text(message, encoding="utf-8")
    
    return {"status": "queued", "file": filename}


if __name__ == "__main__":
    print("=" * 50)
    print("  AntiGravity Bridge Server")
    print("  Run with: uvicorn server:app --reload")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000)
