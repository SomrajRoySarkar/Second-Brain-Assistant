import sqlite3
import json
from datetime import datetime
from config import DATABASE_PATH

class SecondBrainDB:
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_message TEXT NOT NULL,
                assistant_response TEXT NOT NULL,
                context TEXT,
                task_type TEXT
            )
        ''')
        
        # Check if memory table exists and has the correct schema
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memory'")
        memory_table_exists = cursor.fetchone() is not None
        
        if memory_table_exists:
            # Check if the table has the old schema (user_message, assistant_response columns)
            cursor.execute("PRAGMA table_info(memory)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'user_message' in columns and 'assistant_response' in columns:
                # Old schema detected - drop and recreate
                cursor.execute("DROP TABLE memory")
                print("Migrating memory table to new schema...")
        
        # Create memory table with correct schema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT,
                importance INTEGER DEFAULT 1
            )
        ''')
        # Removed tasks table creation
        conn.commit()
        conn.close()
    
    def save_conversation(self, user_message, assistant_response, context="", task_type=""):
        """Save a conversation exchange to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO conversations (timestamp, user_message, assistant_response, context, task_type)
            VALUES (?, ?, ?, ?, ?)
        ''', (datetime.now().isoformat(), user_message, assistant_response, context, task_type))
        
        conn.commit()
        conn.close()
    
    def get_recent_conversations(self, limit=10):
        """Get recent conversations for context"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_message, assistant_response, timestamp, task_type
            FROM conversations
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        conversations = cursor.fetchall()
        conn.close()
        
        return conversations
    
    def save_memory(self, content, category="general", importance=1):
        """Save important information to memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO memory (timestamp, content, category, importance)
            VALUES (?, ?, ?, ?)
        ''', (datetime.now().isoformat(), content, category, importance))
        conn.commit()
        conn.close()

    def get_memories(self, category=None, limit=20):
        """Retrieve memories, optionally filtered by category"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if category:
            cursor.execute('''
                SELECT id, content, category, importance, timestamp
                FROM memory
                WHERE category = ?
                ORDER BY importance DESC, timestamp DESC
                LIMIT ?
            ''', (category, limit))
        else:
            cursor.execute('''
                SELECT id, content, category, importance, timestamp
                FROM memory
                ORDER BY importance DESC, timestamp DESC
                LIMIT ?
            ''', (limit,))
        memories = cursor.fetchall()
        conn.close()
        return memories
    
    def search_memories(self, query, limit=3):
        """Search memories by keyword in content, sorted by recency"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, content, category, importance, timestamp
            FROM memory
            WHERE content LIKE ?
            ORDER BY importance DESC, timestamp DESC
            LIMIT ?
        ''', (f'%{query}%', limit))
        results = cursor.fetchall()
        conn.close()
        return results
    
    def delete_memory(self, memory_id):
        """Delete a specific memory by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM memory
            WHERE id = ?
        ''', (memory_id,))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted