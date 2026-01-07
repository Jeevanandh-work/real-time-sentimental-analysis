#!/usr/bin/env python3
"""
MapReduce Analysis - Save results directly to MongoDB
This script runs MapReduce operations using MongoDB's aggregation framework
and saves all results as separate documents in the mapreduce_analysis_results collection
"""

import sys
sys.path.insert(0, '.')

from pymongo import MongoClient
from pymongo.server_api import ServerApi
import certifi
from datetime import datetime

def connect_to_mongodb():
    """Connect to MongoDB Atlas"""
    uri = "mongodb+srv://jeevanandhm_db_user:1234567jeeva@cluster0.umcf1y7.mongodb.net/?appName=Cluster0"
    client = MongoClient(
        uri, 
        server_api=ServerApi('1'),
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000
    )
    
    client.admin.command('ping')
    print("✅ Connected to MongoDB Atlas")
    
    return client["TwitterDB"]

def run_mapreduce_analysis():
    """Run all MapReduce analyses and save to MongoDB"""
    
    print("="*70)
    print("🚀 MAPREDUCE ANALYSIS - SAVING RESULTS TO MONGODB")
    print("="*70)
    
    db = connect_to_mongodb()
    tweets_coll = db["tweets"]
    results_coll = db["mapreduce_analysis_results"]
    
    # Clear old results
    print("\n🗑️  Clearing old results...")
    results_coll.delete_many({})
    print("✅ Cleared old documents")
    
    timestamp = datetime.now().isoformat()
    
    # ==========================================
    # 1. SENTIMENT DISTRIBUTION
    # ==========================================
    print("\n" + "-"*70)
    print("📊 1. SENTIMENT DISTRIBUTION")
    print("-"*70)
    
    try:
        pipeline = [
            {
                "$group": {
                    "_id": "$sentiment_label",
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"count": -1}}
        ]
        
        results = list(tweets_coll.aggregate(pipeline))
        
        sentiment_data = {}
        total = 0
        for item in results:
            sentiment = item["_id"] or "unknown"
            count = item["count"]
            sentiment_data[sentiment] = count
            total += count
        
        doc = {
            "type": "sentiment_distribution",
            "timestamp": timestamp,
            "total_tweets": total,
            "data": sentiment_data,
            "breakdown": {
                "positive": sentiment_data.get("positive", 0),
                "negative": sentiment_data.get("negative", 0),
                "neutral": sentiment_data.get("neutral", 0)
            }
        }
        
        results_coll.insert_one(doc)
        print(f"✅ Saved Sentiment Distribution:")
        print(f"   Total: {total}")
        print(f"   Positive: {sentiment_data.get('positive', 0)}")
        print(f"   Negative: {sentiment_data.get('negative', 0)}")
        print(f"   Neutral: {sentiment_data.get('neutral', 0)}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # ==========================================
    # 2. TOP HASHTAGS
    # ==========================================
    print("\n" + "-"*70)
    print("🏷️  2. TOP HASHTAGS")
    print("-"*70)
    
    try:
        pipeline = [
            {
                "$match": {"hashtags": {"$exists": True, "$ne": []}}
            },
            {
                "$unwind": "$hashtags"
            },
            {
                "$group": {
                    "_id": "$hashtags",
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": 20}
        ]
        
        results = list(tweets_coll.aggregate(pipeline))
        
        hashtags_data = []
        for item in results:
            hashtags_data.append({
                "hashtag": item["_id"],
                "count": item["count"]
            })
        
        doc = {
            "type": "top_hashtags",
            "timestamp": timestamp,
            "limit": 20,
            "total_results": len(hashtags_data),
            "data": hashtags_data
        }
        
        results_coll.insert_one(doc)
        print(f"✅ Saved Top 20 Hashtags:")
        for i, tag in enumerate(hashtags_data[:5], 1):
            print(f"   {i}. {tag['hashtag']}: {tag['count']}")
        print(f"   ... and {len(hashtags_data)-5} more")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # ==========================================
    # 3. SENTIMENT BY HASHTAG
    # ==========================================
    print("\n" + "-"*70)
    print("🏷️  3. SENTIMENT BY TOP HASHTAGS")
    print("-"*70)
    
    try:
        pipeline = [
            {
                "$match": {"hashtags": {"$exists": True, "$ne": []}}
            },
            {
                "$unwind": "$hashtags"
            },
            {
                "$group": {
                    "_id": {
                        "hashtag": "$hashtags",
                        "sentiment": "$sentiment_label"
                    },
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": 100}
        ]
        
        results = list(tweets_coll.aggregate(pipeline))
        
        hashtag_sentiment_data = []
        for item in results:
            hashtag_sentiment_data.append({
                "hashtag": item["_id"]["hashtag"],
                "sentiment": item["_id"]["sentiment"],
                "count": item["count"]
            })
        
        doc = {
            "type": "sentiment_by_hashtag",
            "timestamp": timestamp,
            "total_combinations": len(hashtag_sentiment_data),
            "data": hashtag_sentiment_data
        }
        
        results_coll.insert_one(doc)
        print(f"✅ Saved Sentiment by Hashtag ({len(hashtag_sentiment_data)} combinations)")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # ==========================================
    # 4. TOP USERS
    # ==========================================
    print("\n" + "-"*70)
    print("👥 4. TOP USERS BY TWEET COUNT")
    print("-"*70)
    
    try:
        pipeline = [
            {
                "$match": {"user.name": {"$exists": True, "$ne": ""}}
            },
            {
                "$group": {
                    "_id": "$user.name",
                    "count": {"$sum": 1},
                    "user_id": {"$first": "$user.id"}
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": 15}
        ]
        
        results = list(tweets_coll.aggregate(pipeline))
        
        users_data = []
        for item in results:
            users_data.append({
                "user_name": item["_id"],
                "user_id": item.get("user_id"),
                "tweet_count": item["count"]
            })
        
        doc = {
            "type": "top_users",
            "timestamp": timestamp,
            "limit": 15,
            "total_results": len(users_data),
            "data": users_data
        }
        
        results_coll.insert_one(doc)
        print(f"✅ Saved Top 15 Users:")
        for i, user in enumerate(users_data[:5], 1):
            print(f"   {i}. {user['user_name']}: {user['tweet_count']} tweets")
        print(f"   ... and {len(users_data)-5} more")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # ==========================================
    # 5. POLITICAL TWEETS ANALYSIS
    # ==========================================
    print("\n" + "-"*70)
    print("🏛️  5. POLITICAL TWEETS ANALYSIS")
    print("-"*70)
    
    try:
        keywords = [
            'politic', 'election', 'government', 'vote', 'president',
            'congress', 'senate', 'democrat', 'republican', 'trump',
            'obama', 'campaign', 'party', 'law', 'policy'
        ]
        
        keyword_pattern = "|".join(keywords)
        
        pipeline = [
            {
                "$match": {
                    "text": {"$regex": keyword_pattern, "$options": "i"}
                }
            },
            {
                "$group": {
                    "_id": "$sentiment_label",
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"count": -1}}
        ]
        
        results = list(tweets_coll.aggregate(pipeline))
        
        political_data = {}
        total_political = 0
        for item in results:
            sentiment = item["_id"] or "unknown"
            count = item["count"]
            political_data[sentiment] = count
            total_political += count
        
        doc = {
            "type": "political_analysis",
            "timestamp": timestamp,
            "total_political_tweets": total_political,
            "keywords_used": keywords,
            "data": political_data,
            "breakdown": {
                "positive": political_data.get("positive", 0),
                "negative": political_data.get("negative", 0),
                "neutral": political_data.get("neutral", 0)
            }
        }
        
        results_coll.insert_one(doc)
        print(f"✅ Saved Political Analysis:")
        print(f"   Total Political Tweets: {total_political}")
        print(f"   Positive: {political_data.get('positive', 0)}")
        print(f"   Negative: {political_data.get('negative', 0)}")
        print(f"   Neutral: {political_data.get('neutral', 0)}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # ==========================================
    # 6. OVERALL STATISTICS
    # ==========================================
    print("\n" + "-"*70)
    print("📈 6. OVERALL STATISTICS")
    print("-"*70)
    
    try:
        total_tweets = tweets_coll.count_documents({})
        unique_users = tweets_coll.distinct("user.name")
        unique_hashtags = tweets_coll.distinct("hashtags")
        
        doc = {
            "type": "overall_statistics",
            "timestamp": timestamp,
            "total_tweets": total_tweets,
            "unique_users": len([u for u in unique_users if u]),
            "total_hashtags": len([h for hlist in unique_hashtags if hlist for h in hlist]),
            "data": {
                "total_tweets": total_tweets,
                "unique_users_count": len([u for u in unique_users if u]),
                "unique_hashtags_count": len([h for hlist in unique_hashtags if hlist for h in hlist])
            }
        }
        
        results_coll.insert_one(doc)
        print(f"✅ Saved Overall Statistics:")
        print(f"   Total Tweets: {total_tweets}")
        print(f"   Unique Users: {len([u for u in unique_users if u])}")
        print(f"   Unique Hashtags: {len([h for hlist in unique_hashtags if hlist for h in hlist])}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # ==========================================
    # SUMMARY
    # ==========================================
    print("\n" + "="*70)
    print("✅ MAPREDUCE ANALYSIS COMPLETE!")
    print("="*70)
    
    # Show all saved documents
    all_results = list(results_coll.find({}))
    print(f"\n📊 Saved {len(all_results)} MapReduce result documents:")
    for i, result in enumerate(all_results, 1):
        doc_type = result.get("type", "unknown")
        print(f"   {i}. {doc_type.upper()}")
        if "total_tweets" in result:
            print(f"      Total: {result['total_tweets']}")
        if "total_results" in result:
            print(f"      Results: {result['total_results']}")
        if "total_political_tweets" in result:
            print(f"      Political Tweets: {result['total_political_tweets']}")
    
    print("\n✅ All results are now stored in MongoDB collection: 'mapreduce_analysis_results'")
    print("✅ View them in MongoDB Atlas Data Explorer or query with your application!")

if __name__ == "__main__":
    try:
        run_mapreduce_analysis()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
