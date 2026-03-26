# Music Word Filter (MVP)

This project mutes detected lyric windows in browser audio/video tabs using a local websocket pipeline.

## What works now

- Chrome extension popup controls:
  - `Censor N-word` (enabled)
  - `Allow N-word` (disabled)
- Configurable blocklist and allowlist terms.
- Background service worker applies allowlist/blocklist matching before forwarding mute events.
- Content script handles overlapping mute windows without early unmute.
- Python websocket server streams mute windows and matched words when terms are detected.

## Project structure

- `chromeExtension/` - Chrome extension (popup + content + background)
- `server/` - Websocket speech/transcription logic
- `flutterProject/` - Clean Flutter prototype for filter model UI

## Run the server

1. Install dependencies (example):
   - `pip install websockets sounddevice numpy deepgram-sdk`
2. Export your Deepgram API key:
   - `export DEEPGRAM_API_KEY=your_key_here`
3. Optional server-side defaults:
   - `export BLOCKLIST_TERMS="nigg,other_term"`
   - `export ALLOWLIST_TERMS="safe_term"`
   - `export AUDIO_CAPTURE_MODE=pulse-monitor`
   - `export PULSE_MONITOR_SOURCE="alsa_output.pci-0000_01_00.1.hdmi-stereo.monitor"`
   - `export AUDIO_INPUT_DEVICE="pulse monitor device name or index"`
   - `export DEBUG_TRANSCRIPTS=true`
   - `export TRANSCRIBE_SECONDS=4.0`
   - `export OVERLAP_SECONDS=0.75`
   - `export STEP_SECONDS=1.0`
   - `export DEEPGRAM_MODEL=nova-3`
   - `export KEYWORDS="nigg,alright,aight"`
   - `export CHUNK_FALLBACK_MUTE=true`
4. Start server:
   - `python3 server/websocketServer.py`

## Load the Chrome extension

1. Open Chrome -> Extensions -> Developer mode -> Load unpacked.
2. Select the `chromeExtension` folder.
3. Open a supported site tab (YouTube, Spotify web, Pandora).
4. Use the extension popup to switch between:
   - `Censor N-word`
   - `Allow N-word`
5. (Optional) enable `Show debug overlay` to view incoming mute events in-page.
6. (Optional) edit `Blocklist terms` and `Allowlist terms` in popup, then click `Save`.

## Local testing plan

### 1) Environment setup

1. Install Python dependencies:
   - `pip install websockets sounddevice numpy deepgram-sdk`
2. Export env vars:
   - `export DEEPGRAM_API_KEY=your_key_here`
   - `export BLOCKLIST_TERMS="nigg"`
   - `export ALLOWLIST_TERMS=""`
3. Load unpacked extension from `chromeExtension/`.

### 2) Fast automated checks

1. JS syntax:
   - `node --check chromeExtension/background.js`
   - `node --check chromeExtension/content.js`
   - `node --check chromeExtension/popup.js`
2. Python checks:
   - `python3 -m py_compile server/websocketServer.py`
   - `python3 -m unittest server/test_websocket_server.py`

### 3) Extension behavior checks (manual)

1. Set popup toggle to `Censor N-word`.
2. Keep blocklist as `nigg`, allowlist empty.
3. Start server: `python3 server/websocketServer.py`.
4. Play audio in supported tab.
5. Verify mute happens when target word is detected.
6. Change popup to `Allow N-word` and verify mute no longer applies.
7. Add allowlist term that would overlap blocklist and verify allowlist wins.
8. Enable `Show debug overlay` to visually confirm incoming mute windows.

### 3.1) If detection is not firing

1. List available audio devices:
   - `python3 server/list_audio_devices.py`
2. On Linux, choose a monitor/loopback input (often contains `monitor` in the name).
3. Export selected device, then restart server:
   - `export AUDIO_INPUT_DEVICE="exact device name or index"`
   - `export DEBUG_TRANSCRIPTS=true`
   - `python3 server/websocketServer.py`
4. Play music and watch terminal for `Transcript chunk:` lines.
5. If no transcript lines appear, server is not hearing your playback device yet.
6. If rap vocals are missed over instrumentals, increase chunk size and keyword bias:
   - `export TRANSCRIBE_SECONDS=4.0`
   - `export OVERLAP_SECONDS=0.75`
   - `export STEP_SECONDS=1.0`
   - `export DEEPGRAM_MODEL=nova-3`
   - `export KEYWORDS="nigg,alright,aight"`
   - `export CHUNK_FALLBACK_MUTE=true` (mutes whole chunk when transcript text matches)

### 3.2) Direct system capture on Linux (recommended)

1. List monitor sources:
   - `python3 server/list_pulse_monitors.py`
2. Pick a `.monitor` source tied to your active output.
3. Start server in direct-capture mode:
   - `export AUDIO_CAPTURE_MODE=pulse-monitor`
   - `export PULSE_MONITOR_SOURCE="your.monitor.source"`
   - `python3 server/websocketServer.py`
4. Keep music playing and verify `Transcript chunk:` logs are more consistent than mic mode.

### 4) Overlap mute checks

1. Stop the real server if running.
2. Start mock server:
   - `python3 server/mock_websocket_sender.py --scenario overlap --delay 0.2`
3. Keep extension toggle on `Censor N-word`.
4. Open a supported tab with active audio/video element.
5. Verify audio stays muted across the combined overlap window.
6. Confirm it unmutes only after the latest mute deadline.
7. Repeat with toggle `Allow N-word` and verify no mute is applied.

### 5) Deterministic mock scenarios

Use these commands to test repeatable behavior quickly:

- Single mute event:
  - `python3 server/mock_websocket_sender.py --scenario single`
- Overlap mute events:
  - `python3 server/mock_websocket_sender.py --scenario overlap`
- Full sequence:
  - `python3 server/mock_websocket_sender.py --scenario all`

### 6) Flutter prototype checks

1. Open `flutterProject/main.dart` in a Flutter app scaffold.
2. Run app (`flutter run`) and verify:
   - toggle changes label (`Censor N-word` vs `Allow N-word`)
   - blocklist/allowlist update preview result
   - allowlist overrides blocklist in preview

## Notes

- This is still an MVP and can have false positives/negatives depending on transcription quality.
- Device-wide audio interception is platform-specific and not implemented in this version.
