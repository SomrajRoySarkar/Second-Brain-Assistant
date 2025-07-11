#!/usr/bin/env python3
"""
Second Brain Assistant - Your AI-powered personal assistant
Built with Cohere and Python
"""

import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text
from rich import print as rprint
from ai_assistant import SecondBrainAssistant
from datetime import datetime
from langdetect import detect
import re

class SecondBrainCLI:
    def __init__(self):
        self.console = Console()
        self.assistant = SecondBrainAssistant()
        self.running = True

    def detect_language_style(self, text):
        try:
            lang = detect(text)
            if lang == 'en':
                return 'en'
            else:
                return 'en'
        except Exception:
            return 'en'
    
    def display_welcome(self):
        """Display welcome message"""
        welcome_text = Text()
        welcome_text.append("🧠 ", style="bold blue")
        welcome_text.append("Welcome to your Second Brain!", style="bold white")
        welcome_text.append("\n\nI'm your AI assistant powered by Cohere. I can help you with:")
        
        features = [
            "🔍 Searching through your memories",
            "📚 Explaining concepts and teaching",
            "💾 Remembering important information",
            "💬 Having friendly conversations",
            "📄 Generating formal PDF reports"
        ]
        
        for feature in features:
            welcome_text.append(f"\n{feature}")
        
        welcome_text.append("\n\nType 'help' for commands or just start chatting!")
        
        panel = Panel(welcome_text, title="Second Brain Assistant", border_style="blue")
        self.console.print(panel)
    
    def display_help(self):
        """Display help information"""
        help_text = Text()
        help_text.append("Available Commands:\n", style="bold yellow")
        
        commands = [
            ("help", "Show this help message"),
            ("/search <query>", "Search Google for your query"),
            ("memories", "Show recent memories"),
            ("memory", "Show memory summary"),
            ("memory search <query>", "Search memories"),
            ("memory add <content>", "Add new memory"),
            ("/explain <topic>[; for X marks][; format: ...]", "Get a detailed explanation of a topic, optionally for marks or in a specific format"),
            ("/report <topic>", "Generate a comprehensive PDF report on any topic (with web search)"),
            ("/report title: ... content: ...", "Generate a custom PDF report with specific title and content"),
            ("/report title: ... sections: ...", "Generate a report with custom sections (comma-separated)"),
            ("clear", "Clear the screen"),
            ("quit/exit", "Exit the application")
        ]
        
        for cmd, desc in commands:
            help_text.append(f"• {cmd:<15} - {desc}\n")
        
        help_text.append("\nYou can also just chat naturally with me!")
        
        panel = Panel(help_text, title="Help", border_style="green")
        self.console.print(panel)
    
    # Removed: handle_task_commands, add_task_interactive, and all task-related CLI logic and help text
    
    def handle_search(self, command):
        """Handle /search command for Google search only"""
        if command.startswith("/search "):
            query = command[len("/search "):].strip()
            result = self.assistant.process_message(command)
            self.console.print(result)
            return True
        elif command == "memories":
            memories = self.assistant.db.get_memories(limit=10)
            if not memories:
                self.console.print("No memories found.")
                return True
            table = Table(title="Recent Memories")
            table.add_column("Content", style="cyan")
            table.add_column("Category", style="magenta")
            table.add_column("Importance", style="yellow")
            table.add_column("Date", style="green")
            for memory in memories:
                table.add_row(
                    memory[1][:50] + "..." if len(memory[1]) > 50 else memory[1],  # memory[1] is content
                    memory[2],  # memory[2] is category
                    str(memory[3]),  # memory[3] is importance
                    memory[4][:10]  # memory[4] is timestamp, just the date part
                )
            self.console.print(table)
            return True
        return False
    
    def _process_and_print(self, message):
        """Processes a single message and prints the assistant's response."""
        try:
            language_style = self.detect_language_style(message)
            response = self.assistant.process_message(message, language_style=language_style)
            
            if "\n\n" in response:
                self.console.print(response.strip())
            else:
                self.console.print(response.strip())
        except Exception as e:
            self.console.print(f"[red]Error processing message: {str(e)}[/red]")
            self.console.print("[yellow]I'm having trouble processing that. Could you try rephrasing?[yellow]")

    def run(self):
        """Main application loop"""
        self.display_welcome()
        
        while self.running:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]")
                
                # Handle special commands
                if user_input.lower() in ['quit', 'exit']:
                    self.console.print("[yellow]Goodbye! Thanks for using your Second Brain! 🧠[/yellow]")
                    break
                elif user_input.lower() == 'help':
                    self.display_help()
                    continue
                elif user_input.lower() == 'clear':
                    os.system('cls' if os.name == 'nt' else 'clear')
                    self.display_welcome()
                    continue
                elif user_input.lower() in ['time', 'date']:
                    now = datetime.now()
                    formatted = now.strftime('%A, %B %d, %Y %I:%M %p')
                    self.console.print(f"[bold green]Current date and time:[/bold green] {formatted}")
                    continue
                # Remove voice mode command
                # elif user_input.lower() == 'voice':
                #     self.console.print("[bold green]Voice mode activated. Say 'exit' to stop.[/bold green]")
                #     self.voice_mode()
                #     continue
                
                # Handle search commands
                if self.handle_search(user_input):
                    continue
                
                # Handle memory commands
                if user_input.lower().startswith("memory"):
                    response = self.assistant._handle_memory_commands(user_input)
                    self.console.print(response)
                    continue
                # Process user input
                # Do not print the user's command

                with self.console.status("[bold green]Thinking..."):
                    # Use the new AI-powered splitter
                    questions = self.assistant.split_into_questions(user_input)

                    if len(questions) > 1:
                        all_answers = []
                        for idx, question in enumerate(questions):
                            try:
                                language_style = self.detect_language_style(question)
                                response = self.assistant.process_message(question, language_style=language_style)
                                if idx == 0:
                                    all_answers.append(f"[bold green]Assistant[/bold green]: {response.strip()}")
                                else:
                                    all_answers.append(response.strip())
                            except Exception as e:
                                self.console.print(f"[red]Error processing message: {str(e)}[/red]")
                                self.console.print("[yellow]I'm having trouble processing that. Could you try rephrasing?[yellow]")
                                continue
                        
                        combined_response = " ".join(all_answers)
                        
                        if len(combined_response) < 80 and '\n' not in combined_response:
                            self.console.print(combined_response)
                        else:
                            self.console.print("\n\n".join(all_answers))
                    else:
                        # If there's only one question, process it directly
                        response = self.assistant.process_message(user_input, language_style=self.detect_language_style(user_input))
                        self.console.print(f"[bold green]Assistant[/bold green]: {response.strip()}")
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Goodbye! Thanks for using your Second Brain! 🧠[/yellow]")
                break
            except Exception as e:
                self.console.print(f"[red]An error occurred: {str(e)}[/red]")

def main():
    """Main entry point"""
    try:
        cli = SecondBrainCLI()
        cli.run()
    except Exception as e:
        console = Console()
        console.print(f"[red]Failed to start Second Brain Assistant: {str(e)}[/red]")
        console.print("[yellow]Please check your API key and internet connection.[/yellow]")
        sys.exit(1)

if __name__ == "__main__":
    main() 