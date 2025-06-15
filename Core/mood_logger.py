import json
import logging
from datetime import datetime
from pathlib import Path

MOOD_LOG_FILE = Path("data/mood_log.json")

logger = logging.getLogger(__name__)

def _load_mood_log():
    """Loads the mood log from the JSON file."""
    if MOOD_LOG_FILE.exists():
        with open(MOOD_LOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def _save_mood_log(log_data):
    """Saves the mood log to the JSON file."""
    MOOD_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MOOD_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=4)

class MoodLogger:
    def __init__(self):
        self.moods_file = "data/moods.json"

    def log_mood(self, mood_data):
        """
        Log mood with timestamp
        mood_data should be a dictionary containing 'mood' and 'message'
        """
        try:
            timestamp = datetime.now().isoformat()
            mood_entry = {
                'timestamp': timestamp,
                'mood': mood_data.get('mood'),
                'message': mood_data.get('message')
            }
            log_data = _load_mood_log()
            log_data.append(mood_entry)
            _save_mood_log(log_data)
            return True
        except Exception as e:
            logger.error(f"Error logging mood: {e}")
            return False


mood_logger = MoodLogger()


def log_mood(mood_data):
    return mood_logger.log_mood(mood_data)

def get_recent_moods(num_entries: int = 3):
    """Retrieves the most recent mood entries."""
    log_data = _load_mood_log()
    return log_data[-num_entries:]

def get_moods_by_date(date_str: str):
    """Retrieves mood entries for a specific date (YYYY-MM-DD)."""
    log_data = _load_mood_log()
    filtered_moods = [
        entry for entry in log_data
        if entry["timestamp"].startswith(date_str)
    ]
    return filtered_moods