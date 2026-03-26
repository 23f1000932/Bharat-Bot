# 🇮🇳 BharatBot — भारत का AI सहायक

**BharatBot** is a multilingual, multi-agent AI assistant built for rural India. It understands and responds in **7 Indian regional languages** — Hindi, Tamil, Telugu, Kannada, Marathi, Bengali, and Gujarati — across three specialized domains.

| Agent | Domain | Covers |
|---|---|---|
| 🌾 **AgriBot** | Agriculture | Crop diseases, pest control, mandi prices, soil health, ICAR guidelines, govt schemes (PM-KISAN, PMFBY) |
| 🏥 **HealthBot** | Health | Symptom guidance, Ayushman Bharat, AYUSH, National Health Portal resources |
| ⚖️ **LawBot** | Legal Aid | FIR filing, RTI, IPC/CrPC, free legal aid via NALSA, Lok Adalat |

Users type or speak in their native language. BharatBot auto-detects the language, routes to the right agent, and responds in the same language — via web chat or voice.

---

## 🛠️ APIs & Services Used

### 1. Google Gemini API — LLM Backend
- **Model:** `gemini-2.5-flash`
- **Library:** `google-generativeai`
- **Purpose:** Powers all three agents (AgriBot, HealthBot, LawBot) with domain-specific system prompts. Maintains per-conversation history using thread IDs stored in memory.
- **Get Key:** [aistudio.google.com](https://aistudio.google.com/app/apikey)

### 2. Azure Cognitive Services — Speech (STT + TTS)
- **Library:** `azure-cognitiveservices-speech`
- **STT:** Converts uploaded audio (WAV/OGG) to text using language-specific recognition.
- **TTS:** Converts agent responses back to MP3 audio using Azure Neural voices (e.g., `hi-IN-SwaraNeural`, `ta-IN-PallaviNeural`).
- **Supports:** All 7 Indian regional languages with dedicated female neural voices.

### 3. Azure Translator API — Language Detection
- **Endpoint:** `api.cognitive.microsofttranslator.com`
- **Purpose:** Detects the ISO 639-1 language code of incoming text (e.g., `hi`, `ta`, `bn`). Falls back to Hindi if detection fails.

### 4. Azure AI Search — Knowledge Base
- **Library:** `azure-search-documents`
- **Purpose:** Three dedicated search indexes power domain-specific knowledge retrieval:
  - `agribot-knowledge` — crop data, schemes, mandi prices
  - `healthbot-knowledge` — diseases, vaccines, government health schemes
  - `lawbot-knowledge` — FIR, RTI, consumer rights, free legal aid

---

## 🔄 Pipeline & Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                        User Input                           │
│            (Text via browser  OR  Audio via mic)            │
└──────────────────────────┬──────────────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │   [Voice Path Only]     │
              │  Azure Speech STT       │
              │  Audio → Text           │
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │   Azure Translator      │
              │   detect_language()     │
              │   → "hi" / "ta" / ...  │
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │   gateway/router.py     │
              │   classify_intent()     │
              │   Keyword matching in   │
              │   7 languages + English │
              └────────────┬────────────┘
                           │
         ┌─────────────────┼──────────────────┐
         │                 │                  │
    ┌────▼────┐      ┌──────▼─────┐     ┌────▼────┐
    │ AgriBot │      │ HealthBot  │     │ LawBot  │
    │  🌾     │      │    🏥      │     │   ⚖️    │
    └────┬────┘      └──────┬─────┘     └────┬────┘
         └─────────────────┼──────────────────┘
                           │
              ┌────────────▼────────────┐
              │  Google Gemini API      │
              │  gemini-2.5-flash       │
              │  + System Prompt        │
              │  + Conversation History │
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │   [Voice Path Only]     │
              │   Azure Speech TTS      │
              │   Text → MP3 Audio      │
              │   → Base64 for JSON     │
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │       Response          │
              │  { text, audio, agent,  │
              │    language, thread_id }│
              └─────────────────────────┘
```

### Key Design Decisions
- **Intent routing is pure Python** — no API calls, just keyword matching across all 7 languages and English. Fast and zero-cost.
- **Conversation threads** — each session gets a `thread_id` (UUID). History is kept in memory per thread so follow-up questions have context.
- **Language-first** — language detection happens before routing. The agent always responds in the user's detected language.
- **User override** — the frontend lets users manually pick an agent, bypassing the auto-classifier.

---

## 📡 API Endpoints

| Method | Route | Description |
|---|---|---|
| `GET` | `/` | Serves the frontend SPA |
| `GET` | `/health` | Health check — returns service status |
| `POST` | `/chat/text` | Text chat (form data: `message`, `thread_id`, `?agent=`) |
| `POST` | `/chat/voice` | Voice chat (multipart: `audio`, `language`, `thread_id`) |

---

## 🚀 Getting Started — Run Locally

### Prerequisites
- Python 3.11+
- Azure account with:
  - **Azure Cognitive Services — Speech** resource
  - **Azure Translator** resource
  - **Azure AI Search** service
- Google Gemini API key

### 1. Clone the Repository

```bash
git clone https://github.com/23f1000932/Bharat-Bot.git
cd Bharat-Bot
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` and fill in your credentials:

```env
# Google Gemini
GEMINI_API_KEY=your_gemini_api_key

# Azure Speech
SPEECH_KEY=your_azure_speech_key
SPEECH_REGION=centralindia

# Azure Translator
TRANSLATOR_KEY=your_azure_translator_key
TRANSLATOR_ENDPOINT=https://api.cognitive.microsofttranslator.com
TRANSLATOR_REGION=global

# Azure AI Search
SEARCH_ENDPOINT=https://your-search-service.search.windows.net
SEARCH_KEY=your_search_admin_key
SEARCH_INDEX_AGRI=agribot-knowledge
SEARCH_INDEX_HEALTH=healthbot-knowledge
SEARCH_INDEX_LAW=lawbot-knowledge
```

### 5. (Optional) Upload Knowledge Base to Azure AI Search

```bash
python scripts/upload_knowledge.py
```

This seeds all three search indexes with sample documents for agriculture, health, and law domains.

### 6. Run the Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Open the Frontend

Visit **[http://localhost:8000](http://localhost:8000)** in your browser.

---

## 🧪 Test the API with cURL

**Health Check**
```bash
curl http://localhost:8000/health
```

**Text Chat (Hindi)**
```bash
curl -X POST http://localhost:8000/chat/text \
  -F "message=मेरी फसल में पीले पत्ते हो रहे हैं क्या करूं"
```

**Text Chat — Force a specific agent**
```bash
curl -X POST "http://localhost:8000/chat/text?agent=lawbot" \
  -F "message=How do I file an FIR?"
```

**Voice Chat**
```bash
curl -X POST http://localhost:8000/chat/voice \
  -F "audio=@your_audio.wav" \
  -F "language=hi-IN"
```

---

## 📁 Project Structure

```
Bharat-Bot/
├── main.py                  # FastAPI app — all endpoints
├── requirements.txt         # Python dependencies
├── Dockerfile               # Container image definition
├── .env.example             # Environment variable template
├── gateway/
│   ├── router.py            # Pure-Python keyword intent classifier (7 languages)
│   ├── translator.py        # Azure Translator — language detection
│   └── speech.py            # Azure Speech — STT and TTS
├── agents/
│   ├── base_agent.py        # Gemini-powered base class with thread history
│   ├── agribot.py           # Agriculture agent + system prompt
│   ├── healthbot.py         # Health agent + system prompt
│   └── lawbot.py            # Legal agent + system prompt
├── knowledge/
│   └── search.py            # Azure AI Search query helper
├── frontend/
│   └── index.html           # Single-page UI (saffron/white/green theme)
└── scripts/
    └── upload_knowledge.py  # Seeds Azure AI Search with sample documents
```

---

## 🐳 Docker Deployment

```bash
# Build
docker build -t bharatbot:latest .

# Run
docker run -p 8000:8000 --env-file .env bharatbot:latest
```

---

## 📄 License

MIT License — Free to use, modify, and distribute for social good.
