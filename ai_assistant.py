import google.generativeai as genai
from database import SecondBrainDB
from datetime import datetime
import json
import random
import re
from google_search import google_search, advanced_web_search
import threading
import dateparser
import pytz
from googletrans import Translator
import os
from dotenv import load_dotenv
from functools import lru_cache
import asyncio
from concurrent.futures import ThreadPoolExecutor
load_dotenv()

# Gemini API Key and Model
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-1.5-flash"

class SecondBrainAssistant:
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(GEMINI_MODEL)
        self.db = SecondBrainDB()
        self.conversation_history = []
        self.advanced_search_mode = True  # Default to advanced mode
        self.executor = ThreadPoolExecutor(max_workers=3)  # For parallel processing
        self._response_cache = {}  # Simple response cache
        self._cache_lock = threading.Lock()
        self.system_prompt = """You are a friendly and helpful assistant. Your main goal is to provide clear, complete answers in a natural, conversational way.\n\n**Core Instructions:**\n1.  **Simple and Clear:** Use easy-to-understand words. Avoid jargon or complex vocabulary.\n2.  **Full Sentences:** Always use grammatically correct, complete sentences. For example, instead of just "Paris," say, "The capital of France is Paris."\n3.  **Friendly Tone:** Be approachable and conversational, like a real person.\n4.  **Be Concise:** Keep your answers brief and to the point (usually 2-3 sentences).\n5.  **Directly Answer:** Always address the user's question directly.\n\n**Example:**\n*   **User:** what's the time and how are you\n*   **Good Response:** "I'm doing well, thanks for asking! The current time is 3:15 PM."\n*   **Bad Response:** "3:15 PM. I am an AI."\n\nYour primary goal is to be helpful, clear, and friendly."""
        self.greeting_responses = [
            "Hi, how are you today?",
            "Hello! What's new with you?",
            "Hey there, I'm here to chat!",
            "Greetings! How can I assist you today?",
            "Hey! Anything on your mind?",
            "Hi! What would you like to talk about today?",
            "Hello! Hope you're having a good day!",
            "Hey! How's everything going?",
            "Hi! Let's make today great!",
            "Hello! I'm here whenever you need me."
        ]
        self.last_greeting = None
    
    def _get_cache_key(self, message, context=""):
        """Generate a cache key for responses"""
        return hash((message.lower().strip(), context))
    
    def _get_cached_response(self, message, context=""):
        """Get cached response if available"""
        cache_key = self._get_cache_key(message, context)
        with self._cache_lock:
            return self._response_cache.get(cache_key)
    
    def _cache_response(self, message, context, response):
        """Cache a response"""
        cache_key = self._get_cache_key(message, context)
        with self._cache_lock:
            # Simple cache with max size of 100 entries
            if len(self._response_cache) >= 100:
                # Remove oldest entry
                oldest_key = next(iter(self._response_cache))
                del self._response_cache[oldest_key]
            self._response_cache[cache_key] = response
    
    @lru_cache(maxsize=50)
    def get_context(self):
        """Build enriched context from user profile, recent interactions and key memories"""
        context_parts = []
        
        # Get user profile information
        user_profile = self.db.get_user_profile()
        if user_profile:
            context_parts.append("About you:")
            if user_profile.get('name'):
                context_parts.append(f"- Your name is {user_profile['name']}")
            if user_profile.get('birthday'):
                context_parts.append(f"- Your birthday is {user_profile['birthday']}")
            if user_profile.get('friends'):
                context_parts.append(f"- Your friends: {user_profile['friends']}")
            if user_profile.get('interests'):
                context_parts.append(f"- Your interests: {user_profile['interests']}")
        
        # Get recent conversations
        recent_conversations = self.db.get_recent_conversations(5)
        if recent_conversations:
            context_parts.append("\nRecent conversations:")
            for conv in recent_conversations:
                context_parts.append(f"You: {conv[0]}")
                context_parts.append(f"Me: {conv[1]}")
        
        # Get important memories with more insight
        memories = self.db.get_memories(limit=5)
        if memories:
            context_parts.append("\nImportant things you've told me:")
            for memory in memories:
                context_parts.append(f"- {memory[1]}")  # memory[1] is content
        
        return "\\n".join(context_parts)
    
    def split_into_questions(self, user_message):
        """
        Uses the language model to split a user's message into distinct questions or statements.
        """
        # Check cache first
        cached = self._get_cached_response(f"split:{user_message}")
        if cached:
            return cached
        
        # A simple heuristic to avoid an API call for very simple inputs
        if len(user_message.split()) < 7 and ' and ' not in user_message and '?' not in user_message[1:]:
            result = [user_message]
            self._cache_response(f"split:{user_message}", "", result)
            return result

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
            response = self.model.generate_content(prompt)
            text = response.text if hasattr(response, 'text') else response.candidates[0].content.parts[0].text
            json_str_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_str_match:
                parsed_json = json.loads(json_str_match.group(0))
                if isinstance(parsed_json, list) and all(isinstance(q, str) for q in parsed_json):
                    self._cache_response(f"split:{user_message}", "", parsed_json)
                    return parsed_json
            result = [user_message]
            self._cache_response(f"split:{user_message}", "", result)
            return result
        except Exception:
            result = [user_message]
            self._cache_response(f"split:{user_message}", "", result)
            return result
    
    def should_combine_responses(self, user_message, responses):
        """
        Determines whether multiple responses should be combined into one cohesive response
        or kept separate based on the context and content.
        """
        # Always combine if there's only one response
        if len(responses) <= 1:
            return True
            
        # Check if the original message suggests a unified response is expected
        unified_indicators = [
            "tell me about", "explain", "describe", "what is", "how to",
            "my name is", "i am", "introduce", "hello", "hi", "hey"
        ]
        
        message_lower = user_message.lower()
        if any(indicator in message_lower for indicator in unified_indicators):
            return True
            
        # Check if responses are related (simple heuristic)
        if len(responses) == 2 and len(user_message) < 100:
            return True
            
        # For longer, complex queries with multiple distinct questions
        return False
    
    def create_unified_response(self, user_message, questions):
        """
        Creates a single, cohesive response to multiple related questions or statements
        instead of processing them separately.
        """
        # Build context for unified response
        context = self.get_context()
        
        # Create a prompt that asks for a unified response to all parts of the message
        unified_prompt = f"""Instructions: {self.system_prompt}
        
Context: {context if context else 'None'}
        
User Message: {user_message}
        
Please provide a single, cohesive response that addresses all parts of the user's message naturally. 
Do not treat each part separately - instead, create one flowing, conversational response that feels human and natural."""
        
        try:
            response = self.model.generate_content(unified_prompt)
            text = response.text if hasattr(response, 'text') else response.candidates[0].content.parts[0].text
            return text.strip()
        except Exception as e:
            return self.process_message(questions[0]) if questions else f"I'm having trouble processing that right now. Error: {str(e)}"
    
    def handle_explain_command(self, user_message):
        """Handle /explain command: parse topic, optional marks, and format, then generate a detailed explanation."""
        import re
        # Remove '/explain' prefix
        command = user_message[len('/explain'):].strip()
        # Parse for 'for X marks' and 'format: ...'
        marks = None
        format_str = None
        # Look for 'for X marks' (case-insensitive)
        marks_match = re.search(r'for (\d+) ?marks?', command, re.IGNORECASE)
        if marks_match:
            marks = int(marks_match.group(1))
            command = re.sub(r'for (\d+) ?marks?', '', command, flags=re.IGNORECASE).strip()
        # Look for 'format: ...' (case-insensitive)
        format_match = re.search(r'format:([^;]+)', command, re.IGNORECASE)
        if format_match:
            format_str = format_match.group(1).strip()
            command = re.sub(r'format:[^;]+', '', command, flags=re.IGNORECASE).strip()
        # Remove trailing semicolons and whitespace
        topic = command.strip(' ;')
        # Build prompt
        prompt = f"You are an expert explainer. Provide a detailed, clear, and efficient explanation of the following topic: '{topic}'. "
        if marks:
            prompt += f"The explanation should be suitable for an answer worth {marks} marks. "
        if format_str:
            prompt += f"Format the answer as: {format_str}. "
        else:
            prompt += "Use a standard, well-structured format with headings, bullet points, and examples if relevant. "
        prompt += "Do not add unnecessary filler or repetition. Be as smart and concise as possible, but cover all key points in detail."
        try:
            response = self.model.generate_content(prompt)
            text = response.text if hasattr(response, 'text') else response.candidates[0].content.parts[0].text
            return text.strip()
        except Exception as e:
            return f"I'm having trouble generating the explanation right now. Error: {str(e)}"

    def handle_report_command(self, user_message):
        """Handle /report command: parse the request and generate a PDF report."""
        from report_generator import PDFReportGenerator
        
        # Extract the actual request after /report
        request_content = user_message[len('/report'):].strip()
        
        # Provide immediate feedback about what we're doing
        if not request_content:
            return "Please specify what you'd like the report to be about. Example: /report on artificial intelligence"
        
        # Show what we understood from the request
        try:
            generator = PDFReportGenerator()
            
            # Get a preview of what will be generated
            preview_prompt = f"""
            Analyze this report request and provide a brief summary of what the report will contain:
            
            Request: "{request_content}"
            
            Provide a 2-3 sentence summary of:
            1. The main topic
            2. Key sections that would be included
            3. Type of report (biographical, technical, analysis, etc.)
            
            Be concise and informative.
            """
            
            preview_response = self.model.generate_content(preview_prompt)
            preview_text = preview_response.text if hasattr(preview_response, 'text') else preview_response.candidates[0].content.parts[0].text
            
            # Generate the actual report
            file_path, title = generator.generate_report(user_message, self)
            
            if file_path:
                return f"\n📄 **Report Generated Successfully!**\n\n**Title:** {title}\n\n**Preview:** {preview_text.strip()}\n\n**File Location:** {file_path}\n\n✅ Your report is ready! You can find it in the reports folder."
            else:
                return f"❌ Failed to generate report: {title}"
                
        except Exception as e:
            return f"❌ Error generating report: {str(e)}. Please try again with a simpler request."
    
    def process_message(self, user_message, language_style='en'):
        # Handle /search command
        if user_message.strip().lower().startswith('/search'):
            query = user_message[len('/search'):].strip()
            if not query:
                return "Please provide a search query after /search."
            search_results = advanced_web_search(query, self.model, num_results=5)
            provide_refs = self.should_provide_references(query)
            if search_results:
                top = search_results[0]
                main_answer = top.get('enriched_snippet') or top.get('snippet') or 'No summary available.'
                if provide_refs:
                    more_refs = []
                    for item in search_results:
                        if item.get('link') and item.get('title'):
                            more_refs.append(f"- {item['title']}: {item['link']}")
                    output = f"{main_answer}\n\nReferences:\n" + "\n".join(more_refs)
                    assistant_response = output
                else:
                    assistant_response = main_answer
            else:
                assistant_response = "Not found in search results."
            return assistant_response
        # Handle /explain command
        if user_message.strip().lower().startswith('/explain'):
            return self.handle_explain_command(user_message)
        # Handle /report command
        if user_message.strip().lower().startswith('/report'):
            return self.handle_report_command(user_message)
        # Handle memory commands
        if user_message.lower().startswith('memory'):
            return self._handle_memory_commands(user_message)
        # All other messages: always use conversation mode, never web search
        return self._process_conversation_message(user_message, language_style=language_style)

    def needs_web_search(self, user_message):
        # Always use web search for general queries (not explain, report, memory, or time/date)
        lowered = user_message.strip().lower()
        if (lowered.startswith('/explain') or lowered.startswith('/report') or lowered.startswith('memory')):
            return False
        # Check for time/date intent
        if self.is_time_or_date_query(user_message) in ['time', 'date']:
            return False
        return True

    def is_time_or_date_query(self, user_message):
        """
        Uses the language model to determine if the user is asking for the current time or date.
        Returns 'time', 'date', or 'none'.
        """
        prompt = f"""You are a text classification assistant. Your task is to determine if the user's message is a direct request for the current time or date.
Respond with only one of these three words: 'time', 'date', or 'none'. Do not add any other text or punctuation.

- If the user is asking for the current time, respond with 'time'.
- If the user is asking for the current date, respond with 'date'.
- If the user's message mentions time or date in another context (e.g., "This is the first time...", "Let's schedule for a later date"), respond with 'none'.
- If the message is a greeting or a general question, respond with 'none'.

User Message:
"{user_message}"

Classification:"""

        try:
            response = self.model.generate_content(prompt)
            text = response.text if hasattr(response, 'text') else response.candidates[0].content.parts[0].text
            result = text.strip().lower()
            if result in ['time', 'date']:
                return result
            else:
                return 'none'
        except Exception:
            return 'none'

    def should_provide_references(self, user_message):
        """Use LLM to decide if references should be provided for this query."""
        prompt = (
            "You are an expert AI assistant. For the following user message, decide if it would be helpful or expected to provide references, sources, or links in the answer. "
            "Respond with only 'yes' or 'no'.\n\n"
            f"User Message: {user_message}\n\nClassification:"
        )
        try:
            response = self.model.generate_content(prompt)
            text = response.text if hasattr(response, 'text') else response.candidates[0].content.parts[0].text
            result = text.strip().lower()
            return result == 'yes'
        except Exception:
            return False

    def _process_conversation_message(self, user_message, language_style='en'):
        # Check cache first
        context = self.get_context()
        cached_response = self._get_cached_response(user_message, context)
        if cached_response:
            return cached_response
        
        # Just answer using the model's own knowledge (never web search)
        task_type = self._classify_task(user_message)
        full_message = f"Instructions: {self.system_prompt}\n\n"
        if context:
            full_message += f"Context: {context}\n\n"
        full_message += f"User: {user_message}"
        
        try:
            response = self.model.generate_content(full_message)
            text = response.text if hasattr(response, 'text') else response.candidates[0].content.parts[0].text
            assistant_response = text.strip()
        except Exception as e:
            assistant_response = f"I'm having trouble processing that right now. Error: {str(e)}"
        
        # Cache the response
        self._cache_response(user_message, context, assistant_response)
        
        # Save to database and extract memory asynchronously
        self.executor.submit(self._save_conversation_async, user_message, assistant_response)
        
        return assistant_response
    
    def _save_conversation_async(self, user_message, assistant_response):
        """Save conversation and extract memory asynchronously"""
        self.db.save_conversation(user_message, assistant_response, None, None)
        self._extract_and_save_memory(user_message, assistant_response)
    
    def _classify_task(self, message):
        """Classify the type of task based on user message"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['remember', 'save', 'important']):
            return 'memory'
        else:
            return 'conversation'
    
    def _extract_and_save_memory(self, user_message, assistant_response):
        """Extract personal information and selectively save to memory or user profile"""
        user_lower = user_message.lower()

        # Handle personal information differently by updating the user profile
        if 'my name is' in user_lower:
            name = user_message.split('my name is')[-1].strip().split()[0]
            self.db.save_user_profile(name=name)
            return

        if 'my birthday is' in user_lower or 'i was born on' in user_lower:
            dob_keywords = ['my birthday is', 'i was born on']
            for keyword in dob_keywords:
                if keyword in user_lower:
                    birthday = user_message.split(keyword)[-1].strip().split('.')[0]
                    self.db.save_user_profile(birthday=birthday)
            return

        if 'my friend is' in user_lower:
            friend_name = user_message.split('my friend is')[-1].strip().split('.')[0]
            current_profile = self.db.get_user_profile() or {}
            friends = current_profile.get('friends', '') + f', {friend_name}'
            self.db.save_user_profile(friends=friends.strip(', '))
            return

        # General important information
        memory_keywords = ['remember this', 'save this', 'important', 'note this', 'memorize', 'keep in mind']
        if any(phrase in user_lower for phrase in memory_keywords):
            # Save the user's message as memory with high importance
            self.db.save_memory(user_message, "user_request", 3)
            return

        # Check for preferences
        preference_keywords = ['i like', 'i prefer', 'i don\'t like', 'i hate', 'favorite', 'least favorite']
        if any(phrase in user_lower for phrase in preference_keywords):
            self.db.save_memory(f"Preference: {user_message}", "preference", 2)
            return

        # Context-based special saves
        if len(assistant_response) >= 150 and any(word in user_lower for word in ['explain', 'teach', 'how', 'what is', 'why']):
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
    
    def get_user_profile_summary(self):
        """Get a summary of user profile information"""
        profile = self.db.get_user_profile()
        if not profile:
            return "👤 No profile information saved yet.\n\nTip: Tell me about yourself! Say things like 'My name is...' or 'My birthday is...'"
        
        result = "👤 Your Profile:\n"
        
        if profile.get('name'):
            result += f"\n🏷️ Name: {profile['name']}"
        
        if profile.get('birthday'):
            result += f"\n🎂 Birthday: {profile['birthday']}"
        
        if profile.get('age'):
            result += f"\n🔢 Age: {profile['age']}"
        
        if profile.get('friends'):
            result += f"\n👥 Friends: {profile['friends']}"
        
        if profile.get('interests'):
            result += f"\n💡 Interests: {profile['interests']}"
        
        if profile.get('important_dates'):
            result += f"\n📅 Important Dates: {profile['important_dates']}"
        
        if profile.get('personal_notes'):
            result += f"\n📝 Notes: {profile['personal_notes']}"
        
        if profile.get('last_updated'):
            result += f"\n\n🕐 Last updated: {profile['last_updated'][:10]}"
        
        return result
    
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
        
        elif command == "profile":
            return self.get_user_profile_summary()
        
        else:
            return """🧠 Memory Commands:
• memory - Show memory summary
• memory search [query] - Search memories
• memory add [content] - Add new memory
• memory delete [id] - Delete memory by ID
• memory summary - Show detailed summary
• memory profile - Show your profile information"""
