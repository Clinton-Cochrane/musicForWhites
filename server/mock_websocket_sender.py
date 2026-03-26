import argparse
import asyncio
import json

import websockets


DEFAULT_EVENTS = [
    # A single mute event.
    {"mute": [0.0, 0.8], "word": "nigga"},
    # Two overlapping events to validate no early unmute.
    {"mute": [0.0, 1.2], "word": "nigger"},
    {"mute": [0.0, 1.5], "word": "nigga"},
]


async def stream_events_to_client(websocket, events, delay_seconds):
    print("Extension connected. Sending mock events...")
    for index, event in enumerate(events, start=1):
        await websocket.send(json.dumps(event))
        print(f"[{index}/{len(events)}] Sent: {event}")
        await asyncio.sleep(delay_seconds)
    print("Done sending mock events.")
    await websocket.wait_closed()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Send deterministic mock mute events to the extension websocket."
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind websocket mock server.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind websocket mock server.",
    )
    parser.add_argument(
        "--scenario",
        choices=["single", "overlap", "all"],
        default="all",
        help="Mock scenario to run.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.3,
        help="Delay between sent events in seconds.",
    )
    return parser.parse_args()


def scenario_events(name):
    if name == "single":
        return [DEFAULT_EVENTS[0]]
    if name == "overlap":
        return [DEFAULT_EVENTS[1], DEFAULT_EVENTS[2]]
    return DEFAULT_EVENTS


def main():
    args = parse_args()
    events = scenario_events(args.scenario)

    async def run():
        async def handler(websocket):
            await stream_events_to_client(websocket, events, args.delay)

        async with websockets.serve(handler, args.host, args.port):
            print(f"Mock websocket server running on ws://{args.host}:{args.port}")
            await asyncio.Future()

    asyncio.run(run())


if __name__ == "__main__":
    main()
