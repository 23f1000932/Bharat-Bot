# 🇮🇳 BharatBot – भारत का AI सहायक

**BharatBot** is a multilingual, multi-agent AI assistant designed for rural India. It answers questions in **7 Indian regional languages** (Hindi, Tamil, Telugu, Kannada, Marathi, Bengali, Gujarati) across three domains:

| Agent | Domain | Use Cases |
|-------|--------|-----------|
| 🌾 **AgriBot** | Agriculture | Crop diseases, pest control, mandi prices, ICAR guidelines, govt schemes |
| 🏥 **HealthBot** | Health | Symptom guidance, Ayushman Bharat, AYUSH, NHP India resources |
| ⚖️ **LawBot** | Legal | FIR filing, RTI, IPC/CrPC, free legal aid (NALSA), Lok Adalat |

Users speak or type in their native language. BharatBot automatically detects the language, routes to the correct agent, and responds in the same language — via web chat, voice, or WhatsApp.

Built on **Azure AI Foundry (GPT-4o-mini)**, **Azure Speech SDK**, **Azure Translator**, and **Azure AI Search**, with a **FastAPI** backend and a mobile-friendly single-page frontend.

---

## Prerequisites

- Python 3.11+
- Azure subscription with the following resources:
  - Azure OpenAI (GPT-4o-mini deployment)
  - Azure AI Foundry Project (for Agent Service)
  - Azure Cognitive Services – Speech
  - Azure Translator
  - Azure AI Search
- (Optional) Meta WhatsApp Cloud API access for WhatsApp integration
- Docker (for containerised deployment)
- ngrok (for local WhatsApp webhook testing)

---

## Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-org/bharatbot.git
cd bharatbot

# 2. Copy and fill in environment variables
cp .env.example .env
# Open .env in your editor and fill in all Azure credentials

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Run the development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 5. Open the frontend
# Visit http://localhost:8000 in your browser
```

---

## Creating Foundry Agents in Azure

1. Go to **[Azure AI Studio](https://ai.azure.com)** → your project.
2. Click **Agents** in the left sidebar → **+ New Agent**.
3. Create three agents:
   - **AgriBot**: Set the system prompt from `agents/agribot.py > SYSTEM_PROMPT`
   - **HealthBot**: System prompt from `agents/healthbot.py > SYSTEM_PROMPT`
   - **LawBot**: System prompt from `agents/lawbot.py > SYSTEM_PROMPT`
4. Copy each agent's **Agent ID** (format: `asst_xxxxxxxxxxxx`).
5. Add the IDs to your `.env` file:
   ```
   AGRIBOT_AGENT_ID=asst_xxxx
   HEALTHBOT_AGENT_ID=asst_xxxx
   LAWBOT_AGENT_ID=asst_xxxx
   ```

> **Note:** If Foundry Agent IDs are not set, BharatBot automatically falls back to direct Azure OpenAI API calls using the same system prompts.

---

## Uploading Knowledge Base

```bash
# Make sure SEARCH_ENDPOINT and SEARCH_KEY are set in .env first
python scripts/upload_knowledge.py
```

This creates three Azure AI Search indexes and uploads sample documents:
- `agribot-knowledge` – Crop diseases, schemes, mandi prices
- `healthbot-knowledge` – Diseases, vaccines, govt schemes
- `lawbot-knowledge` – FIR, RTI, consumer rights, free legal aid

---

## Testing Endpoints with cURL

### Health Check
```bash
curl http://localhost:8000/health
```

### Text Chat
```bash
curl -X POST http://localhost:8000/chat/text \
  -F "message=मेरी फसल में पीले पत्ते हो रहे हैं क्या करूं" \
  -F "thread_id="
```

### Voice Chat (send WAV/WebM file)
```bash
curl -X POST http://localhost:8000/chat/voice \
  -F "audio=@your_audio.wav" \
  -F "language=hi-IN"
```

### WhatsApp Webhook Verification
```bash
curl "http://localhost:8000/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=bharatbot_webhook_2024&hub.challenge=test123"
```

---

## WhatsApp Webhook with ngrok

```bash
# 1. Start BharatBot locally
uvicorn main:app --host 0.0.0.0 --port 8000

# 2. In a new terminal, start ngrok
ngrok http 8000

# 3. Copy the ngrok HTTPS URL (e.g. https://abc123.ngrok.io)

# 4. In the Meta Developers console:
#    App → WhatsApp → Configuration → Webhook URL:
#    https://abc123.ngrok.io/webhook/whatsapp
#    Verify Token: bharatbot_webhook_2024

# 5. Subscribe to "messages" webhook field
```

---

## Docker Deployment

```bash
# Build the image
docker build -t bharatbot:latest .

# Run locally with Docker
docker run -p 8000:8000 --env-file .env bharatbot:latest

# Push to Azure Container Registry
az acr build --registry <your-registry> --image bharatbot:latest .

# Deploy to Azure Container Apps
az containerapp create \
  --name bharatbot \
  --resource-group <your-rg> \
  --environment <your-env> \
  --image <your-registry>.azurecr.io/bharatbot:latest \
  --target-port 8000 \
  --ingress external \
  --env-vars-from-file .env
```

---

## Project Structure

```
bharatbot/
├── main.py                  # FastAPI application (all endpoints)
├── requirements.txt         
├── Dockerfile               
├── .env.example             # Template for environment variables
├── gateway/
│   ├── translator.py        # Azure Translator – language detection & translation
│   ├── speech.py            # Azure Speech – STT and TTS
│   └── router.py            # Keyword-based intent classifier (pure Python)
├── agents/
│   ├── base_agent.py        # Azure Foundry + OpenAI fallback base class
│   ├── agribot.py           # Agriculture agent
│   ├── healthbot.py         # Health agent
│   └── lawbot.py            # Legal agent
├── knowledge/
│   └── search.py            # Azure AI Search query helper
├── webhooks/
│   └── whatsapp.py          # Meta WhatsApp Cloud API handler
├── frontend/
│   └── index.html           # Single-page UI (saffron/white/green theme)
└── scripts/
    └── upload_knowledge.py  # Seed Azure AI Search with sample documents
```

---

## License

MIT License – Free to use, modify, and distribute for social good.
