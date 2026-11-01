# Local Voice Setup (Windows)

Nazi AI's local speech-to-text endpoint uses faster-whisper. Audio is posted to the local FastAPI process and transcribed on the same computer. The runtime does not download model files and does not call a hosted transcription API.

## 1. Install the optional package

Activate the backend virtual environment, then run:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-voice.txt
```

## 2. Place a compatible model on disk

Download the model repository `Systran/faster-whisper-small` separately, then copy its complete model snapshot into:

```text
backend/models/faster-whisper-small/
```

The directory should contain the CTranslate2 model files such as `model.bin`, `config.json`, tokenizer files, and vocabulary files. Do not put only a model card or a Git LFS pointer file in this directory.

The model weights are intentionally excluded from Git. The application loads this directory with `local_files_only=True` and does not attempt a download.

## 3. Optional settings

Add these entries to `backend/.env` if you want to override defaults:

```dotenv
VOICE_STT_MODEL_PATH=./models/faster-whisper-small
VOICE_STT_DEVICE=cpu
VOICE_STT_COMPUTE_TYPE=int8
```

The default configuration uses CPU and int8 quantization to be more suitable for ordinary Windows laptops. A supported GPU can be configured later after checking its CUDA/cuDNN compatibility.

## 4. Start and check

Restart the backend, then open:

- `http://127.0.0.1:8000/api/voice/status`

When the model folder exists, `configured` should be true. This checks the folder; the first actual transcription also verifies that the optional package and model can load.

In the chat, choose **ضبط محلی با Whisper**, speak, and press stop. The resulting transcript is placed in the message box for review; it is not sent until you press the normal send button.

## Privacy and limits

- Maximum audio upload: 20 MB.
- Supported formats include WebM, Ogg, WAV, MP3, MP4/M4A, AAC and FLAC.
- Temporary audio files are removed after transcription, including on errors.
- The model inference runs locally. The audio is not sent to a cloud transcription provider by this endpoint.
- Chat responses may still use the separately configured AI provider; when that provider is remote, text sent for response generation leaves the computer.
- The browser's microphone permission is required. Use the local app at `127.0.0.1` or `localhost`.

## Troubleshooting

- If the endpoint returns 503, install `requirements-voice.txt` and verify the model directory.
- If model loading fails, confirm the folder contains actual CTranslate2 model files rather than Git LFS pointer text.
- If CPU transcription is slow, try a smaller compatible model or configure a supported GPU after installing its matching dependencies.
- If the browser cannot access the microphone, grant microphone permission in browser site settings.
