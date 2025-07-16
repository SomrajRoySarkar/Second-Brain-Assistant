import sqlite3
import json
from datetime import datetime
from config import DATABASE_PATH
from contextlib import contextmanager
import threading

class SecondBrainDB:
    def __init__(self):
        self.db_path = DATABASE_PATH
        self._connection_pool = {}
        self._pool_lock = threading.Lock()
        self.init_database()
        self.create_indexes()
    
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
        
        # Create user profile table for personal information
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                name TEXT,
                birthday TEXT,
                age INTEGER,
                interests TEXT,
                friends TEXT,
                important_dates TEXT,
                personal_notes TEXT,
                last_updated TEXT
            )
        ''')
        # Removed tasks table creation
        conn.commit()
        conn.close()
    
    @contextmanager
    def get_connection(self):
        """Get a database connection from the pool"""
        thread_id = threading.get_ident()
        
        with self._pool_lock:
            if thread_id not in self._connection_pool:
                self._connection_pool[thread_id] = sqlite3.connect(self.db_path)
                self._connection_pool[thread_id].row_factory = sqlite3.Row
        
        conn = self._connection_pool[thread_id]
        try:
            yield conn
        finally:
            conn.commit()
    
    def create_indexes(self):
        """Create indexes for faster queries"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Index for conversations timestamp for recent queries
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp DESC)')
            
            # Index for memory search
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_memory_content ON memory(content)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_memory_importance ON memory(importance DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_memory_timestamp ON memory(timestamp DESC)')
            
            # Index for user profile
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_profile_timestamp ON user_profile(timestamp DESC)')
    
    def save_conversation(self, user_message, assistant_response, context="", task_type=""):
        """Save a conversation exchange to the database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO conversations (timestamp, user_message, assistant_response, context, task_type)
                VALUES (?, ?, ?, ?, ?)
            ''', (datetime.now().isoformat(), user_message, assistant_response, context, task_type))
    
    def get_recent_conversations(self, limit=10):
        """Get recent conversations for context"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_message, assistant_response, timestamp, task_type
                FROM conversations
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            return cursor.fetchall()
    
    def save_memory(self, content, category="general", importance=1):
        """Save important information to memory"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO memory (timestamp, content, category, importance)
                VALUES (?, ?, ?, ?)
            ''', (datetime.now().isoformat(), content, category, importance))

    def get_memories(self, category=None, limit=20):
        """Retrieve memories, optionally filtered by category"""
        with self.get_connection() as conn:
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
            return cursor.fetchall()
    
    def search_memories(self, query, limit=3):
        """Search memories by keyword in content, sorted by recency"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, content, category, importance, timestamp
                FROM memory
                WHERE content LIKE ?
                ORDER BY importance DESC, timestamp DESC
                LIMIT ?
            ''', (f'%{query}%', limit))
            return cursor.fetchall()
    
    def delete_memory(self, memory_id):
        """Delete a specific memory by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM memory
                WHERE id = ?
            ''', (memory_id,))
            return cursor.rowcount > 0
    
    def save_user_profile(self, name=None, birthday=None, age=None, interests=None, friends=None, important_dates=None, personal_notes=None):
        """Save or update user profile information"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if profile exists
            cursor.execute('SELECT id FROM user_profile ORDER BY timestamp DESC LIMIT 1')
            existing = cursor.fetchone()
            
            if existing:
                # Update existing profile
                update_fields = []
                values = []
                
                if name: update_fields.append("name = ?"); values.append(name)
                if birthday: update_fields.append("birthday = ?"); values.append(birthday)
                if age: update_fields.append("age = ?"); values.append(age)
                if interests: update_fields.append("interests = ?"); values.append(interests)
                if friends: update_fields.append("friends = ?"); values.append(friends)
                if important_dates: update_fields.append("important_dates = ?"); values.append(important_dates)
                if personal_notes: update_fields.append("personal_notes = ?"); values.append(personal_notes)
                
                if update_fields:
                    update_fields.append("last_updated = ?")
                    values.append(datetime.now().isoformat())
                    values.append(existing[0])
                    
                    cursor.execute(f'''
                        UPDATE user_profile 
                        SET {', '.join(update_fields)}
                        WHERE id = ?
                    ''', values)
            else:
                # Create new profile
                cursor.execute('''
                    INSERT INTO user_profile (timestamp, name, birthday, age, interests, friends, important_dates, personal_notes, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (datetime.now().isoformat(), name, birthday, age, interests, friends, important_dates, personal_notes, datetime.now().isoformat()))
    
    def get_user_profile(self):
        """Get the current user profile"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT name, birthday, age, interests, friends, important_dates, personal_notes, last_updated
                FROM user_profile
                ORDER BY timestamp DESC
                LIMIT 1
            ''')
            
            profile = cursor.fetchone()
            if profile:
                return {
                    'name': profile[0],
                    'birthday': profile[1],
                    'age': profile[2],
                    'interests': profile[3],
                    'friends': profile[4],
                    'important_dates': profile[5],
                    'personal_notes': profile[6],
                    'last_updated': profile[7]
                }
            return None
