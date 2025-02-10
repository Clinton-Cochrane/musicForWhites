import asyncio
import websockets
import sounddevice as sd
import queue
import numpy as np
from deepgram import Deepgram
import json

DEEPGRAM_API_KEY = "fake api key for now"
dg_client = Deepgram(DEEPGRAM_API_KEY)

q = queue.Queue

def audio_callback(indata, frames, time, status):
    q.put(indata.copy())

async def transcribe_audio(websocket):
    while True:
        audio_data = q.get()
        audio_bytes = audio_data.tobytes()

        response = dg_client.transcription.sync_prerecorded(
            audio_bytes, {"punctuate": True}
        )

        words = response["results"]["channels"][0]["alternatives"][0]["words"]
        for word in words:
            if 'nigg' in word["word"].lower():
                await websocket.send(json.dumps({"mute": [word["start"], word["end"]]}))
                

async def websocket_endpoint(websocket):
    print("Client Connected... Listening for audio...")
    asyncio.create_task(transcribe_audio(websocket))

    while True:
        try:
            await websocket.recv()
        except:
            break

async def main():
    async with websockets.serve(websocket_endpoint, "0.0.0.0", 8000):
        print("Websocket server running on ws://localhost:8000")
        await asyncio.Future()

if __name__ == "__main__":
    stream = sd.InputStream(callback=audio_callback, channels=1, samplerate=16000)
    stream.start()
    asyncio.run(main())
