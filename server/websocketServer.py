import asyncio
import websockets
import sounddevice as sd
import queue
import numpy as np
import io
import wave
import subprocess
import threading
from deepgram import DeepgramClient
import json
import os
from filtering import should_mute_word

SAMPLE_RATE = 16000
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
dg_client = DeepgramClient(api_key=DEEPGRAM_API_KEY)
BLOCKLIST_TERMS = [
    term.strip().lower()
    for term in os.getenv("BLOCKLIST_TERMS", "nigg").split(",")
    if term.strip()
]
ALLOWLIST_TERMS = [
    term.strip().lower()
    for term in os.getenv("ALLOWLIST_TERMS", "").split(",")
    if term.strip()
]
DEBUG_TRANSCRIPTS = os.getenv("DEBUG_TRANSCRIPTS", "false").lower() == "true"
AUDIO_INPUT_DEVICE = os.getenv("AUDIO_INPUT_DEVICE")
TRANSCRIBE_SECONDS = float(os.getenv("TRANSCRIBE_SECONDS", "4.0"))
OVERLAP_SECONDS = float(os.getenv("OVERLAP_SECONDS", "0.75"))
STEP_SECONDS_ENV = os.getenv("STEP_SECONDS")
if STEP_SECONDS_ENV is not None:
    STEP_SECONDS = float(STEP_SECONDS_ENV)
else:
    # Backward-compatible default derived from overlap settings.
    STEP_SECONDS = max(0.25, TRANSCRIBE_SECONDS - OVERLAP_SECONDS)
DEEPGRAM_MODEL = os.getenv("DEEPGRAM_MODEL", "nova-3")
CAPTURE_MODE = os.getenv("AUDIO_CAPTURE_MODE", "sounddevice").strip().lower()
PULSE_MONITOR_SOURCE = os.getenv("PULSE_MONITOR_SOURCE", "").strip()
KEYWORDS = [
    term.strip().lower()
    for term in os.getenv("KEYWORDS", "").split(",")
    if term.strip()
]
CHUNK_FALLBACK_MUTE = os.getenv("CHUNK_FALLBACK_MUTE", "true").lower() == "true"
DEDUPE_SECONDS = float(os.getenv("DEDUPE_SECONDS", "1.25"))

q = queue.Queue()

def transcribe_chunk(audio_float32):
    # Convert sounddevice float32 samples into 16-bit PCM.
    audio_int16 = np.clip(audio_float32, -1.0, 1.0)
    audio_int16 = (audio_int16 * 32767).astype(np.int16)

    # Build an in-memory WAV so Deepgram can infer audio metadata reliably.
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)  # int16
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(audio_int16.tobytes())
    wav_bytes = wav_buffer.getvalue()

    request_kwargs = {
        "request": wav_bytes,
        "punctuate": True,
        "model": DEEPGRAM_MODEL,
    }
    if KEYWORDS:
        # Nova-3 uses keyterm, while older models support keywords.
        if DEEPGRAM_MODEL.startswith("nova-3"):
            request_kwargs["keyterm"] = KEYWORDS
        else:
            request_kwargs["keywords"] = KEYWORDS

    response = dg_client.listen.v1.media.transcribe_file(**request_kwargs)
    if hasattr(response, "to_dict"):
        response_dict = response.to_dict()
    elif hasattr(response, "model_dump"):
        response_dict = response.model_dump()
    else:
        response_dict = dict(response)
    alternative = response_dict["results"]["channels"][0]["alternatives"][0]
    words = alternative.get("words", [])
    transcript_text = alternative.get("transcript", "")
    return words, transcript_text


def audio_callback(indata, frames, time, status):
    q.put(indata.copy())


def start_pulse_monitor_capture():
    command = [
        "parec",
        "--raw",
        "--format=s16le",
        "--rate=16000",
        "--channels=1",
    ]
    if PULSE_MONITOR_SOURCE:
        command.extend(["--device", PULSE_MONITOR_SOURCE])

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0,
    )

    def reader_loop():
        bytes_per_sample = 2
        chunk_samples = 4096
        chunk_bytes = chunk_samples * bytes_per_sample

        while True:
            raw_chunk = process.stdout.read(chunk_bytes)
            if not raw_chunk:
                break

            audio_int16 = np.frombuffer(raw_chunk, dtype=np.int16)
            if audio_int16.size == 0:
                continue
            audio_float32 = (audio_int16.astype(np.float32) / 32767.0).reshape(-1, 1)
            q.put(audio_float32)

    reader_thread = threading.Thread(target=reader_loop, daemon=True)
    reader_thread.start()
    return process


