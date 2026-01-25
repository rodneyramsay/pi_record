#!/usr/bin/env python3
import os
import signal
import subprocess
import sys
import time


DURATION_SECONDS = 35 * 60  # 35 minutes


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <output_file.wav>")
        sys.exit(2)

    output_wav = sys.argv[1]

    # Your command (kept essentially the same, but with output filename inserted)
    cmd = [
        "sox",
        "-c", "2",
        "-r", "48000",
        "-b", "32",
        "-L",
        "-d",
        "-t", "wav",
        "-c", "2",
        "-b", "24",
        "-r", "48000",
        "-L",
        output_wav,
    ]

    # Start sox in its own process group so we can terminate it cleanly.
    proc = subprocess.Popen(cmd, preexec_fn=os.setsid)

    interrupted = False
    try:
        start_time = time.time()
        while True:
            elapsed = time.time() - start_time
            remaining = DURATION_SECONDS - elapsed
            if remaining <= 0:
                break
            time.sleep(min(1.0, remaining))
    except KeyboardInterrupt:
        interrupted = True
    finally:
        # Terminate whole process group (covers child processes too)
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            return

        # Give it a moment to exit cleanly
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()

    if interrupted:
        raise SystemExit(130)


if __name__ == "__main__":
    main()
