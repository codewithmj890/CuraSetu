import os
import google.generativeai as genai
from django.conf import settings

class GeminiService:
    def __init__(self):
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY', 'AIzaSyC-c1x6QcroM1y3PxUELsCcsNtnJlSyTOo'))
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def get_health_advice(self, symptoms):
        prompt = f"""
        You are a healthcare assistant specializing in minor diseases common in India. 
        Based on the symptoms provided, identify the most likely minor illness and provide both generic and traditional Indian (desi) remedies.
        
        Symptoms: {symptoms}
        
        Please respond in the following format:
        
        **Expected Disease:** [Disease Name]
        
        **Generic Cure:**
        - [Generic remedy 1]
        - [Generic remedy 2]
        - [Generic remedy 3]
        
        **Desi Cure:**
        - [Traditional remedy 1]
        - [Traditional remedy 2]
        - [Traditional remedy 3]
        
        Important: Only suggest remedies for minor ailments. If symptoms suggest a serious condition, recommend consulting a doctor immediately.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Sorry, I couldn't process your request at the moment. Please try again later. Error: {str(e)}"