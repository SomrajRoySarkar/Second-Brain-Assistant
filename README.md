# 🧠 Second Brain Assistant

Your AI-powered personal assistant built with Python and Cohere. This second brain helps you manage tasks, remember important information, search through conversations, and have intelligent conversations.

## ✨ Features

- **🤖 AI-Powered Conversations**: Natural conversations using Cohere's advanced language models
- **💾 Memory System**: Automatically saves and retrieves important information from conversations
- **🔍 Smart Search**: Search through your conversation history and saved memories
- **📚 Teaching & Explanation**: Get detailed explanations and learn new concepts
- **🎨 Beautiful CLI**: Rich, colorful interface with tables, panels, and status indicators

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- Cohere API key
- Google Custom Search API key and CSE ID
- OpenWeatherMap API key (optional, for weather features)

### Installation

1. **Clone or download the project files**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Create a `.env` file** in your project root with the following content (replace with your actual values):
   ```ini
   # Cohere API Key
   COHERE_API_KEY=your-cohere-api-key-here

   # Google Custom Search API Key and CSE ID
   GOOGLE_API_KEY=your-google-api-key-here
   GOOGLE_CSE_ID=your-google-cse-id-here

   # OpenWeatherMap API Key (for weather features)
   OPENWEATHER_API_KEY=your-openweathermap-api-key-here

   # Personal Details (used for weather/location context)
   CITY=your_city
   PLACE=your_place
   LATITUDE=your_latitude
   LONGITUDE=your_longitude

   # Optional: Database and other config
   DATABASE_PATH=your-databse-path
   MAX_CONVERSATION_HISTORY=your-max-conversation-history
   MAX_MEMORY_ENTRIES=your-max-memory-entries
   KNOWLEDGE_FILE=knowledge_base.json
   ```

4. **Run the assistant**:
   ```bash
   python main.py
   ```

## 🎯 Usage Examples

### Basic Conversation
```
You: Hi! How are you today?
🤖 Assistant: Hey there! I'm doing great, thanks for asking! How about you? I'm here to help with whatever you need - whether it's managing tasks, explaining something, or just having a friendly chat. What's on your mind?
```

### Search Memories
```
You: search python
🔍 Search results for 'python':
- Python is a high-level programming language known for its simplicity and readability
- Remember to use virtual environments for Python projects
- Python's main advantages include extensive libraries and community support
```

### Get Help
```
You: help
Available Commands:
• help           - Show this help message
• search <query> - Search through your memories
• memories       - Show recent memories
• clear          - Clear the screen
• quit/exit      - Exit the application
```

## 🏗️ Architecture

The Second Brain Assistant is built with a modular architecture:

- **`main.py`**: Beautiful CLI interface with Rich library
- **`ai_assistant.py`**: Core AI logic and Cohere integration
- **`database.py`**: SQLite database management for conversations and memories
- **`config.py`**: Configuration and API key management (now loads all secrets from `.env`)

### Database Schema

The assistant uses SQLite with two main tables:

1. **conversations**: Stores all conversation exchanges
2. **memory**: Stores important information and insights

## 🔧 Configuration & Environment Variables

All sensitive information and configuration is now managed via environment variables in a `.env` file. **Do not hardcode any API keys or personal details in the code.**

**Required variables:**
- `COHERE_API_KEY`: Your Cohere API key
- `GOOGLE_API_KEY`: Google Custom Search API key
- `GOOGLE_CSE_ID`: Google Custom Search Engine ID
- `OPENWEATHER_API_KEY`: OpenWeatherMap API key (for weather features)
- `CITY`, `PLACE`: Your default city and place (for weather context)
- `LATITUDE`, `LONGITUDE`: (Optional) Your location coordinates
- `DATABASE_PATH`, `MAX_CONVERSATION_HISTORY`, `MAX_MEMORY_ENTRIES`, `KNOWLEDGE_FILE`: (Optional) Other config

**Example:** See the sample `.env` above.

## 🎨 Features in Detail

### Intelligent Context Awareness
The assistant remembers your conversation history and uses it to provide more relevant responses. It automatically builds context from:
- Recent conversations
- Important memories
- User preferences

### Smart Classification
The assistant automatically detects when you're:
- Searching for information (search, find, look for)
- Asking for explanations (explain, teach, how does)
- Saving important information (remember, save, important)

### Memory Management
Important information is automatically extracted and saved:
- User requests to remember something
- Detailed explanations provided by the assistant
- Task-related information
- Personal preferences and details

## 🛠️ Development

### Adding New Features

1. **New Commands**: Add handlers in `main.py`
2. **AI Capabilities**: Extend `ai_assistant.py`
3. **Data Storage**: Modify `database.py` schema
4. **Configuration**: Update `config.py` and `.env`

### Testing

The assistant can be tested by running it and trying various commands:
```bash
python main.py
```

## 🤝 Contributing

Feel free to enhance the assistant with:
- New AI capabilities
- Additional task management features
- Better memory organization
- Web interface
- Mobile app integration

## 📝 License

This project is open source. Feel free to use and modify for your personal use.

## 🆘 Troubleshooting

### Common Issues

1. **API Key Error**: Make sure your API keys are set correctly in your `.env` file
2. **Import Errors**: Install all dependencies with `