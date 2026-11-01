# Local Neural Voice Output (Windows)

Nazi AI can optionally use the Piper command-line engine to synthesize a companion's replies into WAV audio. The adapter is local-only: it launches the Piper executable on the same computer, loads a model from disk, and does not call a hosted TTS API or download model files.

## 1. Install Piper

Activate the backend virtual environment and install the optional package:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-voice.txt
```

Confirm that the `piper` command is available in the same terminal:

```powershell
piper --help
```

If the executable is not on PATH, set `VOICE_TTS_EXECUTABLE` in `backend/.env` to its full executable path.

## 2. Install a compatible voice model

Place the complete Piper ONNX voice files in:

```text
backend/models/piper-voices/
```

Each voice needs both files, for example:

```text
your_voice.onnx
your_voice.onnx.json
```

Use only a voice model compatible with the installed Piper version. Check the model's language, quality tier, license, and redistribution terms before using it. Persian language support depends on the specific model available; this project does not bundle or claim a particular Persian voice.

Model weights are excluded from Git. The application only scans this local folder and never downloads voices automatically.

## 3. Optional configuration

Add to `backend/.env` if needed:

```dotenv
VOICE_TTS_EXECUTABLE=piper
VOICE_TTS_MODEL_DIR=./models/piper-voices
VOICE_TTS_TIMEOUT_SECONDS=90
```

Restart FastAPI after changing settings or adding models.

## 4. Select a voice for each character

Open the character creator or editor. Under Personality Studio, choose a voice in **صدای اختصاصی محلی**. The selection is stored inside that character's existing personality configuration in SQLite.

In chat, use **♫ صدای اختصاصی** under an assistant message. If automatic voice playback is enabled and the character has a local voice selected, Nazi AI prefers the local Piper voice. Otherwise it falls back to the browser's speech synthesis.

## 5. Verify local voice availability

Open:

- `http://127.0.0.1:8000/api/voice/tts/voices`

The endpoint lists only complete local ONNX + JSON voice pairs. It returns an empty list when no compatible model is present.

## Privacy and limitations

- Synthesis runs locally through the Piper executable.
- Text is sent only to the local FastAPI service for synthesis.
- The generated WAV is temporary and deleted after the response is sent.
- Voice models are not included in Git and are not downloaded by the application.
- TTS is optional. Browser speech remains available as a fallback.
- Chat completion may still use a separately configured remote AI API; local TTS does not make remote chat inference local.
- Voice model quality, language coverage, and license depend on the model you install.
