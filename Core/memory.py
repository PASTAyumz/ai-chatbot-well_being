import json
import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables (kept for other settings like GEMINI_API_KEY)
load_dotenv()

MEMORY_FILE = os.path.join(os.path.dirname(__file__), 'conversation_memory.json')

def _read_all_conversations() -> dict:
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {} # Return empty dict if JSON is invalid
    return {}

def _write_all_conversations(all_conversations: dict):
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_conversations, f, ensure_ascii=False, indent=4)

def save_conversation(conversation_name: str, history: list, user_profile: dict):
    all_conversations = _read_all_conversations()
    all_conversations[conversation_name] = {
        'history': history,
        'user_profile': user_profile
    }
    _write_all_conversations(all_conversations)
    logger.debug(f"Conversation '{conversation_name}' saved to JSON.")

def load_conversation(conversation_name: str) -> tuple[list, dict]:
    all_conversations = _read_all_conversations()
    conversation_data = all_conversations.get(conversation_name)
    if conversation_data:
        logger.debug(f"Conversation '{conversation_name}' loaded from JSON.")
        return conversation_data.get('history', []), conversation_data.get('user_profile', {})
    return [], {}

def list_conversations(user_id: str) -> list[str]:
    all_conversations = _read_all_conversations()
    user_conversations = []
    prefix = f"{user_id}_"
    for name in all_conversations.keys():
        if name.startswith(prefix):
            user_conversations.append(name[len(prefix):])
    logger.debug(f"Listed conversations for user '{user_id}' from JSON.")
    return user_conversations

def delete_conversation(user_id: str, conversation_name: str):
    conversation_name_with_prefix = f"{user_id}_{conversation_name}"
    all_conversations = _read_all_conversations()
    if conversation_name_with_prefix in all_conversations:
        del all_conversations[conversation_name_with_prefix]
        _write_all_conversations(all_conversations)
        logger.debug(f"Conversation '{conversation_name_with_prefix}' deleted from JSON.") 