async def transcribe_audio(websocket):
    target_samples = int(SAMPLE_RATE * TRANSCRIBE_SECONDS)
    step_samples = max(1, int(SAMPLE_RATE * STEP_SECONDS))
    rolling_audio = np.array([], dtype=np.float32)
    samples_since_last_inference = 0
    last_sent_at_by_word = {}

    while True:
        audio_data = await asyncio.to_thread(q.get)
        mono_data = np.squeeze(audio_data)
        if mono_data.ndim == 0:
            mono_data = np.array([mono_data], dtype=np.float32)
        mono_data = mono_data.astype(np.float32)
        rolling_audio = np.concatenate([rolling_audio, mono_data], axis=0)
        samples_since_last_inference += mono_data.shape[0]

        max_buffer_samples = max(target_samples * 2, target_samples + step_samples)
        if rolling_audio.shape[0] > max_buffer_samples:
            rolling_audio = rolling_audio[-max_buffer_samples:]

        if rolling_audio.shape[0] < target_samples:
            continue
        if samples_since_last_inference < step_samples:
            continue

        buffered_audio = rolling_audio[-target_samples:]
        samples_since_last_inference = 0

        try:
            words, transcript_text = await asyncio.to_thread(transcribe_chunk, buffered_audio)
        except Exception as exc:
            if DEBUG_TRANSCRIPTS:
                print(f"Transcription error: {exc}")
            continue

        if DEBUG_TRANSCRIPTS and words:
            transcript_preview = " ".join(word.get("word", "") for word in words[:16])
            print(f"Transcript chunk: {transcript_preview}")
        elif DEBUG_TRANSCRIPTS and transcript_text:
            print(f"Transcript text: {transcript_text}")
        elif DEBUG_TRANSCRIPTS:
            print("Transcript chunk: <no words>")

        matched_any_word = False
        now_monotonic = asyncio.get_event_loop().time()
        for word in words:
            raw_word = word.get("word", "")
            if should_mute_word(
                raw_word,
                blocklist_terms=BLOCKLIST_TERMS,
                allowlist_terms=ALLOWLIST_TERMS,
            ):
                normalized_word = raw_word.lower().strip()
                last_sent_at = last_sent_at_by_word.get(normalized_word, 0.0)
                if now_monotonic - last_sent_at < DEDUPE_SECONDS:
                    continue
                last_sent_at_by_word[normalized_word] = now_monotonic
                matched_any_word = True
                if DEBUG_TRANSCRIPTS:
                    print(f"Matched blocked word: {raw_word}")
                await websocket.send(
                    json.dumps(
                        {
                            "mute": [word["start"], word["end"]],
                            "word": raw_word
                        }
                    )
                )

        if not matched_any_word and CHUNK_FALLBACK_MUTE and transcript_text:
            if should_mute_word(
                transcript_text,
                blocklist_terms=BLOCKLIST_TERMS,
                allowlist_terms=ALLOWLIST_TERMS,
            ):
                if DEBUG_TRANSCRIPTS:
                    print("Fallback chunk mute from transcript text match.")
                await websocket.send(
                    json.dumps(
                        {
                            "mute": [0, TRANSCRIBE_SECONDS],
                            "word": transcript_text
                        }
                    )
                )


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
    if not DEEPGRAM_API_KEY:
        raise RuntimeError("Missing DEEPGRAM_API_KEY environment variable.")
    stream = None
    pulse_process = None

    if CAPTURE_MODE == "pulse-monitor":
        print("Capture mode: pulse-monitor (direct system output capture).")
        if PULSE_MONITOR_SOURCE:
            print(f"Using pulse monitor source: {PULSE_MONITOR_SOURCE}")
        else:
            print("Using default pulse monitor source from parec.")
        pulse_process = start_pulse_monitor_capture()
    else:
        if AUDIO_INPUT_DEVICE:
            stripped_device = AUDIO_INPUT_DEVICE.strip()
            selected_device = int(stripped_device) if stripped_device.isdigit() else stripped_device
        else:
            selected_device = None
        print("Capture mode: sounddevice (input device).")
        if selected_device:
            print(f"Using audio input device: {selected_device}")
        else:
            print("Using default audio input device.")
        stream = sd.InputStream(
            callback=audio_callback,
            channels=1,
            samplerate=SAMPLE_RATE,
            device=selected_device,
        )
        stream.start()

    if DEBUG_TRANSCRIPTS:
        print("Debug transcripts enabled.")
        print(f"Deepgram model: {DEEPGRAM_MODEL}")
        if KEYWORDS:
            print(f"Keyword bias enabled: {', '.join(KEYWORDS)}")
        print(f"Chunk fallback mute enabled: {CHUNK_FALLBACK_MUTE}")
        print(f"Transcribe window seconds: {TRANSCRIBE_SECONDS}")
        print(f"Transcribe step seconds: {STEP_SECONDS}")
        print(f"Dedupe seconds: {DEDUPE_SECONDS}")
    try:
        asyncio.run(main())
    finally:
        if stream is not None:
            stream.stop()
            stream.close()
        if pulse_process is not None:
            pulse_process.terminate()
