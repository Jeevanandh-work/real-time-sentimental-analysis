#!/usr/bin/env python3
"""
Data Ingestion Script - Load Kaggle Sentiment140 Dataset into MongoDB Atlas
Processes: training.1600000.processed.noemoticon.csv (1.6M tweets)
Output: MongoDB Atlas TwitterDB.tweets collection
"""

from pymongo import MongoClient
from pymongo.server_api import ServerApi
import pandas as pd
import sys
from datetime import datetime
import certifi

# ==================== CONFIGURATION ====================

MONGO_URI = "mongodb+srv://jeevanandhm_db_user:1234567jeeva@cluster0.umcf1y7.mongodb.net/?appName=Cluster0"
DATABASE_NAME = "TwitterDB"
COLLECTION_NAME = "tweets"
CSV_FILE = r"training.1600000.processed.noemoticon.csv"

# Sentiment mapping
SENTIMENT_MAP = {
    0: "negative",
    2: "neutral", 
    4: "positive"
}

# ==================== FUNCTIONS ====================

def get_mongodb_collection():
    """Connect to MongoDB Atlas"""
    try:
        client = MongoClient(
            MONGO_URI, 
            server_api=ServerApi('1'),
            tlsCAFile=certifi.where(),
            retryWrites=True,
            retryReads=True
        )
        client.admin.command('ping')
        print("✅ Connected to MongoDB Atlas successfully!")
        
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        return collection, client
    except Exception as e:
        print(f"❌ Error connecting to MongoDB Atlas: {e}")
        sys.exit(1)


def load_csv_data(filepath, chunk_size=50000):
    """
    Load CSV data in chunks and yield dataframes.
    CSV format: sentiment, id, date, query, user, text
    """
    print(f"\n📂 Loading CSV file: {filepath}")
    
    try:
        # Get file size for progress tracking
        import os
        file_size = os.path.getsize(filepath)
        print(f"📊 File size: {file_size / (1024*1024):.2f} MB")
        
        # Read CSV in chunks
        chunk_count = 0
        for chunk in pd.read_csv(
            filepath, 
            encoding='latin-1',
            header=None,
            names=['sentiment', 'id', 'date', 'query', 'user', 'text'],
            chunksize=chunk_size,
            dtype={'sentiment': int, 'id': str, 'date': str, 'query': str, 'user': str, 'text': str}
        ):
            chunk_count += 1
            print(f"   📦 Chunk {chunk_count}: {len(chunk)} records")
            yield chunk
            
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        sys.exit(1)


def preprocess_chunk(chunk):
    """
    Preprocess a chunk of data and convert to MongoDB documents
    """
    documents = []
    
    for _, row in chunk.iterrows():
        try:
            # Map sentiment
            sentiment_label = SENTIMENT_MAP.get(row['sentiment'], 'neutral')
            
            # Create document
            doc = {
                "tweet_id": str(row['id']),
                "created_at": row['date'],
                "text": str(row['text']),
                "clean_text": str(row['text']).lower(),
                "user": {
                    "id": str(row['user']),
                    "name": str(row['user'])
                },
                "query": str(row['query']),
                "sentiment_label": sentiment_label,
                "sentiment_score": 0.5 if sentiment_label == "positive" else (-0.5 if sentiment_label == "negative" else 0.0),
                "hashtags": [],
                "processed_at": datetime.now()
            }
            documents.append(doc)
        except Exception as e:
            print(f"   ⚠️ Error processing row: {e}")
            continue
    
    return documents


def insert_data_in_batches(collection, filepath, batch_size=10000):
    """
    Load CSV, preprocess, and insert data into MongoDB in batches
    """
    print("\n" + "="*70)
    print("📥 STARTING DATA INGESTION TO MONGODB ATLAS")
    print("="*70)
    
    total_inserted = 0
    batch_counter = 0
    
    try:
        # First, clear existing data
        existing_count = collection.count_documents({})
        if existing_count > 0:
            print(f"\n⚠️ Collection already has {existing_count} documents")
            response = input("Clear existing data? (y/n): ").strip().lower()
            if response == 'y':
                collection.delete_many({})
                print("✅ Cleared existing data")
            else:
                print("⏭️  Skipping data ingestion")
                return
        
        # Load and insert data
        print(f"\n📦 Processing CSV file in chunks...")
        for chunk in load_csv_data(filepath, chunk_size=50000):
            # Preprocess chunk
            documents = preprocess_chunk(chunk)
            
            if documents:
                # Insert batch
                try:
                    result = collection.insert_many(documents, ordered=False)
                    batch_counter += 1
                    total_inserted += len(result.inserted_ids)
                    
                    # Progress update every 10 batches
                    if batch_counter % 10 == 0:
                        print(f"\n   ✅ Batch {batch_counter}: Inserted {len(result.inserted_ids)} documents")
                        print(f"      📊 Total inserted so far: {total_inserted:,}")
                except Exception as insert_error:
                    print(f"   ❌ Error inserting batch {batch_counter}: {insert_error}")
        
        # Final summary
        print("\n" + "="*70)
        print("✅ DATA INGESTION COMPLETED!")
        print("="*70)
        print(f"📊 Total documents inserted: {total_inserted:,}")
        print(f"📦 Total batches processed: {batch_counter}")
        
        # Verify count
        final_count = collection.count_documents({})
        print(f"✅ MongoDB verification: {final_count:,} documents in collection")
        
        return total_inserted
        
    except Exception as e:
        print(f"\n❌ Critical error during ingestion: {e}")
        sys.exit(1)


def create_indexes(collection):
    """Create indexes for better query performance"""
    print("\n📑 Creating indexes...")
    try:
        collection.create_index([("sentiment_label", 1)])
        print("   ✅ Created index: sentiment_label")
        
        collection.create_index([("created_at", -1)])
        print("   ✅ Created index: created_at")
        
        collection.create_index([("user.id", 1)])
        print("   ✅ Created index: user.id")
        
        collection.create_index([("hashtags", 1)])
        print("   ✅ Created index: hashtags")
        
    except Exception as e:
        print(f"   ⚠️ Error creating indexes: {e}")


def main():
    """Main execution function"""
    print("\n" + "="*70)
    print("🚀 KAGGLE SENTIMENT140 DATASET - MONGODB ATLAS INGESTION")
    print("="*70)
    print(f"\n📋 Configuration:")
    print(f"   - CSV File: {CSV_FILE}")
    print(f"   - Database: {DATABASE_NAME}")
    print(f"   - Collection: {COLLECTION_NAME}")
    print(f"   - MongoDB Atlas Cluster: cluster0 (umcf1y7)")
    
    # Connect to MongoDB
    print("\n🔗 Connecting to MongoDB Atlas...")
    collection, client = get_mongodb_collection()
    
    # Show current stats
    current_count = collection.count_documents({})
    print(f"\n📊 Current collection status:")
    print(f"   - Documents: {current_count:,}")
    
    # Insert data
    inserted = insert_data_in_batches(collection, CSV_FILE)
    
    # Create indexes
    if inserted > 0:
        create_indexes(collection)
    
    # Final verification
    final_count = collection.count_documents({})
    print("\n" + "="*70)
    print("📈 FINAL STATUS")
    print("="*70)
    print(f"✅ Total documents in MongoDB Atlas: {final_count:,}")
    print(f"✅ Collection: {DATABASE_NAME}.{COLLECTION_NAME}")
    print(f"✅ Ready for MapReduce analysis!")
    print("="*70 + "\n")
    
    # Close connection
    client.close()


if __name__ == "__main__":
    main()
