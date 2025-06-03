"""
Google Gemini AI Service - AI response generation and image processing
Handles communication with Google's Gemini AI API for text and image processing
"""

import google.generativeai as genai
import base64
import io
from PIL import Image
from typing import List, Dict, Optional
from utils.env_utils import get_env_str, get_env_int, get_env_bool
from utils.logging_config import get_logger

logger = get_logger(__name__)

class GeminiService:
    """Service for interacting with Google Gemini AI"""
    
    def __init__(self):
        # Environment variables
        self.api_key = get_env_str("GOOGLE_API_KEY", "")
        self.model_name = get_env_str("GEMINI_MODEL", "gemini-1.5-flash")
        self.max_tokens = get_env_int("GEMINI_MAX_TOKENS", 2048)
        self.temperature = float(get_env_str("GEMINI_TEMPERATURE", "0.7"))
        self.safety_enabled = get_env_bool("GEMINI_SAFETY_ENABLED", True)
        self.max_image_size = get_env_int("MAX_IMAGE_SIZE", 4194304)  # 4MB
        
        if not self.api_key:
            logger.error("Google API key not configured")
            raise ValueError("Google API key is required")
        
        # Configure the API
        genai.configure(api_key=self.api_key)
        
        # Initialize the model
        try:
            generation_config = {
                "temperature": self.temperature,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": self.max_tokens,
            }
            
            safety_settings = []
            if self.safety_enabled:
                safety_settings = [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                ]
            
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            logger.info(f"Gemini service initialized with model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            raise
    
    def validate_image(self, image_data: str) -> bool:
        """Validate base64 image data"""
        try:
            if not image_data or not image_data.startswith('data:image/'):
                return False
            
            # Extract base64 data
            header, data = image_data.split(',', 1)
            image_bytes = base64.b64decode(data)
            
            # Check file size
            if len(image_bytes) > self.max_image_size:
                logger.warning(f"Image too large: {len(image_bytes)} bytes")
                return False
            
            # Validate image format
            try:
                image = Image.open(io.BytesIO(image_bytes))
                image.verify()
                return True
            except Exception as e:
                logger.warning(f"Invalid image format: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Image validation error: {e}")
            return False
    
    def process_image(self, image_data: str) -> Optional[Image.Image]:
        """Process base64 image data for Gemini"""
        try:
            if not self.validate_image(image_data):
                return None
            
            # Extract base64 data
            header, data = image_data.split(',', 1)
            image_bytes = base64.b64decode(data)
            
            # Open and process image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large (max 2048x2048)
            max_size = get_env_int("MAX_IMAGE_DIMENSION", 2048)
            if image.width > max_size or image.height > max_size:
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                logger.info(f"Image resized to {image.width}x{image.height}")
            
            return image
            
        except Exception as e:
            logger.error(f"Image processing error: {e}")
            return None
    
    async def generate_response(
        self, 
        message: str, 
        image_data: Optional[str] = None,
        context: Optional[str] = None
    ) -> str:
        """Generate AI response using Gemini"""
        try:
            # Prepare the prompt
            prompt_parts = []
            
            # Add context if provided
            if context:
                prompt_parts.append(f"Context: {context}\n\n")
            
            # Add the main message
            prompt_parts.append(message)
            
            # Process image if provided
            if image_data:
                image = self.process_image(image_data)
                if image:
                    prompt_parts.append(image)
                    logger.info("Image added to prompt")
                else:
                    logger.warning("Failed to process image, continuing with text only")
            
            # Generate response
            response = self.model.generate_content(prompt_parts)
            
            if response.text:
                logger.info("Successfully generated AI response")
                return response.text
            else:
                logger.warning("Empty response from Gemini")
                return "I apologize, but I couldn't generate a response. Please try again."
                
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return f"I encountered an error while processing your request. Please try again later."
    
    def get_conversation_context(self, messages: List[Dict[str, str]], max_context: int = None) -> str:
        """Build conversation context from recent messages"""
        if not messages:
            return ""
        
        if max_context is None:
            max_context = get_env_int("MAX_CONTEXT_MESSAGES", 5)
        
        # Take the most recent messages
        recent_messages = messages[-max_context:] if len(messages) > max_context else messages
        
        context_parts = []
        for msg in recent_messages:
            role = "Human" if msg["role"] == "user" else "Assistant"
            context_parts.append(f"{role}: {msg['content']}")
        
        return "\n".join(context_parts)
    
    def get_model_info(self) -> Dict[str, any]:
        """Get information about the current model"""
        return {
            "model_name": self.model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "safety_enabled": self.safety_enabled,
            "max_image_size": self.max_image_size
        }

# Global service instance
gemini_service = GeminiService() 