# Voice Conversation

## Implemented browser features
- Persian speech recognition using the Web Speech API with `fa-IR`.
- Microphone button in the chat; recognized text is inserted into the composer for review before sending.
- Optional automatic speech playback of assistant responses.
- Existing per-message speech playback, rate and pitch controls remain available.

## Browser requirements
- A browser that implements SpeechRecognition or webkitSpeechRecognition (current Chromium-based browsers are the intended target).
- Microphone permission granted to the local app.
- Speech recognition availability and quality depend on the browser, operating system, language pack and network conditions.

## Privacy caveat
The browser SpeechRecognition implementation may process audio through a browser/vendor speech service. This iteration does not claim offline or local-only microphone transcription. Do not use it for sensitive audio if the browser's processing policy is not acceptable.

## Next local-first voice milestone
Integrate a locally hosted speech-to-text engine (for example, whisper.cpp or faster-whisper) behind a backend interface. Audio should be posted only to the local FastAPI service, and inference should run on the user's computer. Add explicit recording controls and clear microphone status.
