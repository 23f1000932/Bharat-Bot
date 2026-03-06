# Bharat-Bot 🇮🇳

**Bharat-Bot** is a multilingual conversational AI assistant designed to serve as a digital companion for Indian users. Built with cutting-edge AI technologies, it provides instant information and support across multiple domains in the user's preferred language.

## 🌟 Key Features

- **Multilingual Support**:
  - Speaks and understands 7 Indian languages: Hindi, English, Marathi, Bengali, Tamil, Telugu, and Gujarati.
  - Automatically detects the user's language for seamless interaction.

- **Domain-Specific Expertise**:
  - **Agriculture Bot**: Expert advice on farming, crops, and soil health.
  - **Health Bot**: General wellness information and first-aid guidance.
  - **Law Bot**: Legal information and rights awareness.

- **Advanced AI Stack**:
  - **LLM Backend**: Powered by **Google Gemini** for intelligent reasoning and natural conversation.
  - **Speech-to-Text**: Uses **Azure Cognitive Services** for high-accuracy voice recognition.
  - **Text-to-Speech**: Converts text to natural-sounding speech using **Azure Neural Voices**.
  - **Knowledge Base**: Leverages **Azure AI Search** for fast and relevant information retrieval.

- **WhatsApp Integration**:
  - Seamlessly deployable as a WhatsApp bot via the **Meta Business API**.

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip package manager

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Bharat-Bot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Configuration**:
   Create a `.env` file in the root directory with the following credentials:
   ```env
   # Google Gemini API
   GEMINI_API_KEY=your_gemini_key

   # Azure Speech Services
   SPEECH_KEY=your_speech_key
   SPEECH_REGION=centralindia

   # Azure Translator
   TRANSLATOR_KEY=your_translator_key
   TRANSLATOR_ENDPOINT=https://api.cognitive.microsofttranslator.com
   TRANSLATOR_REGION=global

   # Azure AI Search
   SEARCH_ENDPOINT=your_search_endpoint
   SEARCH_KEY=your_search_key
   SEARCH_INDEX_AGRI=agribot-knowledge
   SEARCH_INDEX_HEALTH=healthbot-knowledge
   SEARCH_INDEX_LAW=lawbot-knowledge

   # WhatsApp (Optional)
   WA_TOKEN=your_wa_token
   WA_PHONE_ID=your_phone_id
   WA_VERIFY_TOKEN=your_verify_token
   ```

### Running the Server

Start the FastAPI server using uvicorn:

```bash
uvicorn bharatbot.main:app --reload
```

The API will be available at `http://localhost:8000`.

## 🛠️ API Endpoints

### Health Check
```http
GET /health
```
Returns the status of the bot and its integrations.

### Chat with Bharat-Bot
```http
POST /chat
```
**Request Body:**
```json
{
  "text": "नमस्ते, मुझे फसल के बारे में सलाह चाहिए।",
  "language": "hi-IN"
}
```

**Response:**
```json
{
  "response": "नमस्ते! मैं आपकी कैसे मदद कर सकता हूँ?",
  "language": "hi-IN"
}
```

### Voice Chat (STT + TTS)
```http
POST /chat/voice
```
**Request Body:**
```json
{
  "audio": "base64_encoded_audio_data",
  "language": "hi-IN"
}
```

**Response:**
```json
{
  "text": "नमस्ते! मैं आपकी कैसे मदद कर सकता हूँ?",
  "audio": "base64_encoded_audio_response"
}
```

## 📂 Project Structure

```
bharatbot/
├── main.py             # FastAPI application entry point
├── gateway/            # API gateways and integrations
│   ├── gemini.py       # Google Gemini LLM integration
│   ├── speech.py       # Azure Speech-to-Text & Text-to-Speech
│   ├── translator.py   # Azure Language Detection
│   └── search.py       # Azure AI Search
├── models/             # Data models and schemas
├── services/           # Business logic and domain services
└── utils/              # Utility functions
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.