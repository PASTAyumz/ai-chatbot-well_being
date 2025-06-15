import json
import os

MEMORY_FILE = os.path.join(os.path.dirname(__file__), 'conversation_memory.json')

def _read_all_conversations() -> dict:
    """Helper to read all conversations from the memory file."""
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {} # Return empty dict if file is corrupted or empty
    return {}

def _write_all_conversations(all_conversations: dict):
    """Helper to write all conversations to the memory file."""
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_conversations, f, ensure_ascii=False, indent=4)

def save_conversation(conversation_name: str, history: list, user_profile: dict):
    """Saves a named conversation history and user profile to a file."""
    all_conversations = _read_all_conversations()
    all_conversations[conversation_name] = {
        'history': history,
        'user_profile': user_profile
    }
    _write_all_conversations(all_conversations)

def load_conversation(conversation_name: str) -> tuple[list, dict]:
    """Loads a specific named conversation history and user profile from a file."""
    all_conversations = _read_all_conversations()
    conversation_data = all_conversations.get(conversation_name)
    if conversation_data:
        return conversation_data.get('history', []), conversation_data.get('user_profile', {})
    return [], {} # Return empty if conversation name does not exist

def list_conversations() -> list[str]:
    """Lists all available conversation names."""
    all_conversations = _read_all_conversations()
    return list(all_conversations.keys())

def delete_conversation(conversation_name: str):
    """Deletes a specific named conversation from the memory file."""
    all_conversations = _read_all_conversations()
    if conversation_name in all_conversations:
        del all_conversations[conversation_name]
        _write_all_conversations(all_conversations) 