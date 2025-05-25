"""
Gemini AI Service - Integration with Google Gemini API
Handles text and image-based AI interactions with proper error handling
"""

import google.generativeai as genai
from PIL import Image
import io
import base64
from typing import Optional, Dict, Any
from config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiService:
    """Service class for interacting with Google Gemini AI"""
    
    def __init__(self):
        """Initialize Gemini service with API key"""
        genai.configure(api_key=settings.google_api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        self.vision_model = genai.GenerativeModel('gemini-pro-vision')
    
    async def generate_text_response(self, message: str, context: Optional[str] = None) -> str:
        """
        Generate text response from Gemini
        
        Args:
            message: User's message
            context: Optional conversation context
            
        Returns:
            Generated response text
        """
        try:
            # Prepare prompt with context if available
            if context:
                prompt = f"Context: {context}\n\nUser: {message}\n\nAssistant:"
            else:
                prompt = message
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            if response.text:
                return response.text.strip()
            else:
                return "I apologize, but I couldn't generate a response. Please try again."
                
        except Exception as e:
            logger.error(f"Error generating text response: {str(e)}")
            raise Exception(f"Failed to generate response: {str(e)}")
    
    async def generate_image_response(self, message: str, image_data: str) -> str:
        """
        Generate response for image + text input
        
        Args:
            message: User's message about the image
            image_data: Base64 encoded image data
            
        Returns:
            Generated response text
        """
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_data.split(',')[1] if ',' in image_data else image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Prepare prompt
            prompt = f"Please analyze this image and respond to: {message}"
            
            # Generate response with image
            response = self.vision_model.generate_content([prompt, image])
            
            if response.text:
                return response.text.strip()
            else:
                return "I can see the image, but I couldn't generate a specific response. Please try rephrasing your question."
                
        except Exception as e:
            logger.error(f"Error generating image response: {str(e)}")
            raise Exception(f"Failed to analyze image: {str(e)}")
    
    async def generate_response(self, message: str, image_data: Optional[str] = None, 
                              context: Optional[str] = None) -> str:
        """
        Main method to generate response (with or without image)
        
        Args:
            message: User's message
            image_data: Optional base64 encoded image
            context: Optional conversation context
            
        Returns:
            Generated response text
        """
        try:
            if image_data:
                return await self.generate_image_response(message, image_data)
            else:
                return await self.generate_text_response(message, context)
                
        except Exception as e:
            logger.error(f"Error in generate_response: {str(e)}")
            # Return a user-friendly error message
            return "I'm experiencing some technical difficulties right now. Please try again in a moment."
    
    def validate_image(self, image_data: str) -> bool:
        """
        Validate if the provided image data is valid
        
        Args:
            image_data: Base64 encoded image data
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Remove data URL prefix if present
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            # Decode and validate
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Check image format
            if image.format not in ['JPEG', 'PNG', 'GIF', 'WEBP']:
                return False
            
            # Check image size (max 10MB)
            if len(image_bytes) > 10 * 1024 * 1024:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Image validation error: {str(e)}")
            return False
    
    def get_conversation_context(self, messages: list, max_messages: int = 5) -> str:
        """
        Build conversation context from recent messages
        
        Args:
            messages: List of recent messages
            max_messages: Maximum number of messages to include
            
        Returns:
            Formatted context string
        """
        try:
            if not messages:
                return ""
            
            # Take last max_messages
            recent_messages = messages[-max_messages:]
            
            context_parts = []
            for msg in recent_messages:
                role = "User" if msg.get('role') == 'user' else "Assistant"
                content = msg.get('content', '')[:200]  # Limit content length
                context_parts.append(f"{role}: {content}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error building context: {str(e)}")
            return ""

# Create global instance
gemini_service = GeminiService() 