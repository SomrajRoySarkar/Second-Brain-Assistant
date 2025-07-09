#!/usr/bin/env python3
"""
Test script for Second Brain Assistant
"""

from ai_assistant import SecondBrainAssistant

def test_assistant():
    """Test the assistant functionality"""
    assistant = SecondBrainAssistant()
    
    print("🧠 Testing Second Brain Assistant...\n")
    
    # Test 1: Basic greeting
    print("Test 1: Basic greeting")
    response = assistant.process_message("hey")
    print(f"Input: hey")
    print(f"Response: {response}\n")
    
    # Test 2: Memory addition
    print("Test 2: Memory addition")
    response = assistant.process_message("remember this: I like pizza")
    print(f"Input: remember this: I like pizza")
    print(f"Response: {response}\n")
    
    # Test 3: Memory search
    print("Test 3: Memory search")
    response = assistant.search_memories("pizza")
    print(f"Search: pizza")
    print(f"Response: {response}\n")
    
    # Test 4: Memory summary
    print("Test 4: Memory summary")
    response = assistant.get_memory_summary()
    print(f"Memory summary:")
    print(f"{response}\n")
    
    # Test 7: Complex conversation
    print("Test 7: Complex conversation")
    response = assistant.process_message("What is the capital of France?")
    print(f"Input: What is the capital of France?")
    print(f"Response: {response}\n")
    
    print("✅ All tests completed!")

if __name__ == "__main__":
    test_assistant() 