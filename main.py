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
        welcome_text.append("\n\nI'm your AI assistant powered by Gemini. I can help you with:")
        
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
            ("clear", "Clear the screen"),
            ("quit/exit", "Exit the application")
        ]
        
        # Add examples section
        help_text.append("\n\n📄 Report Command Examples:\n", style="bold blue")
        examples = [
            "/report artificial intelligence",
            "/report on Gandhi ji and also have a section of their education and achievements",
            "/report climate change with sections on causes, effects, and solutions",
            "/report machine learning include background and current applications",
            "/report about renewable energy covering types and future prospects"
        ]
        
        for cmd, desc in commands:
            help_text.append(f"• {cmd:<15} - {desc}\n")
        
        # Add examples
        for example in examples:
            help_text.append(f"  {example}\n")
        
        help_text.append("\nYou can also just chat naturally with me!")
        
        panel = Panel(help_text, title="Help", border_style="green")
        self.console.print(panel)
    
    # Removed: handle_task_commands, add_task_interactive, and all task-related CLI logic and help text
    
    def handle_search(self, command):
        """Handle /search command for Google search only"""
        if command.startswith("/search "):
            result = self.assistant.process_message(command)
            self.console.print(result)
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
                    # Optimized processing - skip complex splitting for simple queries
                    if len(user_input.split()) <= 10 and ' and ' not in user_input.lower():
                        # Simple query - process directly
                        language_style = self.detect_language_style(user_input)
                        final_response = self.assistant.process_message(user_input, language_style=language_style)
                    else:
                        # Complex query - use AI-powered splitter
                        questions = self.assistant.split_into_questions(user_input)
                        
                        # Check if we should create a unified response
                        if len(questions) > 1:
                            # Simplified decision making - combine if similar length
                            if len(questions) <= 2 and len(user_input) < 150:
                                # Create a unified response instead of separate ones
                                final_response = self.assistant.create_unified_response(user_input, questions)
                            else:
                                # Process each question separately for distinct topics
                                responses = []
                                for question in questions:
                                    try:
                                        language_style = self.detect_language_style(question)
                                        response = self.assistant.process_message(question, language_style=language_style)
                                        responses.append(response.strip())
                                    except Exception as e:
                                        self.console.print(f"[red]Error processing message: {str(e)}[/red]")
                                        continue
                                final_response = "\n\n".join(responses)
                        else:
                            # Single question - process normally
                            language_style = self.detect_language_style(user_input)
                            final_response = self.assistant.process_message(user_input, language_style=language_style)
                        
                    self.console.print(f"[bold green]Assistant[/bold green]: {final_response}")
                
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