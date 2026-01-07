#!/usr/bin/env python3
"""
Export MapReduce Results to MongoDB Atlas
Saves all MapReduce aggregation results as a new collection in MongoDB
"""

from pymongo import MongoClient
from datetime import datetime
import json

# ============================================================================
# MONGODB CONNECTION
# ============================================================================

def connect_mongodb():
    """Connect to MongoDB Atlas"""
    try:
        uri = "mongodb+srv://jeevanandhm_db_user:1234567jeeva@cluster0.umcf1y7.mongodb.net/?appName=Cluster0&retryWrites=true&w=majority"
        client = MongoClient(
            uri,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=15000,
            retryWrites=True,
            retryReads=True,
            tlsAllowInvalidCertificates=True,
            tlsAllowInvalidHostnames=True
        )
        
        # Test connection
        client.admin.command('ping')
        print("[SUCCESS] Connected to MongoDB Atlas!")
        
        db = client["TwitterDB"]
        return db, True
    
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        return None, False

# ============================================================================
# MAPREDUCE FUNCTIONS
# ============================================================================

def get_sentiment_distribution(coll):
    """Get sentiment distribution - Map/Reduce Phase"""
    try:
        pipeline = [
            {"$group": {
                "_id": "$sentiment_label",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]
        
        results = list(coll.aggregate(pipeline))
        
        mapreduce_data = []
        total = sum(r["count"] for r in results)
        
        for result in results:
            mapreduce_data.append({
                "map_key": result["_id"],
                "reduce_value": {
                    "count": result["count"],
                    "percentage": round((result["count"] / total * 100), 2) if total > 0 else 0
                },
                "type": "sentiment_distribution"
            })
        
        return mapreduce_data
    except Exception as e:
        print(f"[ERROR] Sentiment distribution: {e}")
        return []

def get_top_users_mapreduce(coll, limit=15):
    """Get top users - Map/Reduce Phase"""
    try:
        pipeline = [
            {"$group": {
                "_id": "$user",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        
        results = list(coll.aggregate(pipeline))
        
        mapreduce_data = []
        total = sum(r["count"] for r in results)
        
        for result in results:
            user = result["_id"]
            if isinstance(user, dict):
                username = user.get("username", user.get("name", "Unknown"))
            else:
                username = str(user)
            
            mapreduce_data.append({
                "map_key": username,
                "reduce_value": {
                    "tweet_count": result["count"],
                    "percentage": round((result["count"] / total * 100), 2) if total > 0 else 0
                },
                "type": "top_users"
            })
        
        return mapreduce_data
    except Exception as e:
        print(f"[ERROR] Top users: {e}")
        return []

def get_sentiment_stats_mapreduce(coll):
    """Get sentiment statistics - Map/Reduce Phase"""
    try:
        pipeline = [
            {"$group": {
                "_id": "$sentiment_label",
                "count": {"$sum": 1},
                "avg_length": {"$avg": {"$strLenCP": "$text"}},
                "min_length": {"$min": {"$strLenCP": "$text"}},
                "max_length": {"$max": {"$strLenCP": "$text"}},
                "total_chars": {"$sum": {"$strLenCP": "$text"}}
            }},
            {"$sort": {"count": -1}}
        ]
        
        results = list(coll.aggregate(pipeline))
        
        mapreduce_data = []
        
        for result in results:
            mapreduce_data.append({
                "map_key": result["_id"],
                "reduce_value": {
                    "count": result["count"],
                    "statistics": {
                        "avg_length": round(result["avg_length"], 2),
                        "min_length": result["min_length"],
                        "max_length": result["max_length"],
                        "total_chars": result["total_chars"]
                    }
                },
                "type": "sentiment_statistics"
            })
        
        return mapreduce_data
    except Exception as e:
        print(f"[ERROR] Sentiment stats: {e}")
        return []

def get_user_sentiment_mapreduce(coll, limit=50):
    """Get user-sentiment breakdown - Map/Reduce Phase"""
    try:
        pipeline = [
            {"$group": {
                "_id": {
                    "user": "$user",
                    "sentiment": "$sentiment_label"
                },
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        
        results = list(coll.aggregate(pipeline))
        
        mapreduce_data = []
        
        for result in results:
            user = result["_id"]["user"]
            if isinstance(user, dict):
                username = user.get("username", user.get("name", "Unknown"))
            else:
                username = str(user)
            
            map_key = f"{username}_{result['_id']['sentiment']}"
            
            mapreduce_data.append({
                "map_key": map_key,
                "reduce_value": {
                    "user": username,
                    "sentiment": result["_id"]["sentiment"],
                    "count": result["count"]
                },
                "type": "user_sentiment"
            })
        
        return mapreduce_data
    except Exception as e:
        print(f"[ERROR] User-sentiment: {e}")
        return []

def get_political_tweets_mapreduce(coll):
    """Get political tweets - Map/Reduce Phase"""
    try:
        political_keywords = [
            'politic', 'election', 'government', 'vote', 'president',
            'congress', 'senate', 'democrat', 'republican', 'trump',
            'obama', 'campaign', 'party', 'law', 'policy',
            'federal', 'state', 'bill', 'house', 'representative',
            'senator', 'electoral', 'ballot', 'legislation'
        ]
        
        pipeline = [
            {"$match": {
                "text": {"$regex": "|".join(political_keywords), "$options": "i"}
            }},
            {"$group": {
                "_id": "$sentiment_label",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]
        
        results = list(coll.aggregate(pipeline))
        
        mapreduce_data = []
        total = sum(r["count"] for r in results)
        
        for result in results:
            mapreduce_data.append({
                "map_key": result["_id"],
                "reduce_value": {
                    "count": result["count"],
                    "percentage": round((result["count"] / total * 100), 2) if total > 0 else 0
                },
                "type": "political_sentiment"
            })
        
        return mapreduce_data
    except Exception as e:
        print(f"[ERROR] Political tweets: {e}")
        return []

# ============================================================================
# EXPORT TO MONGODB
# ============================================================================

def export_mapreduce_results(db, tweets_coll):
    """Export all MapReduce results to MongoDB"""
    
    print("\n" + "="*70)
    print("EXPORTING MAPREDUCE RESULTS TO MONGODB ATLAS")
    print("="*70)
    
    # Create or get mapreduce collection
    mapreduce_coll = db["mapreduce_results"]
    
    # Delete existing data to avoid duplicates
    print("\n🗑️  Cleaning existing MapReduce results...")
    mapreduce_coll.delete_many({})
    
    # 1. Sentiment Distribution
    print("\n📊 Processing: Sentiment Distribution (Map/Reduce)...")
    sentiment_dist = get_sentiment_distribution(tweets_coll)
    for doc in sentiment_dist:
        doc["exported_at"] = datetime.now()
    mapreduce_coll.insert_many(sentiment_dist)
    print(f"   ✅ Exported {len(sentiment_dist)} sentiment records")
    
    # 2. Top Users
    print("\n👥 Processing: Top Users (Map/Reduce)...")
    top_users = get_top_users_mapreduce(tweets_coll)
    for doc in top_users:
        doc["exported_at"] = datetime.now()
    mapreduce_coll.insert_many(top_users)
    print(f"   ✅ Exported {len(top_users)} user records")
    
    # 3. Sentiment Statistics
    print("\n📈 Processing: Sentiment Statistics (Map/Reduce)...")
    sentiment_stats = get_sentiment_stats_mapreduce(tweets_coll)
    for doc in sentiment_stats:
        doc["exported_at"] = datetime.now()
    mapreduce_coll.insert_many(sentiment_stats)
    print(f"   ✅ Exported {len(sentiment_stats)} statistics records")
    
    # 4. User-Sentiment Breakdown
    print("\n👤 Processing: User-Sentiment Breakdown (Map/Reduce)...")
    user_sentiment = get_user_sentiment_mapreduce(tweets_coll)
    for doc in user_sentiment:
        doc["exported_at"] = datetime.now()
    mapreduce_coll.insert_many(user_sentiment)
    print(f"   ✅ Exported {len(user_sentiment)} user-sentiment records")
    
    # 5. Political Tweets
    print("\n🏛️  Processing: Political Tweets (Map/Reduce)...")
    political = get_political_tweets_mapreduce(tweets_coll)
    for doc in political:
        doc["exported_at"] = datetime.now()
    mapreduce_coll.insert_many(political)
    print(f"   ✅ Exported {len(political)} political records")
    
    # Get summary
    total_exported = mapreduce_coll.count_documents({})
    
    print("\n" + "="*70)
    print("MAPREDUCE EXPORT SUMMARY")
    print("="*70)
    print(f"✅ Total MapReduce key-value pairs exported: {total_exported}")
    print(f"📍 Collection: TwitterDB.mapreduce_results")
    print(f"⏰ Export time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Show sample data
    print("\n📋 Sample MapReduce Key-Value Pairs:")
    print("-" * 70)
    
    samples = list(mapreduce_coll.find().limit(5))
    for i, sample in enumerate(samples, 1):
        print(f"\n{i}. Type: {sample.get('type', 'N/A')}")
        print(f"   Map Key: {sample.get('map_key', 'N/A')}")
        print(f"   Reduce Value: {json.dumps(sample.get('reduce_value', {}), indent=2)}")
    
    print("\n" + "="*70)
    print("✅ MAPREDUCE RESULTS SUCCESSFULLY EXPORTED TO MONGODB!")
    print("="*70)
    
    return total_exported

# ============================================================================
# QUERY MAPREDUCE RESULTS
# ============================================================================

def query_mapreduce_results(db):
    """Query and display MapReduce results"""
    
    print("\n" + "="*70)
    print("QUERYING MAPREDUCE RESULTS FROM MONGODB")
    print("="*70)
    
    mapreduce_coll = db["mapreduce_results"]
    
    # Group by type
    types = mapreduce_coll.distinct("type")
    
    for type_name in types:
        print(f"\n📊 {type_name.upper()}")
        print("-" * 70)
        
        records = list(mapreduce_coll.find({"type": type_name}).limit(5))
        for record in records:
            print(f"   Map Key: {record['map_key']}")
            print(f"   Reduce Value: {record['reduce_value']}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""
    
    # Connect to MongoDB
    db, connected = connect_mongodb()
    
    if not connected:
        print("[CRITICAL] Failed to connect to MongoDB Atlas!")
        return
    
    # Get collections
    tweets_coll = db["tweets"]
    
    # Check tweets collection
    tweet_count = tweets_coll.count_documents({})
    print(f"[INFO] Total tweets in database: {tweet_count:,}")
    
    if tweet_count == 0:
        print("[ERROR] No tweets found in database!")
        return
    
    # Export MapReduce results
    total_exported = export_mapreduce_results(db, tweets_coll)
    
    # Query MapReduce results
    query_mapreduce_results(db)
    
    print("\n✅ Program completed successfully!")

if __name__ == "__main__":
    main()
