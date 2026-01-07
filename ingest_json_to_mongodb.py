#!/usr/bin/env python3
"""
JSON Data Ingestion Script - Load Kaggle Sentiment140 Dataset JSON into MongoDB Atlas
Processes: training_data.json (1.6M tweets in JSON format)
Output: MongoDB Atlas TwitterDB.tweets collection
"""

from pymongo import MongoClient
from pymongo.server_api import ServerApi
import json
import sys
from datetime import datetime
import certifi
import os

# ==================== CONFIGURATION ====================

MONGO_URI = "mongodb+srv://jeevanandhm_db_user:1234567jeeva@cluster0.umcf1y7.mongodb.net/?appName=Cluster0"
DATABASE_NAME = "TwitterDB"
COLLECTION_NAME = "tweets"
JSON_FILE = r"training_data.json"

# ==================== FUNCTIONS ====================

def get_mongodb_collection():
    """Connect to MongoDB Atlas"""
    try:
        client = MongoClient(
            MONGO_URI, 
            server_api=ServerApi('1'),
            tlsCAFile=certifi.where(),
            retryWrites=True,
            retryReads=True,
            connectTimeoutMS=30000,
            serverSelectionTimeoutMS=30000
        )
        client.admin.command('ping')
        print("✅ Connected to MongoDB Atlas successfully!")
        
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        return collection, client
    except Exception as e:
        print(f"❌ Error connecting to MongoDB Atlas: {e}")
        sys.exit(1)


def load_json_data(filepath, batch_size=5000):
    """
    Load JSON data in batches and yield them.
    """
    print(f"\n📂 Loading JSON file: {filepath}")
    
    try:
        # Check if file exists
        if not os.path.exists(filepath):
            print(f"❌ Error: JSON file not found at {filepath}")
            sys.exit(1)
        
        # Get file size
        file_size = os.path.getsize(filepath)
        print(f"📊 File size: {file_size / (1024*1024):.2f} MB")
        
        # Load entire JSON file
        print("📥 Reading JSON file...")
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ Loaded {len(data):,} records from JSON")
        
        # Yield data in batches
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            print(f"   📦 Batch {i//batch_size + 1}: {len(batch)} records")
            yield batch
            
    except Exception as e:
        print(f"❌ Error loading JSON: {e}")
        sys.exit(1)


def preprocess_batch(batch):
    """
    Preprocess a batch of JSON data into MongoDB documents.
    """
    documents = []
    
    for record in batch:
        try:
            doc = {
                'sentiment_label': record.get('sentiment', 'unknown'),
                'sentiment_value': record.get('sentiment_value', 0),
                'tweet_id': str(record.get('id', '')),
                'created_at': str(record.get('date', '')),
                'query': str(record.get('query', '')),
                'user': {'username': str(record.get('user', ''))},
                'text': str(record.get('text', '')),
                'ingested_at': datetime.utcnow()
            }
            documents.append(doc)
        except Exception as e:
            print(f"   ⚠️  Error processing record: {e}")
            continue
    
    return documents


def insert_data_in_batches():
    """Main orchestration function"""
    print("\n" + "="*70)
    print("🚀 JSON DATA INGESTION TO MONGODB ATLAS")
    print("="*70)
    print(f"\n📋 Configuration:")
    print(f"   - JSON File: {JSON_FILE}")
    print(f"   - Database: {DATABASE_NAME}")
    print(f"   - Collection: {COLLECTION_NAME}")
    print(f"   - MongoDB Atlas Cluster: cluster0 (umcf1y7)")
    
    print(f"\n🔗 Connecting to MongoDB Atlas...")
    collection, client = get_mongodb_collection()
    
    # Check existing documents
    doc_count = collection.count_documents({})
    print(f"\n📊 Current collection status: {doc_count} documents")
    
    if doc_count > 0:
        print(f"\n⚠️  Collection already has {doc_count} documents")
        response = input("Clear existing data and proceed? (y/n): ").strip().lower()
        if response == 'y':
            collection.delete_many({})
            print("✅ Collection cleared")
        else:
            print("⏭️  Skipping ingestion")
            client.close()
            return
    
    # Load and process JSON
    total_inserted = 0
    batch_num = 0
    
    try:
        print(f"\n📦 Processing JSON data...")
        for batch in load_json_data(JSON_FILE, batch_size=5000):
            batch_num += 1
            
            # Preprocess batch
            documents = preprocess_batch(batch)
            
            # Insert into MongoDB
            if documents:
                result = collection.insert_many(documents, ordered=False)
                inserted = len(result.inserted_ids)
                total_inserted += inserted
                
                if batch_num % 10 == 0:
                    print(f"\n   ✅ Batch {batch_num}: Inserted {inserted} documents")
                    print(f"   📈 Running total: {total_inserted:,} documents")
        
        print(f"\n" + "="*70)
        print(f"✨ INGESTION COMPLETE!")
        print(f"   Total documents inserted: {total_inserted:,}")
        
        # Create indexes for query optimization
        create_indexes(collection)
        
        # Final verification
        final_count = collection.count_documents({})
        print(f"   Final collection count: {final_count:,} documents")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error during ingestion: {e}")
        sys.exit(1)
    finally:
        client.close()
        print("\n🔌 MongoDB connection closed")


def create_indexes(collection):
    """Create indexes for optimal query performance"""
    print(f"\n🔑 Creating database indexes...")
    
    try:
        # Index on sentiment for aggregations
        collection.create_index("sentiment_label")
        print("   ✅ Index on sentiment_label")
        
        # Index on timestamp
        collection.create_index("created_at")
        print("   ✅ Index on created_at")
        
        # Index on user for user-based queries
        collection.create_index("user.username")
        print("   ✅ Index on user.username")
        
        # Text index on text field for full-text search
        collection.create_index([("text", "text")])
        print("   ✅ Text index on text field")
        
    except Exception as e:
        print(f"   ⚠️  Warning creating indexes: {e}")


# ==================== MAIN ====================

if __name__ == "__main__":
    insert_data_in_batches()
