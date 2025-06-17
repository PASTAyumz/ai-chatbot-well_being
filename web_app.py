import os
import sys
import logging
import tempfile
import traceback
import warnings
import whisper
import werkzeug.datastructures
from dotenv import load_dotenv
import secrets
import uuid
from flask import Flask, render_template, request, jsonify, session


import warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*gRPC.*")


os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['GRPC_TRACE'] = ''
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' 


logging.getLogger('grpc').setLevel(logging.ERROR)
logging.getLogger('google.auth').setLevel(logging.WARNING)

from flask import Flask, render_template, request, jsonify


ffmpeg_bin_path = r"C:\Users\PC\Desktop\ffmpeg-N-119884-gfb65ecbc9b-win64-gpl-shared\bin"
if os.path.exists(ffmpeg_bin_path) and ffmpeg_bin_path not in os.environ['PATH']:
    os.environ['PATH'] += os.pathsep + ffmpeg_bin_path
    logging.info(f"Added FFmpeg bin path to Python's PATH: {ffmpeg_bin_path}")


logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Core')))
    
    
    from Core.chatbot import ChatBot, guided_breathing_exercise
    from Core.utils import load_config
    from Core.memory import save_conversation, load_conversation, list_conversations, delete_conversation
    
    app = Flask(__name__)
    app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_urlsafe(16))
    config = load_config()

    # Load environment variables from .env file explicitly
    load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
    
    logger.info("Initializing ChatBot...")
    chatbot_instance = ChatBot(chat_model_name="gemini-1.5-flash", title_model_name="gemini-1.5-flash")
    logger.info("ChatBot initialized successfully")

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/chat', methods=['POST'])
    def chat():
        try:
            # Ensure a user_id exists in the session
            if 'user_id' not in session:
                session['user_id'] = str(uuid.uuid4())
                logger.info(f"New user session created: {session['user_id']}")

            user_id = session['user_id']
            data = request.get_json()
            if not data or 'message' not in data:
                return jsonify({'error': 'No message provided'}), 400

            # Original conversation_name from frontend
            frontend_conversation_name = data.get('conversation_name', 'default')
            # Prefix conversation_name with user_id for isolation
            conversation_name_with_prefix = f"{user_id}_{frontend_conversation_name}"

            user_message = data['message']
            
            # Get history and user profile from frontend
            current_conversation_history = data.get('history', [])
            current_user_profile = data.get('user_profile', {})

            logger.debug(f"Chat: user_id: {user_id}, conversation_name: {conversation_name_with_prefix}, History size: {len(current_conversation_history)}")
            logger.debug(f"User message: {user_message}")

            response_config = {
                'current_language': data.get('language', config.get('default_language', 'en'))
            }
            
            # Generate new title for default conversations with empty history
            if frontend_conversation_name == 'default' and not current_conversation_history:
                logger.debug("Generating new conversation title")
                
                # Create temporary history for title generation
                title_generation_history = [{'role': 'user', 'parts': [{'text': user_message}]}]
                generated_title = chatbot_instance.generate_conversation_title(
                    title_generation_history,
                    response_config
                )
                # Prefix the generated title as well
                conversation_name_with_prefix = f"{user_id}_{generated_title}"
                logger.debug(f"Generated prefixed title: '{conversation_name_with_prefix}'")
                
                # Load existing history for this conversation name
                loaded_history, loaded_profile = load_conversation(conversation_name_with_prefix)
                current_conversation_history = loaded_history
                current_user_profile = loaded_profile if not current_user_profile else current_user_profile
            else:
                # Load existing conversation with the prefixed name
                current_conversation_history, current_user_profile = load_conversation(conversation_name_with_prefix)

            # Add user message to history
            current_conversation_history.append({'role': 'user', 'parts': [{'text': user_message}]})

            # Get bot response
            bot_response_text = chatbot_instance.get_response(user_message)
            logger.debug(f"Bot response: {bot_response_text}")
            
            # Update history with bot response
            updated_history = current_conversation_history + [{'role': 'model', 'parts': [{'text': bot_response_text}]}]
            updated_profile = current_user_profile

            # Save conversation with prefixed name
            save_conversation(conversation_name_with_prefix, updated_history, updated_profile)
            logger.debug(f"Saved conversation '{conversation_name_with_prefix}' with {len(updated_history)} entries")
            
            return jsonify({
                'response': bot_response_text,
                'history': updated_history,
                'user_profile': updated_profile,
                'conversation_name': frontend_conversation_name  # Return original name to frontend
            })

        except Exception as e:
            logger.error(f"Chat error: {str(e)}", exc_info=True)
            return jsonify({
                'error': str(e),
                'response': f"I encountered an error: {str(e)}"
            }), 500

    @app.route("/transcribe", methods=["POST"])
    def transcribe():
        try:
            logger.debug("Transcribe endpoint called")
            
            
            if 'audio' not in request.files:
                logger.error("No audio file in request")
                return jsonify({"error": "No audio file provided"}), 400
            
            audio_file = request.files['audio']
            
           
            if not audio_file or audio_file.filename == '':
                logger.error("Empty audio file")
                return jsonify({"error": "No audio file selected"}), 400
            
            logger.debug(f"Audio file received: {audio_file.filename}")
            
            temp_audio_path = None
            try:
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_audio:
                    audio_file.save(tmp_audio.name)
                    temp_audio_path = tmp_audio.name
                    logger.debug(f"Audio saved to: {temp_audio_path}")

               
                if not os.path.exists(temp_audio_path) or os.path.getsize(temp_audio_path) == 0:
                    logger.error("Audio file is empty or doesn't exist")
                    return jsonify({"error": "Audio file is empty"}), 400

              
                logger.debug("Loading Whisper model...")
                model = whisper.load_model("base")
                logger.debug("Transcribing audio...")
                result = model.transcribe(temp_audio_path)
                
                transcribed_text = result["text"]
                logger.debug(f"Transcription result: {transcribed_text}")
                
                return jsonify({"text": transcribed_text})
                
            except Exception as e:
                logger.error(f"Transcription processing error: {str(e)}", exc_info=True)
                return jsonify({"error": f"Transcription failed: {str(e)}"}), 500
            finally:
                
                if temp_audio_path and os.path.exists(temp_audio_path):
                    try:
                        os.remove(temp_audio_path)
                        logger.debug("Temporary audio file cleaned up")
                    except Exception as e:
                        logger.warning(f"Failed to clean up temp file: {e}")
                        
        except Exception as e:
            logger.error(f"Transcribe endpoint error: {str(e)}", exc_info=True)
            return jsonify({"error": f"Server error: {str(e)}"}), 500

    @app.route('/breathing_exercise', methods=['POST'])
    def breathing_exercise():
        try:
            return jsonify({
                'success': True, 
                'steps': guided_breathing_exercise()
            })
        except Exception as e:
            logger.error(f"Breathing exercise error: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/save_conversation', methods=['POST'])
    def save_current_conversation():
        try:
            if 'user_id' not in session:
                return jsonify({'success': False, 'message': 'No user session found'}), 401
            user_id = session['user_id']
            
            data = request.get_json()
            if not data or 'conversation_name' not in data:
                return jsonify({'success': False, 'message': 'Missing conversation name'}), 400

            frontend_conversation_name = data['conversation_name']
            conversation_name_with_prefix = f"{user_id}_{frontend_conversation_name}"

            save_conversation(
                conversation_name_with_prefix,
                data.get('history', []),
                data.get('user_profile', {})
            )
            return jsonify({'success': True})

        except Exception as e:
            logger.error(f"Save conversation error: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

    @app.route('/load_conversation', methods=['GET'])
    def load_current_conversation():
        try:
            if 'user_id' not in session:
                return jsonify({'success': False, 'message': 'No user session found'}), 401
            user_id = session['user_id']
            
            frontend_conversation_name = request.args.get('conversation_name', 'default')
            conversation_name_with_prefix = f"{user_id}_{frontend_conversation_name}"
            
            history, profile = load_conversation(conversation_name_with_prefix)
            return jsonify({
                'success': True, 
                'history': history, 
                'user_profile': profile,
                'conversation_name': frontend_conversation_name # Return original name to frontend
            })
        except Exception as e:
            logger.error(f"Load conversation error: {str(e)}")
            return jsonify({
                'success': False, 
                'message': f'Failed to load: {str(e)}'
            }), 500

    @app.route('/list_conversations', methods=['GET'])
    def get_conversation_list():
        try:
            if 'user_id' not in session:
                return jsonify({'success': False, 'message': 'No user session found'}), 401
            user_id = session['user_id']
            
            return jsonify({
                'success': True, 
                'conversations': list_conversations(user_id)
            })
        except Exception as e:
            logger.error(f"List conversations error: {str(e)}")
            return jsonify({
                'success': False, 
                'message': f'Failed to list: {str(e)}'
            }), 500

    @app.route('/delete_conversation', methods=['POST'])
    def delete_conversation_route():
        try:
            if 'user_id' not in session:
                logger.warning("Delete conversation: No user session found")
                return jsonify({'success': False, 'message': 'No user session found'}), 401
            user_id = session['user_id']
            
            data = request.get_json()
            if not data or not data.get('conversation_name'):
                logger.warning("Delete conversation: No conversation name provided")
                return jsonify({
                    'success': False, 
                    'message': 'Conversation name required'
                }), 400

            frontend_conversation_name = data['conversation_name']
            logger.debug(f"Deleting conversation: '{frontend_conversation_name}' for user '{user_id}'")
            
            delete_conversation(user_id, frontend_conversation_name)
            logger.info(f"Successfully deleted conversation: '{frontend_conversation_name}' for user '{user_id}'")
            return jsonify({
                'success': True, 
                'message': 'Conversation deleted'
            })
        except Exception as e:
            logger.error(f"Delete conversation error: {str(e)}", exc_info=True)
            return jsonify({
                'success': False, 
                'message': f'Failed to delete: {str(e)}'
            }), 500

    @app.errorhandler(404)
    def page_not_found(e):
        return jsonify({'error': 'Not found'}), 404

    if __name__ == '__main__':
        logger.info("Starting Flask application...")
        app.run(debug=True, host='0.0.0.0', port=5000)

except ImportError as e:
    logger.error(f"Fatal import error: {str(e)}")
    print(f"Missing dependencies. Please install required packages:")
    print("pip install flask whisper-openai python-dotenv google-generativeai textblob requests")
    sys.exit(1)
except Exception as e:
    logger.error(f"Fatal startup error: {str(e)}")
    sys.exit(1)
