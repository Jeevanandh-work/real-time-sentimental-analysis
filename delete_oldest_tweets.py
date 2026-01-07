#!/usr/bin/env python3
"""
Delete oldest tweets to free up MongoDB quota
Delete 20% of tweets to get back under quota
"""

import sys
sys.path.insert(0, 'scripts')

from pymongo import MongoClient
from pymongo.server_api import ServerApi
import certifi

def delete_oldest_tweets():
    """
    Delete oldest tweets to free up space
    """
    print("="*70)
    print("🗑️  DELETING OLDEST TWEETS TO FREE QUOTA")
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
    tweets = db["tweets"]
    
    # Get initial count
    initial_count = tweets.count_documents({})
    print(f"\n📊 Initial tweet count: {initial_count:,}")
    
    # We need to delete ~200K tweets to free ~74 MB
    # This is roughly 17% of the dataset
    target_to_delete = int(initial_count * 0.18)  # Delete 18%
    
    print(f"🎯 Target to delete: {target_to_delete:,} tweets ({target_to_delete/initial_count*100:.1f}%)")
    print(f"📈 Expected to keep: {initial_count - target_to_delete:,} tweets")
    
    # Delete oldest tweets (by _id ObjectId which has timestamp)
    print(f"\n🗑️  Deleting oldest {target_to_delete:,} tweets...")
    
    try:
        # Get the ObjectId of the tweet at position target_to_delete
        old_tweets = tweets.find().sort("_id", 1).limit(target_to_delete)
        oldest_ids = [doc["_id"] for doc in old_tweets]
        
        if oldest_ids:
            result = tweets.delete_many({"_id": {"$in": oldest_ids}})
            deleted = result.deleted_count
            
            print(f"✅ Deleted {deleted:,} oldest tweets")
            
            final_count = tweets.count_documents({})
            print(f"\n" + "="*70)
            print(f"✅ DELETION COMPLETE")
            print("="*70)
            print(f"\nTweets before: {initial_count:,}")
            print(f"Tweets after: {final_count:,}")
            print(f"Tweets deleted: {deleted:,}")
            print(f"Reduction: {deleted/initial_count*100:.1f}%")
            
            # Estimate space freed
            initial_mb = 442.78
            estimated_freed_mb = (deleted / initial_count) * initial_mb
            estimated_remaining_mb = initial_mb - estimated_freed_mb
            
            print(f"\n💾 Estimated storage impact:")
            print(f"   Before: {initial_mb:.2f} MB")
            print(f"   Freed: {estimated_freed_mb:.2f} MB")
            print(f"   After: {estimated_remaining_mb:.2f} MB of 512 MB")
            print(f"   Available for MapReduce: {512 - estimated_remaining_mb:.2f} MB")
            
            if 512 - estimated_remaining_mb > 50:
                print(f"\n✅ Should have enough space now for MapReduce analysis!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    delete_oldest_tweets()
