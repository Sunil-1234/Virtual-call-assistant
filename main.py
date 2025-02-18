from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client
import google.generativeai as genai
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
import os
from dotenv import load_dotenv
import logging
from functools import wraps
from langchain_community.document_loaders import PyPDFLoader


# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize support system
class CustomerSupport:
    def __init__(self):
        # Initialize Gemini
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        self.model = genai.GenerativeModel('gemini-pro')
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(openai_api_key=os.getenv('OPENAI_API_KEY'))
        
        # Initialize knowledge base
        self.initialize_knowledge_base()
        
        # Store conversations
        self.conversations = {}

# If you want to build knowledge base from pdf then uncomment below function and comment function starting from line 64
    
    # def initialize_knowledge_base(self):
    #     logger.info(f"Loading content from PDF: {self.pdf_path}")
        
    #     try:
    #         # Use PyPDFLoader instead of WebBaseLoader
    #         loader = PyPDFLoader(self.pdf_path)
    #         documents = loader.load()
            
    #         text_splitter = RecursiveCharacterTextSplitter(
    #             chunk_size=1000,
    #             chunk_overlap=200
    #         )
    #         splits = text_splitter.split_documents(documents)
            
    #         self.vectorstore = FAISS.from_documents(splits, self.embeddings)
    #         logger.info("Knowledge base initialized successfully")
            
    #     except Exception as e:
    #         logger.error(f"Error initializing knowledge base: {str(e)}")
    #         raise
    
    # If you want to build knowledge base from scrapping website then use below function otherwise uncomment above function and comment this function

    def initialize_knowledge_base(self):
        website_url = os.getenv('WEBSITE_URL')
        logger.info(f"Loading content from: {website_url}")
        
        try:
            loader = WebBaseLoader(website_url)
            documents = loader.load()
            
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            splits = text_splitter.split_documents(documents)
            
            self.vectorstore = FAISS.from_documents(splits, self.embeddings)
            logger.info("Knowledge base initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing knowledge base: {str(e)}")
            raise

    def get_response(self, query: str, call_sid: str) -> str:
        try:
            relevant_docs = self.vectorstore.similarity_search(query, k=3)
            context = "\n".join([doc.page_content for doc in relevant_docs])
            
            if call_sid not in self.conversations:
                chat = self.model.start_chat(history=[])
                initial_context = """
                You are an AI customer support representative. Your responses should be:
                1. Brief and clear (2-3 sentences maximum)
                2. Professional and friendly
                3. Focused on one key point at a time
                4. Easy to understand over the phone
                """
                chat.send_message(initial_context)
                self.conversations[call_sid] = chat
            else:
                chat = self.conversations[call_sid]
            
            prompt = f"""
            Using this context: {context}
            
            Provide a brief, clear answer to: {query}
            
            Keep your response to 2-3 sentences maximum.
            """
            
            response = chat.send_message(prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I apologize, but I'm having trouble. Let me transfer you to a human agent."

# Initialize Flask app
app = Flask(__name__)

# Initialize support system
support = CustomerSupport()

@app.route("/test", methods=['GET', 'POST'])
def test():
    """Test endpoint"""
    logger.info("Test endpoint hit!")
    return "Test successful!"

from twilio.request_validator import RequestValidator

def validate_twilio_request(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Extensive logging
        logger.error("VALIDATION DEBUG START")
        logger.error(f"Request URL: {request.url}")
        logger.error(f"Request Method: {request.method}")
        logger.error(f"Request Headers: {dict(request.headers)}")
        logger.error(f"Request Form Data: {dict(request.form)}")
        logger.error(f"Twilio Signature: {request.headers.get('X-TWILIO-SIGNATURE', 'No Signature')}")
        
        try:
            # More lenient validation
            validator = RequestValidator(os.getenv('TWILIO_AUTH_TOKEN'))
            
            # Log the exact validation parameters
            logger.error(f"Validation Params:")
            logger.error(f"URL: {request.url}")
            logger.error(f"Form Data: {dict(request.form)}")
            logger.error(f"Auth Token: {os.getenv('TWILIO_AUTH_TOKEN')[:4]}...{os.getenv('TWILIO_AUTH_TOKEN')[-4:]}")
            
            request_valid = validator.validate(
                request.url,
                request.form,
                request.headers.get('X-TWILIO-SIGNATURE', '')
            )
            
            logger.error(f"Request Validation Result: {request_valid}")
            
            # More permissive validation
            if request_valid or request.headers.get('X-Forwarded-Proto', 'http') == 'https':
                return f(*args, **kwargs)
            else:
                logger.error("Request validation failed")
                return 'Invalid request', 403
        
        except Exception as e:
            logger.error(f"VALIDATION EXCEPTION: {str(e)}")
            return 'Validation error', 500
    
    return decorated_function

# Add more robust error handling in your main routes
@app.route("/answer", methods=['POST'])
@validate_twilio_request
def answer_call():
    logger.info("Answer endpoint hit!")
    logger.info(f"Request values: {request.values}")
    
    response = VoiceResponse()
    response.say("Welcome to Oracle support. Please speak your question after the beep.", voice='alice')
    response.pause(length=1)
    
    gather = Gather(
        input='speech',
        action='/handle-response',
        timeout=5,
        speech_timeout='auto'
    )
    response.append(gather)
    
    logger.info("Sending initial response")
    return str(response)

@app.route("/handle-response", methods=['POST'])
def handle_response():
    logger.info(f"Handle response hit with values: {request.values}")
    response = VoiceResponse()
    
    speech_result = request.values.get('SpeechResult')
    call_sid = request.values.get('CallSid')
    
    if speech_result:
        logger.info(f"Received speech: {speech_result}")
        
        try:
            # Use your CustomerSupport class to get AI response
            ai_response = support.get_response(speech_result, call_sid)
            logger.info(f"AI response: {ai_response}")
            
            # Speak the AI response
            response.say(ai_response, voice='alice')
            response.pause(length=2)
            
            # Prepare for next input
            gather = Gather(
                input='speech',
                action='/handle-response',
                timeout=5,
                speech_timeout='auto'
            )
            response.append(gather)
        
        except Exception as e:
            logger.error(f"Error processing response: {e}")
            response.say("I'm sorry, I couldn't process your request. Please try again.", voice='alice')
            
            # Retry gather
            gather = Gather(
                input='speech',
                action='/handle-response',
                timeout=5,
                speech_timeout='auto'
            )
            response.append(gather)
    else:
        logger.info("No speech detected")
        response.say("I didn't hear anything. Please speak clearly.", voice='alice')
        
        # Retry gather
        gather = Gather(
            input='speech',
            action='/handle-response',
            timeout=5,
            speech_timeout='auto'
        )
        response.append(gather)
    
    return str(response)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# In your app.py or main.py
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)