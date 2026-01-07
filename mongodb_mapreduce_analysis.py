#!/usr/bin/env python3
"""
MongoDB Atlas MapReduce Aggregation Analysis
Sentiment analysis using MongoDB aggregation pipeline
"""

from pymongo import MongoClient
from pymongo.server_api import ServerApi
import certifi
import json

def connect_mongodb():
    """Connect to MongoDB Atlas"""
    try:
        uri = "mongodb+srv://jeevanandhm_db_user:1234567jeeva@cluster0.umcf1y7.mongodb.net/?appName=Cluster0"
        client = MongoClient(
            uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            retryWrites=True,
            retryReads=True,
            tls=True,
            tlsAllowInvalidCertificates=True,
            tlsAllowInvalidHostnames=True
        )
        
        # Test connection
        client.admin.command('ping')
        print("[SUCCESS] Connected to MongoDB Atlas!")
        
        db = client["TwitterDB"]
        return db["tweets"]
    
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        return None

def get_sentiment_distribution(coll):
    """Get sentiment distribution from MongoDB"""
    try:
        pipeline = [
            {"$group": {
                "_id": "$sentiment_label",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]
        
        results = list(coll.aggregate(pipeline))
        
        dist = {}
        total = 0
        for result in results:
            sentiment = result["_id"]
            count = result["count"]
            dist[sentiment] = count
            total += count
        
        dist["total"] = total
        return dist
    except Exception as e:
        print(f"[ERROR] Sentiment distribution failed: {e}")
        return None

def get_top_users(coll, limit=10):
    """Get top users by tweet count"""
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
        return results
    except Exception as e:
        print(f"[ERROR] Top users query failed: {e}")
        return []

def get_sentiment_stats(coll):
    """Get detailed sentiment statistics"""
    try:
        pipeline = [
            {"$group": {
                "_id": "$sentiment_label",
                "count": {"$sum": 1},
                "avg_length": {"$avg": {"$strLenCP": "$text"}}
            }},
            {"$sort": {"count": -1}}
        ]
        
        results = list(coll.aggregate(pipeline))
        return results
    except Exception as e:
        print(f"[ERROR] Sentiment stats failed: {e}")
        return []

def get_political_analysis(coll):
    """Analyze political tweets"""
    try:
        political_keywords = [
            'politic', 'election', 'government', 'vote', 'president',
            'congress', 'senate', 'democrat', 'republican', 'trump',
            'obama', 'campaign', 'party', 'law', 'policy'
        ]
        
        query = {
            "$or": [
                {"text": {"$regex": keyword, "$options": "i"}}
                for keyword in political_keywords
            ]
        }
        
        political_count = coll.count_documents(query)
        
        pipeline = [
            {"$match": query},
            {"$group": {
                "_id": "$sentiment_label",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]
        
        sentiment_dist = list(coll.aggregate(pipeline))
        
        return {
            "total_political": political_count,
            "sentiment_distribution": sentiment_dist
        }
    except Exception as e:
        print(f"[ERROR] Political analysis failed: {e}")
        return None

def get_user_sentiment(coll, limit=10):
    """Get sentiment breakdown by user"""
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
        return results
    except Exception as e:
        print(f"[ERROR] User sentiment query failed: {e}")
        return []

def main():
    """Main execution"""
    print("\n" + "="*70)
    print("MONGODB ATLAS - MAPREDUCE SENTIMENT ANALYSIS")
    print("="*70)
    
    # Connect
    coll = connect_mongodb()
    if coll is None:
        print("[CRITICAL] Failed to connect to MongoDB Atlas!")
        return
    
    # Get total tweets
    total_tweets = coll.count_documents({})
    print(f"\n[INFO] Total tweets in database: {total_tweets:,}")
    
    # Sentiment Distribution
    print("\n" + "-"*70)
    print("SENTIMENT DISTRIBUTION")
    print("-"*70)
    
    dist = get_sentiment_distribution(coll)
    if dist:
        print(f"Positive tweets:  {dist.get('positive', 0):>10,}")
        print(f"Negative tweets:  {dist.get('negative', 0):>10,}")
        print(f"Neutral tweets:   {dist.get('neutral', 0):>10,}")
        print(f"Total:            {dist['total']:>10,}")
        
        total = dist['total']
        print(f"\nPercentages:")
        print(f"Positive: {(dist.get('positive', 0)/total*100):>6.2f}%")
        print(f"Negative: {(dist.get('negative', 0)/total*100):>6.2f}%")
        print(f"Neutral:  {(dist.get('neutral', 0)/total*100):>6.2f}%")
    
    # Sentiment Statistics
    print("\n" + "-"*70)
    print("SENTIMENT STATISTICS (Average Tweet Length)")
    print("-"*70)
    
    stats = get_sentiment_stats(coll)
    for stat in stats:
        sentiment = stat["_id"]
        count = stat["count"]
        avg_len = stat["avg_length"]
        print(f"{sentiment.upper():>10}: {count:>10,} tweets | Avg length: {avg_len:>6.1f} chars")
    
    # Top Users
    print("\n" + "-"*70)
    print("TOP 10 USERS BY TWEET COUNT")
    print("-"*70)
    
    top_users = get_top_users(coll, 10)
    for i, user in enumerate(top_users, 1):
        user_name = user["_id"]
        if isinstance(user_name, dict):
            user_name = user_name.get("username", user_name.get("name", str(user_name)))
        print(f"{i:>2}. {str(user_name)[:30]:>30} - {user['count']:>6,} tweets")
    
    # User Sentiment
    print("\n" + "-"*70)
    print("TOP USERS - SENTIMENT BREAKDOWN")
    print("-"*70)
    
    user_sentiment = get_user_sentiment(coll, 15)
    current_user = None
    for item in user_sentiment:
        user = item["_id"]["user"]
        if isinstance(user, dict):
            user = user.get("username", user.get("name", str(user)))
        
        if user != current_user:
            print(f"\nUser: {str(user)[:30]}")
            current_user = user
        
        sentiment = item["_id"]["sentiment"]
        count = item["count"]
        print(f"  {sentiment:>10}: {count:>6,} tweets")
    
    # Political Analysis
    print("\n" + "-"*70)
    print("POLITICAL CONTENT ANALYSIS")
    print("-"*70)
    
    political = get_political_analysis(coll)
    if political:
        total_political = political["total_political"]
        print(f"Total political tweets: {total_political:,}")
        print(f"Percentage of total: {(total_political/total_tweets*100):.2f}%")
        
        print(f"\nPolitical Tweet Sentiment Distribution:")
        for sent_dist in political["sentiment_distribution"]:
            sentiment = sent_dist["_id"]
            count = sent_dist["count"]
            pct = (count/total_political*100) if total_political > 0 else 0
            print(f"  {sentiment.upper():>10}: {count:>6,} tweets ({pct:>5.2f}%)")
    
    # Summary
    print("\n" + "="*70)
    print("MAPREDUCE ANALYSIS COMPLETE")
    print("="*70)
    print(f"\nDatabase: TwitterDB")
    print(f"Collection: tweets")
    print(f"Total documents analyzed: {total_tweets:,}")
    print(f"Status: SUCCESS - Connected to MongoDB Atlas")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
