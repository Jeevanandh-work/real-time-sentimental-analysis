#!/usr/bin/env python3
"""
Ingest CSV and JSON data directly into MongoDB Atlas
"""

import sys
sys.path.insert(0, 'scripts')

from pymongo import MongoClient
from pymongo.server_api import ServerApi
import pandas as pd
import json
import certifi
import re
from pathlib import Path

def connect_to_atlas():
    """Connect to MongoDB Atlas"""
    print("📡 Connecting to MongoDB Atlas...")
    uri = "mongodb+srv://jeevanandhm_db_user:1234567jeeva@cluster0.umcf1y7.mongodb.net/?appName=Cluster0"
    client = MongoClient(
        uri, 
        server_api=ServerApi('1'),
        tlsCAFile=certifi.where(),
        retryWrites=False,
        retryReads=False,
        serverSelectionTimeoutMS=5000
    )
    
    client.admin.command('ping')
    print("✅ Connected to MongoDB Atlas successfully!")
    
    db = client["TwitterDB"]
    coll = db["tweets"]
    return coll

def ingest_csv(coll, csv_path):
    """Ingest CSV file into MongoDB"""
    print("\n" + "-"*70)
    print("📦 INGESTING CSV FILE")
    print("-"*70)
    
    print(f"\n📥 Loading {csv_path}...")
    df = pd.read_csv(csv_path, encoding='latin-1', header=None)
    df.columns = ['sentiment', 'target_id', 'date', 'query_flag', 'user', 'text']
    
    print(f"✅ Loaded {len(df):,} tweets from CSV")
    
    # Transform
    print("\n🔄 Transforming data...")
    sentiment_map = {0: 'negative', 2: 'neutral', 4: 'positive'}
    df['sentiment_label'] = df['sentiment'].map(sentiment_map)
    df['sentiment_score'] = df['sentiment'].apply(lambda x: 1.0 if x == 4 else (-1.0 if x == 0 else 0.0))
    df['hashtags'] = df['text'].apply(lambda x: [tag for tag in re.findall(r'#\w+', str(x))])
    
    print(f"✅ Transformed {len(df):,} tweets")
    
    # Insert in batches
    print(f"\n💾 Inserting {len(df):,} tweets into MongoDB...")
    tweets = []
    for _, row in df.iterrows():
        tweet = {
            "tweet_id": str(row['target_id']),
            "created_at": row['date'],
            "text": str(row['text']),
            "user": {"id": str(row['user']), "name": str(row['user'])},
            "sentiment_label": row['sentiment_label'],
            "sentiment_score": row['sentiment_score'],
            "hashtags": row['hashtags'],
            "clean_text": str(row['text'])
        }
        tweets.append(tweet)
        
        if len(tweets) >= 5000:
            try:
                coll.insert_many(tweets, ordered=False)
                print(f"   ✅ Inserted {len(tweets):,} tweets")
            except Exception as e:
                print(f"   ⚠️  Batch insert partial: {e}")
            tweets = []
    
    # Insert remaining
    if tweets:
        try:
            coll.insert_many(tweets, ordered=False)
            print(f"   ✅ Inserted {len(tweets):,} tweets (final batch)")
        except Exception as e:
            print(f"   ⚠️  Final batch partial: {e}")
    
    print("✅ CSV INGESTION COMPLETE")

def ingest_json(coll, json_path):
    """Ingest JSON file into MongoDB"""
    print("\n" + "-"*70)
    print("📦 INGESTING JSON FILE")
    print("-"*70)
    
    print(f"\n📥 Loading {json_path}...")
    tweets = []
    count = 0
    
    with open(json_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    tweet = json.loads(line)
                    tweets.append(tweet)
                    count += 1
                    
                    if len(tweets) >= 5000:
                        try:
                            coll.insert_many(tweets, ordered=False)
                            print(f"   ✅ Inserted {len(tweets):,} tweets")
                        except Exception as e:
                            print(f"   ⚠️  Batch insert partial: {e}")
                        tweets = []
                except:
                    pass
    
    print(f"✅ Loaded {count:,} tweets from JSON")
    
    # Insert remaining
    if tweets:
        try:
            coll.insert_many(tweets, ordered=False)
            print(f"   ✅ Inserted {len(tweets):,} tweets (final batch)")
        except Exception as e:
            print(f"   ⚠️  Final batch partial: {e}")
    
    print("✅ JSON INGESTION COMPLETE")

def get_stats(coll):
    """Show database statistics"""
    print("\n" + "="*70)
    print("📊 DATABASE STATISTICS")
    print("="*70)
    
    try:
        total = coll.count_documents({})
        print(f"\n📈 Total tweets: {total:,}")
        
        # Sentiment distribution
        pipeline = [
            {"$group": {"_id": "$sentiment_label", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        print("\n📊 SENTIMENT DISTRIBUTION:")
        for doc in coll.aggregate(pipeline):
            label = doc.get('_id', 'unknown')
            count = doc.get('count', 0)
            pct = (count / total * 100) if total > 0 else 0
            print(f"   {label:12} : {count:10,} ({pct:6.2f}%)")
        
        # Collection size
        stats = coll.database.command("collStats", "tweets")
        size_mb = stats.get('size', 0) / 1024 / 1024
        print(f"\n💾 Collection size: {size_mb:.2f} MB")
    except Exception as e:
        print(f"⚠️  Error getting stats: {e}")

def main():
    print("\n" + "="*70)
    print("🚀 INGESTING DATA INTO MONGODB ATLAS")
    print("="*70)
    
    try:
        # Connect
        coll = connect_to_atlas()
        
        # Clear existing data
        print("\n🗑️  Clearing existing tweets...")
        result = coll.delete_many({})
        print(f"✅ Deleted {result.deleted_count:,} existing tweets")
        
        # Ingest CSV
        csv_path = 'training.1600000.processed.noemoticon.csv'
        if Path(csv_path).exists():
            ingest_csv(coll, csv_path)
        else:
            print(f"⚠️  CSV not found: {csv_path}")
        
        # Ingest JSON
        json_path = 'training_data.json'
        if Path(json_path).exists():
            ingest_json(coll, json_path)
        else:
            print(f"⚠️  JSON not found: {json_path}")
        
        # Stats
        get_stats(coll)
        
        print("\n" + "="*70)
        print("✅ DATA INGESTION COMPLETE!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise

if __name__ == "__main__":
    main()
