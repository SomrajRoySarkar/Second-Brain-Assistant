# 🧠 Second Brain Assistant

Second Brain Assistant is your personal AI-powered helper, built with Python and Google Gemini. It helps you remember important information, search your memories, and have smart, friendly conversations—all from your terminal.

---

## Features

- **Conversational AI**: Chat naturally with an assistant powered by Google Gemini that understands context and gives clear, concise answers.
- **Memory System**: Important info from your chats is saved and can be searched or recalled later.
- **Smart Search**: Instantly search your saved memories and conversation history.
- **Advanced Web Search**: Get up-to-date answers using Google Custom Search with AI-powered enrichment.
- **PDF Report Generation**: Create formal, professional PDF reports with custom sections and content.
- **Simple, Clean CLI**: Enjoy a colorful, easy-to-read interface powered by the Rich library.
- **Performance Optimized**: Caching and parallel processing for faster responses.

---

## Getting Started

### Prerequisites

- Python 3.7 or higher
- API keys for Google Gemini and Google Custom Search

### Installation

1. **Clone this repository**  
   Download or clone the project files to your computer.

2. **Install dependencies**  
   Open a terminal in the project folder and run:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your environment variables**  
   Create a `.env` file in the project root with your API keys and settings:
   ```ini
   GEMINI_API_KEY=your-gemini-api-key
   GOOGLE_API_KEY=your-google-api-key
   GOOGLE_CSE_ID=your-google-cse-id
   DATABASE_PATH=second_brain.db
   ```

4. **Run the assistant**
   ```bash
   python main.py
   ```

---

## How to Use

Just type your questions or commands in the terminal. Here are some things you can try:

- **Chat naturally:**  
  ```
  You: What's the capital of France?
  Assistant: The capital of France is Paris.
  ```

- **Ask multiple things at once:**  
  ```
  You: Who is Nikola Tesla and what did he invent?
  Assistant: Nikola Tesla was a Serbian-American inventor and engineer. He is best known for his work on alternating current (AC) electricity.
  ```

- **Search your memories:**  
  ```
  You: memory search python
  Assistant: 🔍 Search results for 'python': [memory_id] Python is a high-level programming language... (general) ⭐⭐⭐
  ```

- **Search the web with advanced search:**  
  ```
  You: /search What is quantum computing?
  Assistant: [AI-enriched search results with references]
  ```

- **Get a detailed explanation:**  
  ```
  You: /explain Photosynthesis
  Assistant: [Detailed, well-structured explanation]
  ```

- **Get an explanation for specific marks or format:**  
  ```
  You: /explain Newton's Laws; for 5 marks; format: bullet points
  Assistant: [Explanation tailored for 5 marks, in bullet points]
  ```

- **Generate a comprehensive PDF report:**  
  ```
  You: /report Artificial Intelligence in Healthcare
  Assistant: 📄 **Report Generated Successfully!**
  
  **Title:** Artificial Intelligence in Healthcare Report
  
  **Preview:** This report covers the main topic of AI in healthcare, including key sections on current applications, challenges, and future prospects.
  
  **File Location:** ./reports/artificial_intelligence_in_healthcare_20240101_120000.pdf
  
  ✅ Your report is ready! You can find it in the reports folder.
  ```

- **Generate a report with specific sections:**  
  ```
  You: /report on Gandhi ji and also have a section of their education and achievements
  Assistant: [Generates comprehensive report with Introduction, Education, Achievements, and additional relevant sections]
  ```

- **Memory management:**  
  ```
  You: memory
  Assistant: 🧠 Memory Summary: [Shows your saved memories by category]
  
  You: memory add I prefer dark chocolate over milk chocolate
  Assistant: ✅ Memory saved: I prefer dark chocolate over milk chocolate...
  
  You: memory profile
  Assistant: 👤 Your Profile: [Shows your personal information]
  ```

- **Get help:**  
  ```
  You: help
  ```

- **Exit:**  
  ```
  You: quit
  ```

---

## Available Commands

- `help` - Show help message
- `/search <query>` - Search Google for your query
- `memories` - Show recent memories
- `memory` - Show memory summary
- `memory search <query>` - Search memories
- `memory add <content>` - Add new memory
- `/explain <topic>[; for X marks][; format: ...]` - Get a detailed explanation
- `/report <topic>` - Generate a comprehensive PDF report
- `clear` - Clear the screen
- `quit/exit` - Exit the application

### Report Command Examples:
- `/report artificial intelligence`
- `/report on Gandhi ji and also have a section of their education and achievements`
- `/report climate change with sections on causes, effects, and solutions`
- `/report machine learning include background and current applications`
- `/report about renewable energy covering types and future prospects`

---

## Project Structure

- `main.py` — The command-line interface and main loop
- `ai_assistant.py` — Core AI logic and conversation handling with Gemini
- `database.py` — Handles saving and searching conversations and memories (SQLite)
- `google_search.py` — Integrates Google Custom Search with AI-powered enrichment
- `report_generator.py` — Generates professional PDF reports
- `config.py` — Loads configuration from `.env`
- `requirements.txt` — All required Python packages

---

## Configuration

All sensitive info (API keys, database path, etc.) is managed via the `.env` file.  
**Never hardcode your keys in the code!**

---

## Dependencies

Key libraries used:
- `google-generativeai` — For AI-powered conversation with Gemini
- `rich` — For a beautiful terminal interface
- `googletrans` — For translation features
- `requests` — For web and API calls
- `python-dotenv` — For environment variable management
- `langdetect` — For language detection
- `reportlab` — For PDF report generation
- `beautifulsoup4` — For web scraping and content extraction

Install all dependencies with:
```bash
pip install -r requirements.txt
```

---

## Performance Features

- **Response Caching**: Frequently asked questions are cached for faster responses
- **Parallel Processing**: Web searches and memory operations run in parallel
- **Smart Query Splitting**: Complex questions are intelligently split for better responses
- **Optimized Search**: Advanced web search with query expansion and result enrichment

---

## Notes & Tips

- The assistant uses Google Gemini for all AI interactions, providing high-quality responses
- All your important info and memories are stored in a local SQLite database
- PDF reports are automatically saved in the `reports/` folder with timestamps
- The assistant remembers your preferences and personal information across sessions
- You can easily extend the assistant by editing or adding Python files

---

## License

This project is open source. Feel free to use, modify, and share it for personal or educational purposes.

---

If you have any questions or want to contribute, just open an issue or pull request.  
Enjoy your new Second Brain! 🧠