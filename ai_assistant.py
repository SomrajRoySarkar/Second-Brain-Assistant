import cohere
from config import COHERE_API_KEY
from database import SecondBrainDB
from datetime import datetime
import json
import random
import re
from google_search import google_search
import threading
import dateparser
import pytz
import requests
from googletrans import Translator
import os
from dotenv import load_dotenv
load_dotenv()

CITY = os.getenv('CITY', 'your_city')
PLACE = os.getenv('PLACE', 'your_place')
LATITUDE = os.getenv('LATITUDE', None)
LONGITUDE = os.getenv('LONGITUDE', None)

class SecondBrainAssistant:
    def __init__(self):
        self.co = cohere.Client(COHERE_API_KEY)
        self.db = SecondBrainDB()
        self.conversation_history = []
        self.system_prompt = """You are a friendly and helpful assistant. Your main goal is to provide clear, complete answers in a natural, conversational way.\n\n**Core Instructions:**\n1.  **Simple and Clear:** Use easy-to-understand words. Avoid jargon or complex vocabulary.\n2.  **Full Sentences:** Always use grammatically correct, complete sentences. For example, instead of just "Paris," say, "The capital of France is Paris."\n3.  **Friendly Tone:** Be approachable and conversational, like a real person.\n4.  **Be Concise:** Keep your answers brief and to the point (usually 2-3 sentences).\n5.  **Directly Answer:** Always address the user's question directly.\n\n**Example:**\n*   **User:** what's the time and how are you\n*   **Good Response:** "I'm doing well, thanks for asking! The current time is 3:15 PM."\n*   **Bad Response:** "3:15 PM. I am an AI."\n\nYour primary goal is to be helpful, clear, and friendly."""
        self.greeting_responses = [
            "Hey.",
            "Hey! Everything okay?",
            "Yo.",
            "Hi there.",
            "Hello!",
            "Hey, what's up?",
            "Hey, how's it going?",
            "Hi!",
            "Hey, you good?",
            "Hey, how are you?"
        ]
        self.last_greeting = None
    
    def get_context(self):
        """Build context from recent conversations and memories"""
        context_parts = []
        # Get recent conversations
        recent_conversations = self.db.get_recent_conversations(5)
        if recent_conversations:
            context_parts.append("Recent conversations:")
            for conv in recent_conversations:
                context_parts.append(f"User: {conv[0]}")
                context_parts.append(f"Assistant: {conv[1]}")
        # Get important memories
        memories = self.db.get_memories(limit=10)
        if memories:
            context_parts.append("\nImportant memories:")
            for memory in memories:
                context_parts.append(f"- {memory[1]}")  # memory[1] is content
        return "\\n".join(context_parts)
    
    def split_into_questions(self, user_message):
        """
        Uses the language model to split a user's message into distinct questions or statements.
        """
        # A simple heuristic to avoid an API call for very simple inputs
        if len(user_message.split()) < 7 and ' and ' not in user_message and '?' not in user_message[1:]:
            return [user_message]

        prompt = f"""You are a text-processing utility. Your task is to analyze the following user message and split it into individual, self-contained questions or statements.
Return the output as a single, raw JSON-formatted list of strings. Do not include any other text or formatting.

- If there is only one question, return a list with a single string.
- Split compound sentences into separate items. For example, "What is the capital of France and what is the weather there?" should become ["What is the capital of France?", "what is the weather there?"].
- Preserve the original phrasing.

User Message:
"{user_message}"

JSON Output:
"""
        try:
            response = self.co.chat(
                message=prompt,
                model="command-r-plus",
                temperature=0.0,
            )
            
            # Find and parse the JSON list from the response text
            json_str_match = re.search(r'\[.*\]', response.text, re.DOTALL)
            if json_str_match:
                # The raw string from the model might have escaped characters that need to be handled
                parsed_json = json.loads(json_str_match.group(0))
                if isinstance(parsed_json, list) and all(isinstance(q, str) for q in parsed_json):
                    return parsed_json
            
            # Fallback if parsing fails or no JSON is found
            return [user_message]
        except Exception:
            # If the API call or JSON parsing fails, return the original message as a single question.
            return [user_message]
    
    def process_message(self, user_message, language_style='en'):
        return self._process_single_message(user_message, language_style=language_style)

    def needs_web_search(self, user_message):
        """Check if a message needs web search: only if it starts with '/search '."""
        return user_message.strip().lower().startswith('/search ')

    def get_weather(self, city, place, api_key):
        """Fetch weather data for the given city and place using OpenWeatherMap API."""
        # Compose location string
        location = f"{place}, {city}"
        url = f"https://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': location,
            'appid': api_key,
            'units': 'metric'
        }
        try:
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                weather = data['weather'][0]['description'].capitalize()
                temp = data['main']['temp']
                humidity = data['main']['humidity']
                rain = data.get('rain', {}).get('1h', 0)
                summary = f"Weather in {location}: {weather}, {temp}°C, Humidity: {humidity}%. "
                if rain > 0:
                    summary += f"Rain in the last hour: {rain}mm."
                else:
                    summary += "No rain in the last hour."
                return summary
            else:
                return f"Couldn't fetch weather for {location}. (Status: {response.status_code})"
        except Exception as e:
            return f"Error fetching weather: {str(e)}"

    def get_weather_forecast(self, city, place, api_key, hours_ahead=3):
        """Fetch weather forecast for the given city and place for the next N hours using OpenWeatherMap API."""
        location = f"{place}, {city}"
        url = f"https://api.openweathermap.org/data/2.5/forecast"
        params = {
            'q': location,
            'appid': api_key,
            'units': 'metric'
        }
        try:
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                # Find the forecast closest to hours_ahead from now
                from datetime import datetime, timedelta
                now = datetime.utcnow()
                target_time = now + timedelta(hours=hours_ahead)
                closest = None
                min_diff = float('inf')
                for entry in data['list']:
                    forecast_time = datetime.utcfromtimestamp(entry['dt'])
                    diff = abs((forecast_time - target_time).total_seconds())
                    if diff < min_diff:
                        min_diff = diff
                        closest = entry
                if closest:
                    weather = closest['weather'][0]['description'].capitalize()
                    temp = closest['main']['temp']
                    humidity = closest['main']['humidity']
                    rain = closest.get('rain', {}).get('3h', 0)
                    forecast_time = datetime.utcfromtimestamp(closest['dt']).strftime('%Y-%m-%d %H:%M UTC')
                    summary = f"Forecast for {location} at {forecast_time}: {weather}, {temp}°C, Humidity: {humidity}%. "
                    if rain > 0:
                        summary += f"Rain: {rain}mm."
                    else:
                        summary += "No rain expected."
                    return summary
                else:
                    return f"No forecast data available for {location}."
            else:
                return f"Couldn't fetch forecast for {location}. (Status: {response.status_code})"
        except Exception as e:
            return f"Error fetching forecast: {str(e)}"

    def _process_single_message(self, user_message, language_style='en'):
        # Remove /forget command logic
        # Check for time/date requests
        time_triggers = [
            'time', 'current time', 'what time is it?', 'what is the time?', 'tell me the time'
        ]
        date_triggers = [
            'date', 'current date', 'what is the date?', 'tell me the date', 'current day', "today's date"
        ]
        user_lower = user_message.lower()
        if any(trigger in user_lower for trigger in time_triggers) and not any(trigger in user_lower for trigger in date_triggers):
            ist = pytz.timezone('Asia/Kolkata')
            now = datetime.now(ist)
            formatted = now.strftime('%I:%M %p (IST)')
            # 50% chance to add a playful or situational comment
            if random.random() < 0.5:
                return f"{formatted}"
            else:
                playful = random.choice([
                    "It's chai time!",
                    "Time flies, doesn't it?",
                    "Perfect time for a quick break!",
                    "Tick-tock!",
                    "Hope your day is going well!"
                ])
                return f"{formatted} {playful}"
        if any(trigger in user_lower for trigger in date_triggers):
            ist = pytz.timezone('Asia/Kolkata')
            now = datetime.now(ist)
            formatted = now.strftime('%A, %B %d, %Y')
            # 50% chance to add a friendly or situational message
            if random.random() < 0.5:
                return f"{formatted}"
            else:
                friendly = random.choice([
                    "Hope your week is off to a good start!",
                    "Enjoy your day!",
                    "Wishing you a productive week!",
                    "Make today count!",
                    "Have a great one!"
                ])
                return f"{formatted}. {friendly}"

        # Weather intent detection (before web search)
        weather_keywords = [
            'weather', 'rain', 'temperature', 'forecast', 'humidity', 'sunny', 'cloudy', 'windy', 'storm', 'climate'
        ]
        forecast_keywords = ['forecast', 'next', 'later', 'in', 'after', 'upcoming', 'future']
        user_lower = user_message.lower()
        # Detect if user asks for future weather (e.g., 'in 2 hours', 'next 3 hours')
        future_match = re.search(r'in (\d{1,2}) ?-? ?(\d{0,2})? ?hours?', user_lower)
        if any(word in user_lower for word in weather_keywords):
            city = CITY
            place = PLACE
            api_key = os.getenv('OPENWEATHER_API_KEY')
            # If future/forecast intent detected
            if any(word in user_lower for word in forecast_keywords) or future_match:
                hours_ahead = 3
                if future_match:
                    h1 = int(future_match.group(1))
                    h2 = future_match.group(2)
                    if h2:
                        hours_ahead = (h1 + int(h2)) // 2
                    else:
                        hours_ahead = h1
                return self.get_weather_forecast(city, place, api_key, hours_ahead)
            else:
                return self.get_weather(city, place, api_key)

        # Check for memory-related commands first
        if user_message.lower().startswith('memory'):
            return self._handle_memory_commands(user_message)

        # INTENT DETECTION: Should we use web search?
        needs_search = self.needs_web_search(user_message)

        if needs_search:
            # Remove the '/search ' prefix before searching
            search_query = user_message.strip()[8:].strip()
            search_results = google_search(search_query, num_results=3)
            web_context = ""
            for i, item in enumerate(search_results):
                web_context += f"Result {i+1}: {item['title']}\n{item['snippet']}\n{item['link']}\n\n"
            prompt = (
                f"Based ONLY on the following web search results, answer the user's question as directly, clearly, and humanly as possible. "
                f"If the answer is not found, reply: 'Not found in search results.' "
                f"Do NOT hedge or speculate. Keep your answer natural and easy to understand.\n\n"
                f"Web Results:\n{web_context}\n"
                f"User Question: {search_query}\n"
                f"Direct Answer:"
            )
            try:
                response = self.co.chat(
                    message=prompt,
                    model="command-r-plus",
                    temperature=0.7,
                    max_tokens=1000
                )
                assistant_response = response.text.strip()
            except Exception as e:
                assistant_response = f"I'm having trouble processing that right now. Error: {str(e)}"
        else:
            # Just answer using the model's own knowledge
            # Determine task type
            task_type = self._classify_task(user_message)
            # Build context
            context = self.get_context()
            # Prepare the message with system prompt at the beginning
            full_message = f"Instructions: {self.system_prompt}\n\n"
            if context:
                full_message += f"Context: {context}\n\n"
            full_message += f"User: {user_message}"
            try:
                response = self.co.chat(
                    message=full_message,
                    model="command-r-plus",
                    temperature=0.7,
                    max_tokens=1000
                )
                assistant_response = response.text.strip()
            except Exception as e:
                assistant_response = f"I'm having trouble processing that right now. Error: {str(e)}"

        # Save conversation
        self.db.save_conversation(user_message, assistant_response, None, None)
        # Extract and save important information
        self._extract_and_save_memory(user_message, assistant_response)

        # Language style handling
        # Only keep English, remove 'hi' and 'hien' handling
        return assistant_response
    
    def _classify_task(self, message):
        """Classify the type of task based on user message"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['remember', 'save', 'important']):
            return 'memory'
        else:
            return 'conversation'
    
    def _extract_and_save_memory(self, user_message, assistant_response):
        """Extract important information and save to memory"""
        user_lower = user_message.lower()
        
        # Check for explicit memory requests
        memory_keywords = ['remember this', 'save this', 'important', 'note this', 'memorize', 'keep in mind']
        if any(phrase in user_lower for phrase in memory_keywords):
            # Save the user's message as memory with high importance
            self.db.save_memory(user_message, "user_request", 3)
            return
        
        # Check for personal information
        personal_keywords = ['my name is', 'i am', 'i\'m', 'i work', 'i live', 'my birthday', 'my age']
        if any(phrase in user_lower for phrase in personal_keywords):
            self.db.save_memory(f"Personal info: {user_message}", "personal", 3)
            return
        
        # Check for preferences
        preference_keywords = ['i like', 'i prefer', 'i don\'t like', 'i hate', 'favorite', 'least favorite']
        if any(phrase in user_lower for phrase in preference_keywords):
            self.db.save_memory(f"Preference: {user_message}", "preference", 2)
            return
        
        # Check for detailed explanations that might be worth remembering
        if len(assistant_response) > 150 and any(word in user_lower for word in ['explain', 'teach', 'how', 'what is', 'why']):
            # Extract key points from the explanation
            key_points = self._extract_key_points(assistant_response)
            if key_points:
                self.db.save_memory(f"Explanation: {key_points}", "explanation", 1)
    
    def _extract_key_points(self, text):
        """Extract key points from a longer text"""
        # Simple extraction - take first sentence and any bullet points
        sentences = text.split('.')
        if len(sentences) > 0:
            first_sentence = sentences[0].strip()
            if len(first_sentence) > 20:  # Only if it's substantial
                return first_sentence
        return None
    
    def search_memories(self, query):
        """Search through memories using database search"""
        memories = self.db.search_memories(query, limit=5)
        if not memories:
            return f"No memories found matching '{query}'"
        
        result = f"🔍 Search results for '{query}':\n"
        for memory in memories:
            memory_id, content, category, importance, timestamp = memory
            importance_stars = "⭐" * importance
            result += f"[{memory_id}] {content} ({category}) {importance_stars}\n"
        
        return result
    
    def get_memory_summary(self):
        """Get a summary of all memories by category"""
        memories = self.db.get_memories(limit=50)
        if not memories:
            return "No memories stored yet."
        
        # Group by category
        categories = {}
        for memory in memories:
            memory_id, content, category, importance, timestamp = memory
            if category not in categories:
                categories[category] = []
            categories[category].append((memory_id, content, importance))
        
        result = "🧠 Memory Summary:\n"
        for category, items in categories.items():
            result += f"\n📂 {category.title()} ({len(items)} items):\n"
            # Show top 3 most important items per category
            sorted_items = sorted(items, key=lambda x: x[2], reverse=True)[:3]
            for memory_id, content, importance in sorted_items:
                importance_stars = "⭐" * importance
                result += f"  [{memory_id}] {content[:100]}{'...' if len(content) > 100 else ''} {importance_stars}\n"
        
        return result
    
    def add_memory(self, content, category="general", importance=1):
        """Manually add a memory"""
        self.db.save_memory(content, category, importance)
        return f"✅ Memory saved: {content[:50]}{'...' if len(content) > 50 else ''}"
    
    def delete_memory(self, memory_id):
        """Delete a specific memory by ID"""
        if self.db.delete_memory(memory_id):
            return f"✅ Memory {memory_id} deleted successfully."
        else:
            return f"❌ Memory {memory_id} not found."
    
    def _handle_memory_commands(self, user_message):
        """Handle memory-related commands"""
        parts = user_message.lower().split()
        
        if len(parts) == 1:
            # Just "memory" - show summary
            return self.get_memory_summary()
        
        command = parts[1]
        
        if command == "search" and len(parts) > 2:
            query = " ".join(parts[2:])
            return self.search_memories(query)
        
        elif command == "add" and len(parts) > 2:
            content = " ".join(parts[2:])
            category = "general"
            importance = 1
            
            # Check for category and importance in the message
            if "personal" in content.lower():
                category = "personal"
            elif "preference" in content.lower():
                category = "preference"
            elif "task" in content.lower():
                category = "task"
            
            if "important" in content.lower():
                importance = 3
            elif "very important" in content.lower():
                importance = 4
            
            return self.add_memory(content, category, importance)
        
        elif command == "delete" and len(parts) > 2:
            try:
                memory_id = int(parts[2])
                return self.delete_memory(memory_id)
            except ValueError:
                return "❌ Please provide a valid memory ID number."
        
        elif command == "summary":
            return self.get_memory_summary()
        
        else:
            return """🧠 Memory Commands:
• memory - Show memory summary
• memory search [query] - Search memories
• memory add [content] - Add new memory
• memory delete [id] - Delete memory by ID
• memory summary - Show detailed summary""" 