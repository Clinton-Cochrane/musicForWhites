import subprocess


def main():
    result = subprocess.run(
        ["pactl", "list", "short", "sources"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print("Failed to query pulse sources. Is PulseAudio/PipeWire available?")
        print(result.stderr.strip())
        return

    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    monitor_lines = [line for line in lines if ".monitor" in line]
    if not monitor_lines:
        print("No monitor sources found.")
        print("All sources:")
        for line in lines:
            print(line)
        return

    print("Monitor sources:")
    for line in monitor_lines:
        print(line)


if __name__ == "__main__":
    main()
