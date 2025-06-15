import sys
import threading
import tkinter as tk
from pathlib import Path
import json
from scheduler import Scheduler
from chatbot import respond_to_query
from gui import AIPersonalAssistantGUI
from utils import load_config, print_assistant, print_error, print_warning

def show_welcome_menu():
    menu = [
        "\n🧘 Welcome to your Well-being Companion! 🧘",
        "I'm here to support your mental and emotional well-being. Feel free to talk to me about anything.",
        "\n🌟 Quick Actions:",
        f"1️⃣  Start a guided breathing exercise",
        f"2️⃣  Switch to GUI mode",
        "0️⃣  Exit",
        "\nOr just start chatting with me about your feelings or day!"
    ]
    return menu

def handle_option(option, config, conversation_history: list, user_profile: dict):
    """Handles user options in CLI mode."""
    lang = config.get('default_language', 'en')
    
    if option == "1": # Start breathing exercise
        response, conversation_history, user_profile = respond_to_query("start breathing exercise", {'current_language': lang}, conversation_history, user_profile)
        print_assistant(response)
        return response, conversation_history, user_profile
    elif option == "2": # Switch to GUI mode
        print_assistant("Switching to GUI mode...")
        run_gui()
        return None, conversation_history, user_profile
    elif option == "0": # Exit
        print_assistant("Exiting...")
        sys.exit()
    else:
        response, updated_history, updated_user_profile = respond_to_query(option, {
            'current_language': lang,
            'gemini_api_key': config['gemini_api_key']
        }, conversation_history, user_profile)
        return response, updated_history, updated_user_profile

def run_cli(config):
    """Runs the CLI mode of the assistant."""
    conversation_history = [] # Initialize conversation history for the CLI session
    user_profile = {} # Initialize user profile for the CLI session
    
    while True:
        current_lang = config.get('default_language', 'en')
        menu = show_welcome_menu()
        
        for line in menu:
            print(line)

        prompt = "\n😊 How can I support you today? (Or choose an option 0-2): "
        user_input = input(prompt).strip()
        
        # Check if the input is a numeric option for meta-commands or breathing exercise
        if user_input.isdigit() and int(user_input) in range(0, 3):
            response_from_option, conversation_history, user_profile = handle_option(user_input, config, conversation_history, user_profile)
            if response_from_option:
                print_assistant(response_from_option)
        else:
            # Treat as a conversational query and pass/update the conversation history and user profile
            response, conversation_history, user_profile = respond_to_query(user_input, {
                'current_language': current_lang,
                'gemini_api_key': config['gemini_api_key']
            }, conversation_history, user_profile) # Pass the existing history and user profile
            print_assistant(response)

def run_gui():
    """Runs the GUI mode of the assistant."""
    try:
        root = tk.Tk()
        app = AIPersonalAssistantGUI(root, load_config())
        root.mainloop()
    except Exception as e:
        print_error(f"GUI Error: {str(e)}")
        run_cli(load_config())

def main():
    """Main function to start the assistant."""
    config = load_config()
    print_assistant("Starting your Well-being Companion...")
    
    run_cli(config)

if __name__ == "__main__":
    main()
