# Core/emojis.py

# A curated collection of emojis, categorized for careful use.
# Use these emojis to enhance the bot's responses based on context and sentiment.

EMOJI_COLLECTION = {
    "positive": [
        "😊", # Smiling face with smiling eyes
        "✨", # Sparkles (for positive emphasis, magic, good ideas)
        "👍", # Thumbs up (for agreement, encouragement)
        "✅", # Check mark (for confirmation, success)
        "🌟", # Glowing star (for excellent, shining)
        "💖", # Sparkling heart (for warmth, strong positive emotion)
        "🥳", # Partying face (for celebration, excitement)
        "☀️"  # Sun (for brightness, good day)
    ],
    "neutral": [
        "💬", # Speech balloon (for conversation, discussion)
        "🤔", # Thinking face (for pondering, reflection)
        "💡", # Light bulb (for ideas, understanding)
        "✍️", # Writing hand (for logging, noting)
        "📖", # Open book (for learning, information)
        "🕰️"  # Mantelpiece clock (for time, planning)
    ],
    "empathetic": [ # For responses that acknowledge difficult emotions or provide comfort
        "🫂", # People hugging (for support, comfort)
        "😔", # Pensive face (for sadness, disappointment, but not overly negative)
        "🥺", # Pleading face (for sympathy, "oh no")
        "🙏", # Folded hands (for gratitude, plea, hope)
        "☔", # Umbrella with rain (for comforting in bad weather/times)
        "💡"  # Light bulb (for a glimmer of hope/solution) - can overlap with neutral
    ],
    "guidance": [ # For responses that offer steps, advice, or direction
        "➡️", # Right arrow (for next step, direction)
        "🧘", # Person in lotus position (for relaxation, meditation)
        "📝", # Memo (for noting, advice)
        "🗣️"  # Speaking head (for talking, expressing)
    ],
    "special": { # For specific, non-sentiment-based uses
        "new_chat_start": "🚀", # Rocket (for starting something new)
        "success_save": "✅", # Check mark (for successful save)
        "error": "❌", # Cross mark (for errors)
        "loading": "⏳" # Hourglass (for processing)
    }
}

def get_emoji(category: str, index: int = 0) -> str:
    """
    Retrieves an emoji from the collection based on category and index.
    Returns an empty string if category or index is invalid.
    """
    return EMOJI_COLLECTION.get(category, [])[index] if category in EMOJI_COLLECTION and \
           isinstance(EMOJI_COLLECTION.get(category), list) and \
           len(EMOJI_COLLECTION[category]) > index else ""

def get_random_emoji(category: str) -> str:
    """
    Retrieves a random emoji from the specified category.
    Returns an empty string if category is invalid or empty.
    """
    import random
    if category in EMOJI_COLLECTION and isinstance(EMOJI_COLLECTION.get(category), list) and \
       EMOJI_COLLECTION[category]:
        return random.choice(EMOJI_COLLECTION[category])
    return ""

def get_specific_emoji(key: str) -> str:
    """
    Retrieves a specific emoji from the 'special' category by its key.
    Returns an empty string if key is invalid.
    """
    return EMOJI_COLLECTION.get("special", {}).get(key, "") 