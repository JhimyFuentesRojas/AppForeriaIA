"""Servicio de IA centralizado para interactuar con Groq"""

import os
from openai import OpenAI
from flask import current_app

class AIService:
    def __init__(self):
        self.client = None
        self.model = 'llama-3.1-8b-instant'

    def _init_client(self):
        """Inicializa el cliente de Groq si no está inicializado"""
        if self.client is None:
            # Obtiene la API key de la configuración de Flask si está disponible, sino del entorno
            api_key = current_app.config.get('GROQ_API_KEY') if current_app else os.environ.get('GROQ_API_KEY')
            
            if current_app:
                self.model = current_app.config.get('GROQ_MODEL', 'llama-3.1-8b-instant')
            
            if not api_key:
                raise ValueError("GROQ_API_KEY no está configurada")
                
            self.client = OpenAI(
                api_key=api_key,
                base_url='https://api.groq.com/openai/v1'
            )

    def obtener_respuesta(self, messages, temperature=0.7, response_format=None):
        """
        Envía mensajes a Groq y obtiene una respuesta
        
        Args:
            messages (list): Lista de diccionarios con 'role' y 'content'
            temperature (float): Temperatura de la respuesta (0.0 a 2.0)
            response_format (dict): Formato de respuesta deseado, ej. {"type": "json_object"}
            
        Returns:
            str: Contenido de la respuesta
        """
        self._init_client()
        
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature
            }
            if response_format:
                kwargs["response_format"] = response_format
                
            respuesta = self.client.chat.completions.create(**kwargs)
            return respuesta.choices[0].message.content
        except Exception as e:
            current_app.logger.error(f"Error al llamar a Groq API: {str(e)}")
            return f"{{\"error\": \"Lo siento, encontré un error al procesar tu solicitud: {str(e)}\"}}"

# Instancia global para usar en toda la aplicación
ai_service = AIService()
