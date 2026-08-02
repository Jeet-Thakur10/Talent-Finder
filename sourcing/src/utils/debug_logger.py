import os
import sys

def debug_log(*args, sep=" ", end="\n"):
    message = sep.join(str(arg) for arg in args) + end
    # Write to console exactly as before
    sys.stdout.write(message)
    sys.stdout.flush()
    # Append to logs/debug.txt
    try:
        os.makedirs("logs", exist_ok=True)
        with open("logs/debug.txt", "a", encoding="utf-8") as f:
            f.write(message)
    except Exception:
        pass
