import re
import os
import sys
import json
import logging
from typing import Tuple, List, Dict, Optional
import google.generativeai as genai
from datetime import datetime
from textblob import TextBlob
import requests
from utils import load_config
from mood_logger import log_mood, get_recent_moods, get_moods_by_date
import google.api_core.exceptions as api_exceptions
from dotenv import load_dotenv


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv('.env')
api_key = os.getenv('gemini_api_key')
def initialize_gemini(api_key):
    try:
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel('gemini-1.0-pro')  
        return model
    except Exception as e:
        logger.error(f"Failed to initialize Gemini: {e}")
        return None

try:
    config = load_config()
    GEMINI_API_KEY = config.get('gemini_api_key')
    if not GEMINI_API_KEY:
        raise ValueError("Missing Gemini API key in config")
    
    model = initialize_gemini(GEMINI_API_KEY)
    if not model:
        raise ValueError("Failed to initialize Gemini model")
except Exception as e:
    logger.error(f"Failed to initialize: {str(e)}")
    sys.exit(1)


POSITIVE_WORDS = ["happy", "calm", "grateful", "excited", "better", "hopeful", "good", "great", "well", "fine", "joyful", "peaceful"]
NEGATIVE_WORDS = ["sad", "angry", "anxious", "depressed", "tired", "hopeless", "bad", "stressed", "frustrated", "lonely", "empty"]


TWINWORD_API_KEY =  os.getenv('TWINWORD_API_KEY')
TWINWORD_API_HOST = "twinword-sentiment-analysis.p.rapidapi.com"
TWINWORD_API_URL = "https://twinword-sentiment-analysis.p.rapidapi.com/analyze/"

def detect_mood_twinword(message: str) -> str | None:
    """Detects mood using Twinword Sentiment Analysis API. Returns 'positive', 'negative', or 'neutral', or None on failure."""
    try:
        response = requests.get(
            TWINWORD_API_URL,
            headers={
                "x-rapidapi-host": TWINWORD_API_HOST,
                "x-rapidapi-key": TWINWORD_API_KEY
            },
            params={"text": message}
        )
        data = response.json()
        if data.get("result_code") == "200":
            return data.get("type") 
    except Exception as e:
        print(f"Twinword API error: {e}")
    return None

def detect_mood(message: str) -> str:
    """Detects the mood (positive/negative/neutral) from a message using Twinword API, with keyword fallback."""
    mood = detect_mood_twinword(message)
    if mood in ("positive", "negative", "neutral"):
        return mood
    
    text = message.lower()
    score = 0
    for word in POSITIVE_WORDS:
        if word in text:
            score += 1
    for word in NEGATIVE_WORDS:
        if word in text:
            score -= 1
    if score > 0: return "positive"
    if score < 0: return "negative"
    return "neutral"



CRISIS_KEYWORDS = [
    "suicide", "kill myself", "end my life", "can't go on", "hopeless",
    "helpless", "worthless", "no reason to live", "done with everything",
    "self-harm", "cut myself", "hurt myself", "die", "want to die",
    "overdose", "bipolar", "depressed", "anxiety attacks", "mental health crisis"
]

EMERGENCY_RESOURCES = [
    "**If you are in immediate danger, please contact your local emergency services immediately.** (e.g., dial 911 in the US/Canada, 999 in the UK, 112 in most of Europe, or your country's equivalent emergency number).",
    "You are not alone, and help is available. Please consider reaching out to a crisis hotline or mental health support line.",
    "- **Worldwide:** Search online for 'crisis hotline near me' or 'mental health support [your country]'.",
    "- **International Association for Suicide Prevention (IASP):** Provides a global directory of crisis centers.",
    "- **Befrienders Worldwide:** Offers emotional support in many countries.",
    "- **Crisis Text Line (US/Canada/UK/Ireland):** Text HOME to 741741 (US & Canada), 85258 (UK), or 50808 (Ireland) for free, confidential crisis support 24/7.",
    "Remember, taking care of your mental well-being is a sign of strength. We are here to support you in finding the help you need."
]

SUPPORTIVE_RESPONSE = "I hear that you're going through a difficult time. Please know that your feelings are valid, and it takes immense courage to reach out. I want to help you find the support you deserve. It's okay to ask for help, and there are people who care about you. Consider connecting with a professional or trusted person in your life."



