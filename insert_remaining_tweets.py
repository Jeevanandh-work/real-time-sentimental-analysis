#!/usr/bin/env python3
"""
Insert remaining tweets to reach 1.6M total
Continues from where the previous ingestion left off
"""

import sys
sys.path.insert(0, 'scripts')

from pymongo import MongoClient
from pymongo.server_api import ServerApi
import pandas as pd
import re
import certifi
import json

def insert_remaining_tweets():
    """
    Insert remaining tweets from CSV to reach 1.6M
    """
    print("="*70)
    print("🚀 INSERTING REMAINING TWEETS TO REACH 1.6M")
    print("="*70)
    
    # Connect to MongoDB
    print("\n📡 Connecting to MongoDB Atlas...")
    uri = "mongodb+srv://jeevanandhm_db_user:1234567jeeva@cluster0.umcf1y7.mongodb.net/?appName=Cluster0"
    client = MongoClient(
        uri, 
        server_api=ServerApi('1'),
        tlsCAFile=certifi.where(),
        retryWrites=False,
        retryReads=False,
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000
    )
    
    try:
        client.admin.command('ping')
        print("✅ Connected to MongoDB Atlas")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    db = client["TwitterDB"]
    coll = db["tweets"]
    
    # Check current count
    print("\n📊 Checking current tweet count...")
    current_count = coll.count_documents({})
    print(f"   Current tweets: {current_count:,}")
    
    target_count = 1600000
    remaining_needed = target_count - current_count
    
    if remaining_needed <= 0:
        print(f"✅ Already have {current_count:,} tweets (target reached!)")
        return
    
    print(f"📈 Need to insert: {remaining_needed:,} more tweets")
    print(f"   Target: {target_count:,}")
    
    # Load CSV
    print("\n📦 Loading CSV dataset...")
    csv_path = "training.1600000.processed.noemoticon.csv"
    
    try:
        df = pd.read_csv(csv_path, encoding='latin-1', header=None, nrows=None)
        df.columns = ['sentiment', 'target_id', 'date', 'query_flag', 'user', 'text']
        print(f"✅ Loaded {len(df)} tweets from CSV")
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return
    
    # Transform data
    print("\n🔄 Transforming data...")
    sentiment_map = {0: 'negative', 2: 'neutral', 4: 'positive'}
    df['sentiment_label'] = df['sentiment'].map(sentiment_map)
    
    # Get existing tweet IDs for deduplication
    print("📋 Getting existing tweet IDs...")
    existing_ids = set(doc['tweet_id'] for doc in coll.find({}, {"tweet_id": 1}))
    print(f"   Existing: {len(existing_ids)} tweet IDs\n")
    
    tweets_to_insert = []
    for idx, row in df.iterrows():
        tweet_id = str(row['target_id'])
        
        # Skip if already exists
        if tweet_id in existing_ids:
            continue
        
        tweet_obj = {
            "tweet_id": tweet_id,
            "created_at": row['date'],
            "text": str(row['text']),
            "user": {"id": str(row['user']), "name": str(row['user'])},
            "sentiment_label": row['sentiment_label'],
            "sentiment_score": 1.0 if row['sentiment_label'] == 'positive' else (-1.0 if row['sentiment_label'] == 'negative' else 0.0),
            "hashtags": [tag for tag in re.findall(r'#\w+', str(row['text']))],
            "clean_text": str(row['text'])
        }
        tweets_to_insert.append(tweet_obj)
        
        # Stop if we have enough
        if len(tweets_to_insert) >= remaining_needed:
            break
    
    print(f"✅ Prepared {len(tweets_to_insert)} new tweets for insertion\n")
    
    # Insert in batches with clear progress
    print("💾 INSERTING DATA:")
    batch_size = 5000
    total_inserted = 0
    
    for i in range(0, len(tweets_to_insert), batch_size):
        batch = tweets_to_insert[i:i+batch_size]
        
        try:
            coll.insert_many(batch, ordered=False)
            total_inserted += len(batch)
            print(f"✅ Inserted {len(batch):,} tweets", end=" ")
            
            # Check current total
            new_total = coll.count_documents({})
            
            # Check if we've reached target
            if new_total >= target_count:
                print(f"\n\n✅ REACHED TARGET OF {target_count:,} TWEETS!")
                break
        except Exception as e:
            print(f"⚠️  Error: {e}", end=" ")
            continue
    
    # Final verification
    print("\n\n" + "="*70)
    final_count = coll.count_documents({})
    print(f"✅ INSERTION COMPLETE!")
    print("="*70)
    print(f"\n📊 Final Statistics:")
    print(f"   Total tweets: {final_count:,}")
    print(f"   Target: {target_count:,}")
    
    if final_count >= target_count:
        print(f"   ✅ TARGET REACHED! 🎉")
    else:
        remaining = target_count - final_count
        print(f"   ⏳ Still need: {remaining:,} more tweets")
    
    # Show sentiment distribution
    print(f"\n📈 Sentiment Distribution:")
    positive = coll.count_documents({"sentiment_label": "positive"})
    negative = coll.count_documents({"sentiment_label": "negative"})
    neutral = coll.count_documents({"sentiment_label": "neutral"})
    
    total = positive + negative + neutral
    if total > 0:
        print(f"   Positive: {positive:,} ({positive/total*100:.1f}%)")
        print(f"   Negative: {negative:,} ({negative/total*100:.1f}%)")
        print(f"   Neutral:  {neutral:,} ({neutral/total*100:.1f}%)")
    
    print(f"\n✅ Dataset ready for MapReduce analysis!")

if __name__ == "__main__":
    insert_remaining_tweets()
