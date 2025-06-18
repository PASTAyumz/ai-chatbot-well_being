# Well-being Companion Chatbot 

## Table of Contents
- [About This Project](#about-this-project)
- [Features](#features)
- [Installation and Setup](#installation-and-setup)
  - [Prerequisites](#prerequisites)
  - [Environment Variables](#environment-variables)
  - [Running the Application](#running-the-application)
- [Usage](#usage)
- [What Makes it Wonderful?](#what-makes-it-wonderful)
- [Future Enhancements](#future-enhancements)
- [Troubleshooting](#troubleshooting)


## About This Project
![Capture d'écran 2025-06-18 191235](https://github.com/user-attachments/assets/c7391af7-15f0-4417-9524-19d996953b38)


The Well-being Companion Chatbot is an AI-powered conversational agent designed to provide emotional support and engage in meaningful interactions focused on mental and emotional well-being. Built with Flask for the web interface and leveraging Google's Gemini models, it offers a personalized and private chat experience.

## Features

- **AI-Powered Conversations:** Utilizes advanced large language models (Google Gemini 1.5 Flash) to provide empathetic and supportive responses.
- **User Privacy:** Designed with user privacy in mind, ensuring that individual conversation histories are kept separate and private.
- **Audio Input (Speech-to-Text):** Allows users to interact with the chatbot using their voice, converting speech to text for seamless communication (requires HTTPS for mobile browsers).
- **Conversation Management:** Users can start new chats, load previous conversations, view a list of their saved conversations, and delete specific conversation histories.
- **Guided Breathing Exercises:** Offers a structured, guided breathing exercise to help users relax and manage stress.
- **Mood Analysis (Planned):** Future capabilities may include analyzing user sentiment to tailor responses more effectively.
- **Responsive Web Interface:** A user-friendly web interface built with HTML, CSS, and JavaScript, designed for a smooth experience across various devices.
- **Conversation Persistence:** User conversation data is stored to maintain continuity across sessions. **Note: For production deployment, a robust, persistent database solution is recommended for data integrity and scalability.**

## Installation and Setup

Follow these steps to get your Well-being Companion Chatbot up and running locally.

### Prerequisites

- Python 3.8+
- `pip` (Python package installer)
- FFmpeg: Essential for audio transcription.
  - **Windows:** Download a pre-built binary from [ffmpeg.org/download.html](https://ffmpeg.org/download.html) and extract it. Update the `ffmpeg_bin_path` in `web_app.py` to point to the `bin` directory within your FFmpeg installation.
  - **macOS:** `brew install ffmpeg`
  - **Linux:** `sudo apt update && sudo apt install ffmpeg`

### Environment Variables

Create a `.env` file in the root directory of your project and add the following:

```
GEMINI_API_KEY="YOUR_GOOGLE_GEMINI_API_KEY"
TWINWORD_API_KEY="YOUR_TWINWORD_RAPIDAPI_KEY"
```

-   **`GEMINI_API_KEY`**: Obtain this from the [Google AI Studio](https://aistudio.google.com/app/apikey).
-   **`FLASK_SECRET_KEY`**: Generate a strong, random string for Flask session security (e.g., using `secrets.token_urlsafe(32)` in Python). For deployment on platforms like Render, ensure this is set as an environment variable in your service settings.
-   **`TWINWORD_API_KEY`**: Obtain this from [RapidAPI](https://rapidapi.com/twinword/api/twinword-sentiment-analysis). You will need to sign up for an account and subscribe to the Twinword Sentiment Analysis API to get your key.

### Running the Application

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/PASTAyumz/ai-chatbot-well_being.git
    cd ai-chatbot-well_being
    ```
    (Note: If you are already in the project directory, skip `git clone` and `cd`.)

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    (A `requirements.txt` file is needed for this. If it's missing, you can create it with `pip freeze > requirements.txt` after installing dependencies.)
    The necessary packages are likely: `flask`, `whisper-openai`, `python-dotenv`, `google-generativeai`, `textblob`, `requests`.

3.  **Start the Flask application:**
    ```bash
    python web_app.py
    ```

## Usage

-   **Chat:** Type your messages in the input box and press Enter or click the send button.
-   **Voice Input:** Click the microphone icon to start/stop recording your voice. Your speech will be transcribed and sent to the chatbot.
-   **Breathing Exercise:** Click the "Start Breathing Exercise" button to receive guided steps for relaxation.
-   **Conversation History:** Use the sidebar menu (toggle button in the header) to view, load, or delete previous conversations.
-   **New Chat:** Click the "New Chat" button in the sidebar to start a fresh conversation.

## What Makes it Wonderful?

This chatbot stands out as a wonderful companion due to its focus on **well-being and privacy**. Unlike many general-purpose chatbots, it's specifically tailored to offer empathetic and supportive interactions. The key wonderful aspects include:

-   **Genuine Empathy (AI-driven):** Powered by Gemini, it strives to understand and respond to user emotions with care and appropriate support, making conversations feel more natural and helpful for mental wellness.
-   **Unwavering Privacy:** The chatbot respects user privacy, providing a confidential and secure environment for personal interactions.
-   **Accessibility through Voice:** Voice input makes it highly accessible and convenient, allowing users to interact naturally without typing, which is particularly beneficial for those who prefer speaking their thoughts.
-   **Ease of Use:** The simple and intuitive web interface, combined with features like conversation management and guided exercises, makes it easy for anyone to engage with and benefit from the companion.
-   **Continuous Improvement:** As an AI, it's designed to continuously improve based on interactions (though this project focuses on foundational interaction rather than direct model retraining from user input).

It's designed to be a supportive digital friend, available whenever needed, offering a judgment-free space to explore thoughts and feelings.

## Future Enhancements
-   **Mood Analysis Integration:** Enhance the chatbot with more sophisticated mood detection and tailored conversational flows based on user sentiment.
-   **User Authentication:** Implement user accounts and login for more personalized experiences and potentially richer profile management.
-   **Broader Well-being Tools:** Add more guided exercises, journaling features, or connections to external well-being resources.
-   **Speech Synthesis (Text-to-Speech):** Allow the chatbot to speak its responses back to the user for an even more immersive voice experience.
-   **Frontend Refinements:** Enhance the UI/UX for a more polished and engaging user experience.

## Troubleshooting

-   **"Error accessing microphone: NotAllowedError" or "PermissionDeniedError" on mobile (especially iOS):** Ensure your deployed website is accessed via **HTTPS**. Microphone access is a sensitive feature usually restricted to secure contexts.
-   **"ModuleNotFoundError: No module named..."**: Ensure all dependencies are installed (`pip install -r requirements.txt`).
-   **"404 models/gemini-pro is not found..."**: Update the `chat_model_name` and `title_model_name` in `web_app.py` to use a model name available to your API key (e.g., `gemini-1.5-flash`). Refer to the console output when the app starts for a list of available models.
-   **FFmpeg related errors:** Verify that FFmpeg is installed and that the `ffmpeg_bin_path` in `web_app.py` is correctly set to your FFmpeg `bin` directory.
-   **"I encountered an error: module 'google.api_core.exceptions' has no attribute 'BlockedPromptException'"**: Ensure `BlockedPromptException` is imported directly from `google.generativeai.types` in `Core/chatbot.py`.
-   **Git Issues (merge conflicts, unable to push/pull)**: Follow standard Git conflict resolution. For stubborn issues, consider stashing local changes, performing a `git reset --hard origin/main`, reapplying the stash, and then pushing. Ensure `.gitignore` correctly lists `debug.log`, `Core/conversation_memory.json`, `Core/main_backup.py`, and `flask_session/`.

