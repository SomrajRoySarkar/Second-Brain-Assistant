# 🧠 Second Brain Assistant

Second Brain Assistant is your personal AI-powered helper, built with Python and Cohere. It helps you remember important information, search your memories, and have smart, friendly conversations—all from your terminal.

---

## Features

- **Conversational AI**: Chat naturally with an assistant that understands context and gives clear, concise answers.
- **Memory System**: Important info from your chats is saved and can be searched or recalled later.
- **Smart Search**: Instantly search your saved memories and conversation history.
- **Web Search**: Get up-to-date answers using Google Custom Search.
- **PDF Report Generation**: Create formal, professional PDF reports with custom titles and content.
- **Simple, Clean CLI**: Enjoy a colorful, easy-to-read interface powered by the Rich library.

---

## Getting Started

### Prerequisites

- Python 3.7 or higher
- API keys for Cohere and Google Custom Search

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
   COHERE_API_KEY=your-cohere-api-key
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
  Assistant: - Python is a high-level programming language...
  ```

- **Search the web with Google:**  
  ```
  You: /search What is quantum computing?
  Assistant: [Google search results...]
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

- **Generate a topic-based report (with automatic web search):**  
  ```
  You: /report Artificial Intelligence in Healthcare
  Assistant: Report 'Artificial Intelligence In Healthcare' generated successfully. Find it at ./reports/artificial_intelligence_in_healthcare_20240101_120000.pdf
  ```

- **Generate a formal PDF report with custom title:**  
  ```
  You: /report title: Market Analysis Report content: Create a comprehensive analysis of the current market trends in renewable energy sector
  Assistant: Report 'Market Analysis Report' generated successfully. Find it at ./reports/market_analysis_report_20240101_120000.pdf
  ```

- **Generate a report with custom sections:**  
  ```
  You: /report title: Project Report sections: Project Overview, Technical Implementation, Results, Future Work
  Assistant: Report 'Project Report' generated successfully. Find it at ./reports/project_report_20240101_120001.pdf
  ```

- **See your recent memories:**  
  ```
  You: memories
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

## Project Structure

- `main.py` — The command-line interface and main loop
- `ai_assistant.py` — Core AI logic and conversation handling
- `database.py` — Handles saving and searching conversations and memories (SQLite)
- `google_search.py` — Integrates Google Custom Search for web results
- `config.py` — Loads configuration from `.env`
- `requirements.txt` — All required Python packages

---

## Configuration

All sensitive info (API keys, database path, etc.) is managed via the `.env` file.  
**Never hardcode your keys in the code!**

---

## Dependencies

Key libraries used:
- `cohere` — For AI-powered conversation
- `rich` — For a beautiful terminal interface
- `googletrans` — For translation features
- `requests` — For web and API calls
- `python-dotenv` — For environment variable management
- `langdetect` — For language detection

Install all dependencies with:
```bash
pip install -r requirements.txt
```

---

## Notes & Tips

- When you ask multiple questions in one message, the assistant will answer them in order, but only the first answer will be prefixed with “Assistant:” for a cleaner look.
- All your important info and memories are stored in a local SQLite database.
- You can easily extend the assistant by editing or adding Python files.

---

## License

This project is open source. Feel free to use, modify, and share it for personal or educational purposes.

---

If you have any questions or want to contribute, just open an issue or pull request.  
Enjoy your new Second Brain! 🧠