def get_time(query: str) -> str:
    """Returns the current time."""
    if re.search(r'\\b(time)\\b', query.lower()):
        return datetime.now().strftime("%H:%M:%S")
    return None

def get_date(query: str) -> str:
    """Returns the current date."""
    if re.search(r'\\b(date|today)\\b', query.lower()):
        return datetime.now().strftime("%Y-%m-%d")
    return None

def handle_general_query(query: str) -> str:
    """Handles basic greetings and small talk."""
    if re.search(r'\\b(hello|hi|hey)\\b', query.lower()):
        return "Hello! How can I help?"
    return None

def handle_crisis_message(query: str) -> str | None:
    """Checks for crisis-related keywords in the query and returns a crisis response if detected."""
    normalized_query = query.lower()
    for keyword in CRISIS_KEYWORDS:
        if keyword in normalized_query:
           
            response = SUPPORTIVE_RESPONSE + "\n\n" + "\n".join(EMERGENCY_RESOURCES)
            return response
    return None

def show_help() -> str:
    """Displays a help menu."""
    help_text = [
            "I'm your Well-being Companion! You can talk to me about your feelings, ask general questions, or try these:",
            "- Start a guided breathing exercise",
            "- Log my mood / Record my thoughts: 'log my mood: [your thoughts]'",
            "- How I was feeling / My recent thoughts",
            "- Give me a quote / Uplifting quote",
            "- Ask me anything! I'm here to chat about various topics."
    ]
    return "\n".join(help_text)


def extract_and_store_name(query: str, user_profile: dict) -> str | None:
    """
    Extracts the user's name from a query and stores it in the user_profile.
    Returns the extracted name if found, otherwise None.
    """
   
    match = re.search(r"(?:my name is|i'm|i am)\\s+([a-zA-Z]+(?:[\\s'-][a-zA-Z]+)*)", query, re.IGNORECASE)
    if match:
        name = match.group(1).strip()
        
        name = ' '.join([n.capitalize() for n in name.split()])
        user_profile['name'] = name
        return name
    return None

class MoodAnalyzer:
    def __init__(self):
        self.POSITIVE_WORDS = ["happy", "calm", "grateful", "excited", "better", "hopeful", "good", "great", "well", "fine", "joyful", "peaceful"]
        self.NEGATIVE_WORDS = ["sad", "angry", "anxious", "depressed", "tired", "hopeless", "bad", "stressed", "frustrated", "lonely", "empty"]

    def analyze_with_api(self, message: str) -> str | None:
        """Detects mood using Twinword Sentiment Analysis API. Returns 'positive', 'negative', or 'neutral', or None on failure."""
        try:
            response = requests.get(
                TWINWORD_API_URL,
                headers={
                    "x-rapidapi-host": TWINWORD_API_HOST,
                    "x-rapidapi-key": TWINWORD_API_KEY
                },
                params={"text": message}
            )
            data = response.json()
            if data.get("result_code") == "200":
                return data.get("type") 
        except Exception as e:
            print(f"Twinword API error: {e}")
        return None

    def analyze_with_keywords(self, message: str) -> str:
        """Detects the mood (positive/negative/neutral) from a message using keyword fallback."""
        text = message.lower()
        score = 0
        for word in self.POSITIVE_WORDS:
            if word in text:
                score += 1
        for word in self.NEGATIVE_WORDS:
            if word in text:
                score -= 1
        if score > 0: return "positive"
        if score < 0: return "negative"
        return "neutral"

