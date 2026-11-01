# Avatar and Voice Foundation

## Avatar
Companions can store an optional avatar image URL in the existing `avatar_url` field. The create and edit screens show a preview, and the companion cards and chat header display the image when set.

This iteration does not upload files to the local server. The image URL must be reachable by the local browser. Local file upload and image management remain planned.

## Voice output
The frontend uses the browser Web Speech API (`speechSynthesis`) to read assistant messages aloud. It prefers an installed Persian (`fa`) system voice and otherwise asks the browser to use its default voice with `fa-IR` language metadata.

Users can set speech rate and pitch in the chat. Playback is on-demand per assistant message and can be stopped.

## Privacy and limitations
- No voice audio is uploaded to the backend by this feature.
- Speech output depends on the browser and operating system's installed voices.
- This is not a bundled offline neural TTS engine. Availability and Persian voice quality vary by Windows/browser installation.
- Microphone input and speech-to-text are not implemented in this milestone.
