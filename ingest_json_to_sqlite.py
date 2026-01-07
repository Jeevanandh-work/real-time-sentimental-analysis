#!/usr/bin/env python3
"""
Local JSON Data Storage - Store Kaggle Sentiment140 Dataset in SQLite
Processes: training_data.json (1.6M tweets in JSON format)
Output: tweets.db (SQLite database)
"""

import json
import sqlite3
import sys
from datetime import datetime
import os

# ==================== CONFIGURATION ====================

JSON_FILE = r"training_data.json"
DATABASE_FILE = r"tweets.db"

# ==================== FUNCTIONS ====================

def create_database():
    """Create SQLite database and tweets table"""
    try:
        # Remove existing database if it exists
        if os.path.exists(DATABASE_FILE):
            print(f"\n⚠️  Database file already exists, removing...")
            os.remove(DATABASE_FILE)
        
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Create tweets table
        cursor.execute('''
            CREATE TABLE tweets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sentiment_label TEXT NOT NULL,
                sentiment_value INTEGER,
                tweet_id TEXT,
                created_at TEXT,
                query TEXT,
                user TEXT,
                text TEXT,
                ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for faster queries
        cursor.execute('CREATE INDEX idx_sentiment ON tweets(sentiment_label)')
        cursor.execute('CREATE INDEX idx_user ON tweets(user)')
        cursor.execute('CREATE INDEX idx_date ON tweets(created_at)')
        
        conn.commit()
        conn.close()
        
        print("✅ Database created successfully!")
        return conn
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        sys.exit(1)


def load_json_and_insert():
    """Load JSON file and insert into SQLite database"""
    print("\n" + "="*70)
    print("📊 JSON TO SQLITE DATABASE INGESTION")
    print("="*70)
    print(f"\n📋 Configuration:")
    print(f"   - JSON File: {JSON_FILE}")
    print(f"   - Database File: {DATABASE_FILE}")
    
    # Create database
    print(f"\n🗄️  Creating SQLite database...")
    create_database()
    
    # Connect to database
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Load JSON file
    print(f"\n📂 Loading JSON file...")
    try:
        if not os.path.exists(JSON_FILE):
            print(f"❌ Error: JSON file not found at {JSON_FILE}")
            sys.exit(1)
        
        file_size = os.path.getsize(JSON_FILE)
        print(f"📊 File size: {file_size / (1024*1024):.2f} MB")
        
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ Loaded {len(data):,} records from JSON")
        
    except Exception as e:
        print(f"❌ Error loading JSON: {e}")
        sys.exit(1)
    
    # Insert data in batches
    print(f"\n📥 Inserting data into SQLite...")
    batch_size = 5000
    total_inserted = 0
    batch_num = 0
    
    try:
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            batch_num += 1
            
            for record in batch:
                cursor.execute('''
                    INSERT INTO tweets 
                    (sentiment_label, sentiment_value, tweet_id, created_at, query, user, text)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    record.get('sentiment', 'unknown'),
                    record.get('sentiment_value', 0),
                    str(record.get('id', '')),
                    str(record.get('date', '')),
                    str(record.get('query', '')),
                    str(record.get('user', '')),
                    str(record.get('text', ''))
                ))
                total_inserted += 1
            
            conn.commit()
            
            if batch_num % 10 == 0:
                print(f"   ✅ Batch {batch_num}: {total_inserted:,} records inserted")
        
        print(f"\n" + "="*70)
        print(f"✨ INGESTION COMPLETE!")
        print(f"   Total documents inserted: {total_inserted:,}")
        
        # Get database file size
        db_size = os.path.getsize(DATABASE_FILE)
        print(f"   Database size: {db_size / (1024*1024):.2f} MB")
        
        # Verify count
        cursor.execute('SELECT COUNT(*) FROM tweets')
        count = cursor.fetchone()[0]
        print(f"   Final record count: {count:,}")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error during ingestion: {e}")
        conn.close()
        sys.exit(1)
    finally:
        conn.close()
        print("\n🔌 SQLite connection closed")


# ==================== MAIN ====================

if __name__ == "__main__":
    load_json_and_insert()
