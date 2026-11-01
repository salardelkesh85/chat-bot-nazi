from app.models import CompanionEmotionalState

POSITIVE_CUES = ("ممنون", "مرسی", "خوشحالم", "عالی", "مهربونی", "عزیزم", "thank you", "thanks", "happy", "great", "kind")
NEGATIVE_CUES = ("عصبانی", "ناراحتم", "اذیتم", "بی‌احترامی", "بد بود", "angry", "upset", "hurt", "rude", "awful")
ENERGY_CUES = ("خسته", "خوابم", "بی‌حوصله", "tired", "sleepy", "exhausted")

def bounded(value: int) -> int:
    return max(0, min(100, value))

def update_emotional_state(state: CompanionEmotionalState, user_text: str) -> CompanionEmotionalState:
    text = (user_text or "").casefold()
    positive = any(cue in text for cue in POSITIVE_CUES)
    negative = any(cue in text for cue in NEGATIVE_CUES)
    tired = any(cue in text for cue in ENERGY_CUES)
    state.interaction_count += 1
    if positive and not negative:
        state.closeness = bounded(state.closeness + 1)
        state.trust = bounded(state.trust + 1)
        state.mood = "warm"
    elif negative and not positive:
        state.mood = "concerned"
    else:
        state.mood = "calm"
    state.energy = bounded(state.energy - 2 if tired else state.energy + 1)
    return state

def describe_state(state: CompanionEmotionalState) -> str:
    moods = {"calm": "calm and composed", "warm": "warm and friendly", "concerned": "concerned and attentive"}
    return (
        f"Current conversational tone: {moods.get(state.mood, 'calm and composed')}. "
        f"Familiarity: {state.closeness}/100. Trust: {state.trust}/100. Energy: {state.energy}/100. "
        "These are fictional roleplay settings, not real emotions or a measure of the user's worth. "
        "Never pressure the user to change these values."
    )