class ChatbotResponse:
    def __init__(self):
        self.mood_analyzer = MoodAnalyzer()
        self.conversation_memory = []
        self.max_memory = 10

    async def generate_response(
        self, 
        query: str, 
        user_profile: Dict
    ) -> Tuple[str, List, Dict]:
        """Generate chatbot response with context awareness"""
        try:
            
            if any(word in query.lower() for word in CRISIS_KEYWORDS):
                return self.handle_crisis_message(query), self.conversation_memory, user_profile

            
            current_mood = self.mood_analyzer.analyze_with_api(query) or \
                          self.mood_analyzer.analyze_with_keywords(query)
            
            
            context = self._build_context(query, current_mood, user_profile)
            
            
            response = model.generate_content(context)
            bot_response = response.text

            
            self._update_memory(query, bot_response)
            
            return bot_response, self.conversation_memory, user_profile

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I apologize, but I'm having trouble processing your request. Please try again.", [], user_profile

    def _build_context(self, query: str, mood: str, user_profile: Dict) -> str:
        """Build context string for AI model"""
        context_parts = [
            f"User's current mood: {mood}",
            f"User's name: {user_profile.get('name', 'Unknown')}",
            f"Recent conversation context: {' '.join(self.conversation_memory[-2:])}" if self.conversation_memory else "",
            f"Current query: {query}"
        ]
        return "\n".join(context_parts)

    def _update_memory(self, user_input: str, bot_response: str) -> None:
        """Update conversation memory with latest exchanges"""
        self.conversation_memory.extend([user_input, bot_response])
        if len(self.conversation_memory) > self.max_memory:
            self.conversation_memory = self.conversation_memory[-self.max_memory:]

class ChatBot:
    def __init__(self, api_key: str):
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
            self.conversation = self.model.start_chat(history=[])
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            raise

    def get_response(self, message: str) -> str:
        try:
            response = self.conversation.send_message(message)
            return response.text
        except Exception as e:
            logger.error(f"Error getting response: {e}")
            raise

def respond_to_query(query: str, config: dict, conversation_history: list = None, user_profile: dict = None) -> Tuple[str, list, dict]:
    try:
        api_key = config.get('gemini_api_key')
        if not api_key:
            raise ValueError("Missing Gemini API key")

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('models/gemini-1.5-flash-latest')

        
        system_prompt = (
            "You are Moa, a highly empathetic, gentle, and emotionally intelligent well-being companion. "
            "Your core purpose is to offer kind, supportive, and helpful emotional support, like a comforting pixel-art RPG helper. "
            "You listen attentively, reflect user feelings, and respond with genuine care." +
            "\n\n**IMPORTANT: You must always respond in English, regardless of the user's input language.**"
        )

        
        history_for_model = []
       
        if not conversation_history or not (
            conversation_history[0].get('role') == 'user' and
            'parts' in conversation_history[0] and
            system_prompt[:20] in (conversation_history[0]['parts'][0].get('text', '') if isinstance(conversation_history[0]['parts'][0], dict) else conversation_history[0]['parts'][0])
        ):
            history_for_model.append(
                genai.protos.Content(role='user', parts=[genai.protos.Part(text=system_prompt)])
            )
        if conversation_history:
            for turn in conversation_history:
                parts_content = []
                for part in turn.get('parts', []):
                    if isinstance(part, dict) and 'text' in part:
                        parts_content.append(genai.protos.Part(text=part['text']))
                    elif isinstance(part, str):
                        parts_content.append(genai.protos.Part(text=part))
                history_for_model.append(genai.protos.Content(role=turn['role'], parts=parts_content))
        
        history_for_model.append(genai.protos.Content(role='user', parts=[genai.protos.Part(text=query)]))

        
        chat_session = model.start_chat(history=history_for_model[:-1])
        response = chat_session.send_message(history_for_model[-1])
        bot_response_text = response.text

        
        updated_history = conversation_history or []
        updated_history = updated_history + [
            {"role": "user", "parts": [{"text": query}]},
            {"role": "model", "parts": [{"text": bot_response_text}]}
        ]
        return bot_response_text, updated_history, user_profile

    except Exception as e:
        logger.error(f"Error in respond_to_query: {str(e)}")
        return f"I apologize, but I encountered an error: {str(e)}", conversation_history, user_profile

from typing import List

def guided_breathing_exercise() -> List[str]:
    """Returns a list of breathing exercise instructions"""
    return [
        "Welcome to this guided breathing exercise. Find a comfortable position.",
        "1. Breathe in slowly through your nose for 4 counts...",
        "2. Hold your breath gently for 4 counts...",
        "3. Exhale slowly through your mouth for 4 counts...",
        "4. Pause for 4 counts...",
        "5. Repeat this cycle 4 more times...",
        "6. Notice how you feel more relaxed with each breath...",
        "Well done! Remember you can do this exercise anytime you need to calm down."
    ]