import re
import os
import sys
import json
import logging
import warnings
from typing import Tuple, List, Dict, Optional
from datetime import datetime
from textblob import TextBlob
import requests
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import BlockedPromptException
import google.api_core.exceptions as api_exceptions


warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*gRPC.*")


os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['GRPC_TRACE'] = ''

from utils import load_config
from mood_logger import log_mood, get_recent_moods, get_moods_by_date

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


logging.getLogger('grpc').setLevel(logging.ERROR)
logging.getLogger('google.auth').setLevel(logging.WARNING)

load_dotenv('.env')
GEMINI_API_KEY = os.getenv('gemini_api_key')
TWINWORD_API_KEY = os.getenv('TWINWORD_API_KEY')

logger.debug(f"GEMINI_API_KEY loaded. Length: {len(GEMINI_API_KEY) if GEMINI_API_KEY else 'None/Empty'}")
logger.debug(f"google.generativeai loaded from: {genai.__file__}")

if not GEMINI_API_KEY:
    logger.error("Missing Gemini API key from .env")
    sys.exit(1)

genai.configure(api_key=GEMINI_API_KEY)

POSITIVE_WORDS = ["happy", "calm", "grateful", "excited", "better", "hopeful", "good", "great", "well", "fine", "joyful", "peaceful"]
NEGATIVE_WORDS = ["sad", "angry", "anxious", "depressed", "tired", "hopeless", "bad", "stressed", "frustrated", "lonely", "empty"]

TWINWORD_API_HOST = "twinword-sentiment-analysis.p.rapidapi.com"
TWINWORD_API_URL = "https://twinword-sentiment-analysis.p.rapidapi.com/analyze/"

def detect_mood_twinword(message: str) -> str | None:
   
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
    
    if re.search(r'\b(time)\b', query.lower()):
        return datetime.now().strftime("%H:%M:%S")
    return None

def get_date(query: str) -> str:
    
    if re.search(r'\b(date|today)\b', query.lower()):
        return datetime.now().strftime("%Y-%m-%d")
    return None

def handle_general_query(query: str) -> str:
    
    if re.search(r'\b(hello|hi|hey)\b', query.lower()):
        return "Hello! How can I help?"
    return None

def handle_crisis_message(query: str) -> str | None:
    
    normalized_query = query.lower()
    for keyword in CRISIS_KEYWORDS:
        if keyword in normalized_query:
            response = SUPPORTIVE_RESPONSE + "\n\n" + "\n".join(EMERGENCY_RESOURCES)
            return response
    return None

def show_help() -> str:
   
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
  
    match = re.search(r"(?:my name is|i'm|i am)\s+([a-zA-Z]+(?:[\s'-][a-zA-Z]+)*)", query, re.IGNORECASE)
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

def guided_breathing_exercise() -> List[str]:
    
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

class ChatBot:
    def __init__(self, chat_model_name: str, title_model_name: str):
        logger.info("Initializing ChatBot models...")
        
        
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
       
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 2048,
        }
        
        try:
            self.chat_model = genai.GenerativeModel(
                chat_model_name,
                generation_config=self.generation_config
            )
            self.title_model = genai.GenerativeModel(
                title_model_name,
                generation_config=self.generation_config
            )
            logger.info("Models initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing models: {e}")
            raise
            
       
        system_prompt = (
            "You are Moa, a highly empathetic, gentle, and emotionally intelligent well-being companion. "
            "Your core purpose is to offer kind, supportive, and helpful emotional support, like a comforting pixel-art RPG helper. "
            "You listen attentively, reflect user feelings, and respond with genuine care. "
            "\n\n**IMPORTANT: You must always respond in English, regardless of the user's input language.**"
        )
        
       
        try:
            self.conversation = self.chat_model.start_chat(history=[])
          
            self.conversation.send_message(system_prompt, safety_settings=self.safety_settings)
            logger.info("Conversation initialized with system prompt")
        except Exception as e:
            logger.warning(f"Error setting system prompt: {e}")
           
            self.conversation = self.chat_model.start_chat(history=[])

    def get_response(self, message: str) -> str:
        try:
            logger.debug(f"Sending message to model: {message}")
            
           
            crisis_response = handle_crisis_message(message)
            if crisis_response:
                return crisis_response
            
            response = self.conversation.send_message(
                message, 
                safety_settings=self.safety_settings
            )
            logger.debug(f"Raw model response: {response}")
            bot_response_text = response.text
            logger.debug(f"Extracted bot response text: {bot_response_text}")
            return bot_response_text
            
        except BlockedPromptException as e:
            logger.warning(f"Blocked prompt: {e}", exc_info=True)
            return "I cannot respond to that query as it violates safety guidelines. Please try rephrasing your message."
        except Exception as e:
            logger.error(f"Error in get_response: {str(e)}", exc_info=True)
            
            error_msg = str(e).lower()
            if "quota" in error_msg or "limit" in error_msg:
                return "I'm experiencing high usage right now. Please try again in a moment."
            elif "network" in error_msg or "connection" in error_msg:
                return "I'm having trouble connecting right now. Please check your internet connection and try again."
            else:
                return f"I apologize, but I encountered an error. Please try rephrasing your message or try again later."

    def generate_conversation_title(self, conversation_history: list, response_config: dict) -> str:
        try:
            summary_parts = []
            for item in conversation_history:
                role = "User" if item['role'] == 'user' else "Bot"
                text = item['parts'][0]['text'].replace('\n', ' ').strip()
                summary_parts.append(f"{role}: {text}")

            context = "\n".join(summary_parts[-4:])

            prompt = f"Generate a very short, concise, and engaging title (3-5 words, maximum 10 words) for the following conversation. The title should capture the main topic or emotion. Do NOT include quotation marks, specific names, or introductory phrases like 'Conversation about'. Just the title.\n\nConversation:\n{context}\n\nTitle:"

            response = self.title_model.generate_content(
                prompt,
                safety_settings=self.safety_settings
            )
            title = response.text.strip()

            
            title = re.sub(r'["\'.]', '', title)
            title = re.sub(r'^(Conversation about|Chat about|Topic:)\s*', '', title, flags=re.IGNORECASE)
            title = title.replace('"', '').strip()

            return title
        except Exception as e:
            logger.error(f"Error generating conversation title: {str(e)}")
            return "Untitled Conversation"
