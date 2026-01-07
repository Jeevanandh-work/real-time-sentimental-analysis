#!/usr/bin/env python3
"""
Remove duplicate tweets to reduce dataset size and free up MongoDB quota
"""

import sys
sys.path.insert(0, 'scripts')

from pymongo import MongoClient
from pymongo.server_api import ServerApi
import certifi

def remove_duplicates():
    """
    Remove duplicate tweets, keeping only one copy of each
    """
    print("="*70)
    print("🧹 REMOVING DUPLICATE TWEETS")
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
    
    # Create unique index on tweet_id (will remove duplicates)
    print("\n🔍 Creating unique index on tweet_id...")
    try:
        tweets.create_index("tweet_id", unique=True, background=True)
        print("✅ Unique index created")
    except Exception as e:
        print(f"⚠️  Index creation note: {e}")
    
    # Find duplicates using aggregation
    print("\n🔎 Finding duplicate tweets...")
    try:
        duplicates_pipeline = [
            {"$group": {
                "_id": "$tweet_id",
                "count": {"$sum": 1},
                "ids": {"$push": "$_id"}
            }},
            {"$match": {"count": {"$gt": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        duplicates = list(tweets.aggregate(duplicates_pipeline))
        
        if duplicates:
            print(f"✅ Found {len(duplicates)} duplicate tweet_ids")
            
            total_to_remove = 0
            for dup in duplicates[:10]:  # Show first 10
                count = dup['count']
                total_to_remove += count - 1
                print(f"   • tweet_id {dup['_id']}: {count} copies (remove {count-1})")
            
            # Calculate total duplicates
            total_duplicates_to_remove = sum(dup['count'] - 1 for dup in duplicates)
            print(f"\n📈 Total duplicate documents to remove: {total_duplicates_to_remove:,}")
            
            # Remove duplicates by keeping first, deleting rest
            print("\n🗑️  Removing duplicates...")
            removed_count = 0
            
            for dup in duplicates:
                tweet_id = dup['_id']
                ids_to_keep = dup['ids'][0]  # Keep first occurrence
                ids_to_delete = dup['ids'][1:]  # Delete rest
                
                result = tweets.delete_many({"_id": {"$in": ids_to_delete}})
                removed_count += result.deleted_count
                
                if removed_count % 50000 == 0:
                    print(f"   ✅ Removed {removed_count:,} duplicate documents...")
            
            print(f"\n✅ Removed {removed_count:,} duplicate documents")
        else:
            print("✅ No duplicates found")
    
    except Exception as e:
        print(f"⚠️  Error finding duplicates: {e}")
        print("   Continuing with alternative approach...")
        
        # Alternative: Use aggregation to remove duplicates
        print("\n🔄 Using aggregation pipeline to remove duplicates...")
        try:
            # Get unique tweets
            unique_tweets = list(tweets.aggregate([
                {"$group": {
                    "_id": "$tweet_id",
                    "doc": {"$first": "$$ROOT"}
                }},
                {"$replaceRoot": {"newRoot": "$doc"}}
            ]))
            
            print(f"   Found {len(unique_tweets)} unique tweets")
            
            if len(unique_tweets) < initial_count:
                duplicates_found = initial_count - len(unique_tweets)
                print(f"   Found {duplicates_found} duplicates")
                
                # Drop and recreate collection
                tweets.drop()
                if unique_tweets:
                    tweets.insert_many(unique_tweets)
                    print(f"✅ Recreated collection with {len(unique_tweets)} unique tweets")
        except Exception as e2:
            print(f"❌ Alternative approach failed: {e2}")
    
    # Get final count
    final_count = tweets.count_documents({})
    print(f"\n" + "="*70)
    print(f"✅ DEDUPLICATION COMPLETE")
    print("="*70)
    print(f"\nFinal tweet count: {final_count:,}")
    print(f"Duplicates removed: {initial_count - final_count:,}")
    
    # Check storage
    print("\n💾 Storage after deduplication:")
    stats = db.command("collStats", "tweets")
    size_mb = stats["size"] / (1024 * 1024)
    data_mb = stats["dataSize"] / (1024 * 1024)
    
    print(f"   Data Size: {data_mb:.2f} MB")
    print(f"   Storage Size: {size_mb:.2f} MB")
    
    db_stats = client.admin.command("dbstats", "TwitterDB")
    total_mb = db_stats["storageSize"] / (1024 * 1024)
    remaining = 512 - total_mb
    
    print(f"   Total DB: {total_mb:.2f} MB of 512 MB")
    print(f"   Quota Used: {total_mb/512*100:.1f}%")
    print(f"   Available: {remaining:.2f} MB")
    
    if remaining > 70:
        print(f"\n✅ Now have {remaining:.2f} MB for MapReduce analysis!")
    else:
        print(f"\n⚠️  Only {remaining:.2f} MB remaining - may need more cleanup")

if __name__ == "__main__":
    remove_duplicates()
