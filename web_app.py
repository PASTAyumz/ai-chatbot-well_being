from flask import Flask, render_template, request, jsonify
import os
import sys
import logging
import tempfile
import traceback
import whisper
import werkzeug.datastructures

ffmpeg_bin_path = r"C:\Users\PC\Desktop\ffmpeg-N-119884-gfb65ecbc9b-win64-gpl-shared\bin"
if os.path.exists(ffmpeg_bin_path) and ffmpeg_bin_path not in os.environ['PATH']:
    os.environ['PATH'] += os.pathsep + ffmpeg_bin_path
    logging.info(f"Added FFmpeg bin path to Python's PATH: {ffmpeg_bin_path}")


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add error handling for missing Core directory
try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Core')))
    
    from Core.chatbot import respond_to_query, guided_breathing_exercise, generate_conversation_title
    from Core.utils import load_config
    from Core.memory import save_conversation, load_conversation, list_conversations, delete_conversation
    
    app = Flask(__name__)
    config = load_config()

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/chat', methods=['POST'])
    def chat():
        try:
            data = request.get_json()
            if not data or 'message' not in data:
                return jsonify({'error': 'No message provided'}), 400

            conversation_name = data.get('conversation_name', 'default')
            # Use the history and user_profile passed from the frontend for the current turn
            # Initialize history and user_profile for respond_to_query
            current_conversation_history = data.get('history', [])
            current_user_profile = data.get('user_profile', {})

            logger.debug(f"Chat: Initial conversation_name received: {conversation_name}, History size from frontend: {len(current_conversation_history)}")

            response_config = {
                'gemini_api_key': config.get('gemini_api_key'),
                'current_language': data.get('language', config.get('default_language', 'en'))
            }

            old_conversation_name = conversation_name # Store original name for logging/comparison
            
            # Condition to trigger new title generation: it's a 'default' conversation AND the frontend sent an empty history (meaning it's a new chat session for the user)
            if conversation_name == 'default' and not current_conversation_history:
                logger.debug("Chat: Triggering new conversation title generation for a truly new chat.")
                generated_title = generate_conversation_title(
                    data['message'],
                    response_config
                )
                conversation_name = generated_title # Update conversation_name to the new title
                logger.debug(f"Chat: Generated new title: '{conversation_name}' from old: '{old_conversation_name}'")
                
                # If a new title is generated, we need to check if there's any existing history for this *new* name.
                # If it's truly new, load_conversation will return empty, and that's correct for a fresh start.
                loaded_history, loaded_profile = load_conversation(conversation_name)
                # Append received history to loaded history, effectively starting with a fresh slate if no history exists for the new name
                current_conversation_history = loaded_history + current_conversation_history
                current_user_profile = loaded_profile if not current_user_profile else current_user_profile
                logger.debug(f"Chat: Loaded/Initialized history for NEW conversation '{conversation_name}': {len(current_conversation_history)} entries.")
            else:
                # If it's not a new 'default' chat, or if it's 'default' but not empty, load the actual history from the file
                # The history from frontend for existing conversations is simply the latest turn, not the full history
                current_conversation_history, current_user_profile = load_conversation(conversation_name)
                logger.debug(f"Chat: Loaded history for existing conversation '{conversation_name}': {len(current_conversation_history)} entries.")

            bot_response, updated_history, updated_profile = respond_to_query(
                data['message'],
                response_config,
                current_conversation_history, # Pass the (potentially loaded) history to respond_to_query
                current_user_profile # Pass the (potentially loaded) user_profile
            )

            # Ensure to save with the potentially new conversation_name
            save_conversation(conversation_name, updated_history, updated_profile)
            logger.debug(f"Chat: Conversation '{conversation_name}' saved with {len(updated_history)} entries.")
            return jsonify({
                'response': bot_response,
                'history': updated_history,
                'user_profile': updated_profile,
                'conversation_name': conversation_name # Always return the current conversation name
            })

        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            return jsonify({
                'error': str(e),
                'response': f"I encountered an error: {str(e)}"
            }), 500

    @app.route("/transcribe", methods=["POST"])
    def transcribe():
        if not isinstance(request.files.get('audio'), werkzeug.datastructures.FileStorage):
            return jsonify({"error": "No audio file"}), 400

        audio_file = request.files['audio']
        temp_audio_path = None
        try:
            # Create a temporary file to save the audio
            # Using NamedTemporaryFile to ensure it's deleted after use
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_audio:
                audio_file.save(tmp_audio.name)
                temp_audio_path = tmp_audio.name

            model = whisper.load_model("base") # You can choose "tiny", "base", "small", "medium", "large"
            result = model.transcribe(temp_audio_path)
            
            return jsonify({"text": result["text"]})
        except Exception as e:
            logger.error(f"Local Whisper transcription error: {str(e)}")
            return jsonify({"error": str(e)}), 500
        finally:
            # Clean up the temporary file
            if temp_audio_path and os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)

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
            data = request.get_json()
            if not data or 'conversation_name' not in data:
                return jsonify({'success': False, 'message': 'Missing conversation name'}), 400

            save_conversation(
                data['conversation_name'],
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
            conversation_name = request.args.get('conversation_name', 'default')
            history, profile = load_conversation(conversation_name)
            return jsonify({
                'success': True, 
                'history': history, 
                'user_profile': profile
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
            return jsonify({
                'success': True, 
                'conversations': list_conversations()
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
            data = request.get_json()
            if not data or not data.get('conversation_name'):
                logger.warning("Delete conversation: No conversation name provided in request.")
                return jsonify({
                    'success': False, 
                    'message': 'Conversation name required'
                }), 400

            conversation_name = data['conversation_name']
            logger.debug(f"Delete conversation: Attempting to delete '{conversation_name}'.")
            
            delete_conversation(conversation_name)
            logger.info(f"Delete conversation: Successfully deleted '{conversation_name}'.")
            return jsonify({
                'success': True, 
                'message': 'Conversation deleted'
            })
        except Exception as e:
            logger.error(f"Delete conversation error for '{conversation_name if 'conversation_name' in locals() else 'unknown'}': {str(e)}", exc_info=True)
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
    print("pip install flask speech-recognition pydub")
    sys.exit(1)
except Exception as e:
    logger.error(f"Fatal startup error: {str(e)}")
    sys.exit(1)