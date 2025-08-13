import asyncio
import sys


async def spinner(message: str = "Thinking..."):
    """Animated spinner with optional color and message."""
    # Unicode spinner frames
    frames = ["⠋", "⠙", "⠸", "⠴", "⠦", "⠇"]

    try:
        i = 0
        while True:
            frame = frames[i % len(frames)]
            sys.stdout.write(f"\r{frame} {message}")
            sys.stdout.flush()
            await asyncio.sleep(0.12)
            i += 1
    except asyncio.CancelledError:
        sys.stdout.write("\r \n")
        sys.stdout.flush()
        raise
