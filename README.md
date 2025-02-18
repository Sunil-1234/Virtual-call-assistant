# Virtual Calling Assistant

An AI-powered virtual calling assistant that handles customer support calls using Twilio, Flask, and Google's Gemini AI. The system converts speech to text, processes queries using a knowledge base, and responds to customers with AI-generated voice responses.

## Features

- 📞 Voice call handling with Twilio
- 🗣️ Speech-to-text conversion
- 🤖 AI-powered responses using Gemini
- 📚 Dynamic knowledge base integration
- 🔊 Text-to-speech response generation
- 📝 Conversation history tracking
- 🔄 Real-time response generation

## Technical Architecture

- **Backend Framework**: Flask
- **Voice Services**: Twilio
- **AI Model**: Google Gemini-Pro
- **Knowledge Base**: FAISS with OpenAI embeddings
- **Text Processing**: LangChain

## Setup Instructions

### Prerequisites
- Python 3.8+
- Twilio Account
- Google Cloud Account (for Gemini AI)
- OpenAI Account (for embeddings)
- ngrok for local development

### Environment Variables
Create a `.env` file with the following:
```
GOOGLE_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token
WEBSITE_URL=your_knowledge_base_url
```

### Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd virtual-calling-assistant
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # For Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Start the Flask server:
```bash
python app.py
```

5. Start ngrok to expose local server:
```bash
ngrok http 5002
```

6. Configure Twilio webhook URL with your ngrok URL

## Twilio Configuration

1. Set up a Twilio account and obtain a phone number
2. Configure the voice webhook URL in Twilio:
   - Method: POST
   - URL: `https://your-ngrok-url/voice`

## System Flow

1. Customer calls the Twilio number
2. Call is received by Flask server
3. Customer's speech is converted to text
4. Text is processed against knowledge base
5. Gemini AI generates appropriate response
6. Response is converted to speech and played back
7. Conversation continues until customer ends call

## Current Limitations

- Limited to single-turn conversations
- Knowledge base needs manual updates
- No authentication system
- Basic error handling
- Limited to English language
- No call recording or analytics

## Future Enhancements

- Multi-turn conversation support
- Dynamic knowledge base updates
- Multi-language support
- Call analytics and reporting
- Sentiment analysis
- Call recording and transcription
- Integration with CRM systems
- Advanced error handling
- Authentication system
- Fallback to human operators

## Troubleshooting

### Common Issues:
1. Webhook errors:
   - Verify ngrok is running
   - Check Twilio webhook configuration
   - Ensure correct auth token

2. Speech recognition issues:
   - Check audio quality
   - Verify Twilio configuration
   - Test with different speech samples

3. AI response issues:
   - Verify API keys
   - Check knowledge base accessibility
   - Monitor API rate limits



## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This is a development project and should be thoroughly tested before any production use. The system may not be suitable for all types of customer support scenarios and should be evaluated based on specific use cases.