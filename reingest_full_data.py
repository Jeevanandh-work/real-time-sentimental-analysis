#!/usr/bin/env python3
"""
Re-ingest the full 1,600,000 Kaggle dataset into MongoDB Atlas
"""

import sys
sys.path.insert(0, 'scripts')

from mongo_connection import get_collection
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import pandas as pd
import certifi
import re

def reingest_full_kaggle():
    """
    Load and ingest the full Kaggle Sentiment140 dataset.
    """
    print("="*70)
    print("🔄 RE-INGESTING FULL 1,600,000 KAGGLE DATASET")
    print("="*70)
    
    # Connect to MongoDB
    print("\n📡 Connecting to MongoDB Atlas...")
    try:
        uri = "mongodb+srv://jeevanandhm_db_user:1234567jeeva@cluster0.umcf1y7.mongodb.net/?appName=Cluster0"
        client = MongoClient(
            uri, 
            server_api=ServerApi('1'),
            tlsCAFile=certifi.where(),
            retryWrites=False,
            retryReads=False
        )
        
        client.admin.command('ping')
        print("✅ Connected to MongoDB Atlas successfully!")
        
        db = client["TwitterDB"]
        coll = db["tweets"]
        
        # Delete existing tweets to make room
        print("\n🗑️  Clearing existing tweets collection...")
        delete_result = coll.delete_many({})
        print(f"✅ Deleted {delete_result.deleted_count} existing tweets")
        
        # Load Kaggle CSV
        print("\n📦 Loading Kaggle Sentiment140 dataset (1,600,000 tweets)...")
        print("   This may take a few minutes...")
        
        csv_path = "training.1600000.processed.noemoticon.csv"
        df = pd.read_csv(csv_path, encoding='latin-1', header=None)
        df.columns = ['sentiment', 'target_id', 'date', 'query_flag', 'user', 'text']
        
        print(f"✅ Loaded {len(df)} tweets from CSV")
        
        # Transform data
        print("\n🔄 Transforming data...")
        sentiment_map = {0: 'negative', 2: 'neutral', 4: 'positive'}
        df['sentiment_label'] = df['sentiment'].map(sentiment_map)
        
        tweets = []
        for idx, row in df.iterrows():
            tweet_obj = {
                "tweet_id": str(row['target_id']),
                "created_at": row['date'],
                "text": str(row['text']),
                "user": {"id": str(row['user']), "name": str(row['user'])},
                "sentiment_label": row['sentiment_label'],
                "sentiment_score": 1.0 if row['sentiment_label'] == 'positive' else (-1.0 if row['sentiment_label'] == 'negative' else 0.0),
                "hashtags": [tag for tag in re.findall(r'#\w+', str(row['text']))],
                "clean_text": str(row['text'])
            }
            tweets.append(tweet_obj)
            
            # Progress indicator
            if (idx + 1) % 200000 == 0:
                print(f"   Processed {idx + 1} tweets...")
        
        print(f"✅ Transformed {len(tweets)} tweets")
        
        # Insert into MongoDB
        print(f"\n💾 Inserting {len(tweets)} tweets into MongoDB...")
        print("   This may take several minutes...")
        
        # Insert in batches
        batch_size = 10000
        for i in range(0, len(tweets), batch_size):
            batch = tweets[i:i+batch_size]
            coll.insert_many(batch)
            print(f"   ✅ Inserted batch {i//batch_size + 1}/{(len(tweets)+batch_size-1)//batch_size}")
        
        # Verify
        count = coll.count_documents({})
        print(f"\n✅ ALL DATA RE-INGESTED SUCCESSFULLY!")
        print(f"   Total tweets in database: {count:,}")
        
        # Get collection stats
        stats = db.command("collStats", "tweets")
        size_mb = stats.get('size', 0) / 1024 / 1024
        print(f"   Collection size: {size_mb:.2f} MB")
        
        # Show sentiment distribution
        print("\n📊 SENTIMENT DISTRIBUTION:")
        positive = coll.count_documents({"sentiment_label": "positive"})
        negative = coll.count_documents({"sentiment_label": "negative"})
        neutral = coll.count_documents({"sentiment_label": "neutral"})
        
        print(f"   Positive: {positive:,}")
        print(f"   Negative: {negative:,}")
        print(f"   Neutral:  {neutral:,}")
        
        print("\n" + "="*70)
        print("✅ RE-INGESTION COMPLETE - READY TO RUN MAPREDUCE!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise

if __name__ == "__main__":
    reingest_full_kaggle()
