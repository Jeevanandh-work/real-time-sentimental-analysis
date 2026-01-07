#!/usr/bin/env python3
"""
Continue ingesting remaining tweets up to 1,500,000 from CSV and JSON files into MongoDB Atlas
"""

import sys
sys.path.insert(0, 'scripts')

from mongo_connection import get_collection
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import pandas as pd
import json
import re
import certifi

def continue_ingestion_to_1500000():
    """
    Continue ingesting tweets from CSV and JSON until we reach 1,500,000
    """
    print("="*70)
    print("🔄 CONTINUING TWEET INGESTION TO 1,500,000")
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
            retryReads=False,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000
        )
        
        client.admin.command('ping')
        print("✅ Connected to MongoDB Atlas successfully!")
        
        db = client["TwitterDB"]
        coll = db["tweets"]
        
        # Check current count
        current_count = coll.count_documents({})
        print(f"\n📊 Current tweets in database: {current_count:,}")
        
        target_count = 1500000
        remaining_needed = target_count - current_count
        
        if remaining_needed <= 0:
            print(f"✅ Already have {current_count:,} tweets (target reached!)")
            return
        
        print(f"📈 Need to insert: {remaining_needed:,} more tweets")
        
        tweets_to_insert = []
        
        # Load from CSV
        print("\n📦 Loading from CSV file...")
        csv_path = "training.1600000.processed.noemoticon.csv"
        df = pd.read_csv(csv_path, encoding='latin-1', header=None)
        df.columns = ['sentiment', 'target_id', 'date', 'query_flag', 'user', 'text']
        
        print(f"✅ Loaded {len(df)} tweets from CSV")
        
        # Transform CSV data
        print("🔄 Transforming CSV data...")
        sentiment_map = {0: 'negative', 2: 'neutral', 4: 'positive'}
        df['sentiment_label'] = df['sentiment'].map(sentiment_map)
        
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
            tweets_to_insert.append(tweet_obj)
            
            if (idx + 1) % 200000 == 0:
                print(f"   Processed {idx + 1} tweets from CSV...")
        
        print(f"✅ Ready to insert {len(tweets_to_insert)} tweets from CSV")
        
        # Load from JSON
        print("\n📦 Loading from JSON file...")
        json_path = "training_data.json"
        json_tweets = []
        
        with open(json_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        tweet = json.loads(line)
                        json_tweets.append(tweet)
                    except:
                        pass
        
        print(f"✅ Loaded {len(json_tweets)} tweets from JSON")
        
        # Add JSON tweets
        for tweet in json_tweets:
            tweet_obj = {
                "tweet_id": tweet.get('tweet_id', f"json_{len(tweets_to_insert)}"),
                "created_at": tweet.get('created_at', ''),
                "text": tweet.get('text', ''),
                "user": tweet.get('user', {'id': '', 'name': ''}),
                "sentiment_label": tweet.get('sentiment_label', 'neutral'),
                "sentiment_score": float(tweet.get('sentiment_score', 0.0)),
                "hashtags": tweet.get('hashtags', []),
                "clean_text": tweet.get('clean_text', tweet.get('text', ''))
            }
            tweets_to_insert.append(tweet_obj)
        
        print(f"✅ Total ready to insert: {len(tweets_to_insert)} tweets")
        
        # Insert with deduplication
        print(f"\n💾 Inserting tweets into MongoDB (with deduplication)...")
        print(f"   Target: {target_count:,} total tweets")
        
        inserted_count = 0
        duplicate_count = 0
        batch_size = 5000
        
        for i in range(0, len(tweets_to_insert), batch_size):
            batch = tweets_to_insert[i:i+batch_size]
            
            for tweet in batch:
                try:
                    # Check if tweet_id already exists
                    existing = coll.find_one({"tweet_id": tweet["tweet_id"]})
                    if not existing:
                        coll.insert_one(tweet)
                        inserted_count += 1
                    else:
                        duplicate_count += 1
                except Exception as e:
                    print(f"   ⚠️  Error inserting tweet: {e}")
            
            new_total = coll.count_documents({})
            batch_num = i // batch_size + 1
            total_batches = (len(tweets_to_insert) + batch_size - 1) // batch_size
            print(f"   ✅ Batch {batch_num}/{total_batches}: Total tweets now: {new_total:,} (inserted: {inserted_count}, skipped duplicates: {duplicate_count})")
            
            # Stop if we reach target
            if new_total >= target_count:
                print(f"\n✅ Reached target of {target_count:,} tweets!")
                break
        
        # Final verification
        final_count = coll.count_documents({})
        stats = db.command("collStats", "tweets")
        size_mb = stats.get('size', 0) / 1024 / 1024
        
        print("\n" + "="*70)
        print("✅ INGESTION COMPLETE!")
        print("="*70)
        print(f"📊 Final tweet count: {final_count:,}")
        print(f"📦 Collection size: {size_mb:.2f} MB")
        print(f"📈 Inserted in this session: {inserted_count:,}")
        print(f"⏭️  Skipped duplicates: {duplicate_count:,}")
        
        # Show sentiment distribution
        print("\n📊 SENTIMENT DISTRIBUTION:")
        positive = coll.count_documents({"sentiment_label": "positive"})
        negative = coll.count_documents({"sentiment_label": "negative"})
        neutral = coll.count_documents({"sentiment_label": "neutral"})
        
        print(f"   Positive: {positive:,} ({positive/final_count*100:.1f}%)")
        print(f"   Negative: {negative:,} ({negative/final_count*100:.1f}%)")
        print(f"   Neutral:  {neutral:,} ({neutral/final_count*100:.1f}%)")
        
        print("\n✅ Ready for MapReduce analysis!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    continue_ingestion_to_1500000()
