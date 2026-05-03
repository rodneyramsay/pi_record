#!/usr/bin/env python3
import subprocess
import os
import signal
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
        "-r", "96000",
        "-b", "32",
        "-L",
        "-d",
        "-t", "wav",
        "-c", "2",
        "-b", "24",
        "-r", "96000",
        "-L",
        output_wav,
    ]

    print(*cmd) 

    # Start sox in its own process group so we can terminate it cleanly.
    proc = subprocess.Popen(cmd, preexec_fn=os.setsid)

    try:
        time.sleep(DURATION_SECONDS)
    except KeyboardInterrupt:
        print()
        print("Recording interrupted; stopping sox and running stats...")
    finally:
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()


    cmd = f'sox "{output_wav}" -p trim 150 | sox -p -n stats'

    print(cmd)
    subprocess.run(cmd, shell=True)


if __name__ == "__main__":
    main()
