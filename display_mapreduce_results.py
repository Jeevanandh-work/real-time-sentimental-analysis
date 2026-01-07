#!/usr/bin/env python3
"""
Retrieve and display all MapReduce results from MongoDB
"""

import sys
sys.path.insert(0, 'scripts')

from pymongo import MongoClient
from pymongo.server_api import ServerApi
import certifi
import json

def display_all_mapreduce_results():
    """
    Retrieve and display all MapReduce analysis results from MongoDB
    """
    print("="*80)
    print("📊 MAPREDUCE ANALYSIS RESULTS FROM MONGODB")
    print("="*80)
    
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
    results_coll = db["mapreduce_analysis_results"]
    
    # Get all documents
    all_results = list(results_coll.find({}))
    
    print(f"\n📚 Found {len(all_results)} MapReduce documents in MongoDB")
    
    # Display each result
    for doc in all_results:
        analysis_type = doc.get('analysis_type', 'Unknown')
        
        print("\n" + "="*80)
        print(f"📋 {analysis_type.upper()}")
        print("="*80)
        
        if analysis_type == "SENTIMENT_DISTRIBUTION":
            print(f"\n📊 Sentiment Distribution Analysis:")
            print(f"   Total Tweets: {doc.get('total', 0):,}")
            print(f"   Positive: {doc.get('positive', 0):,} ({doc.get('positive', 0)/doc.get('total', 1)*100:.1f}%)")
            print(f"   Negative: {doc.get('negative', 0):,} ({doc.get('negative', 0)/doc.get('total', 1)*100:.1f}%)")
            print(f"   Neutral: {doc.get('neutral', 0):,} ({doc.get('neutral', 0)/doc.get('total', 1)*100:.1f}%)")
        
        elif analysis_type == "TOP_HASHTAGS":
            print(f"\n🏷️  Top {len(doc.get('hashtags', []))} Hashtags:")
            for idx, hashtag in enumerate(doc.get('hashtags', []), 1):
                print(f"   {idx:2d}. {hashtag['_id']:20s} : {hashtag['count']:6,} tweets")
        
        elif analysis_type == "SENTIMENT_BY_HASHTAG":
            results = doc.get('results', [])
            print(f"\n🏷️  Sentiment by Hashtag ({len(results)} combinations):")
            
            # Group by hashtag
            hashtags_dict = {}
            for result in results:
                hashtag = result.get('hashtag', 'Unknown')
                sentiment = result.get('sentiment', 'Unknown')
                count = result.get('count', 0)
                
                if hashtag not in hashtags_dict:
                    hashtags_dict[hashtag] = {}
                hashtags_dict[hashtag][sentiment] = count
            
            # Display top hashtags with sentiment breakdown
            for hashtag, sentiments in list(hashtags_dict.items())[:15]:
                pos = sentiments.get('positive', 0)
                neg = sentiments.get('negative', 0)
                neu = sentiments.get('neutral', 0)
                total = pos + neg + neu
                print(f"   {hashtag:20s}: Pos:{pos:5,} Neg:{neg:5,} Neu:{neu:5,} (Total:{total:6,})")
        
        elif analysis_type == "TOP_USERS":
            print(f"\n👥 Top {len(doc.get('users', []))} Users by Tweet Count:")
            for idx, user in enumerate(doc.get('users', []), 1):
                print(f"   {idx:2d}. @{user['_id']:25s} : {user['count']:6,} tweets")
        
        elif analysis_type == "POLITICAL_ANALYSIS":
            print(f"\n🏛️  Political Sentiment Analysis:")
            print(f"   Total Political Tweets: {doc.get('total_political', 0):,}")
            print(f"   Positive: {doc.get('positive', 0):,} ({doc.get('positive', 0)/doc.get('total_political', 1)*100:.1f}%)")
            print(f"   Negative: {doc.get('negative', 0):,} ({doc.get('negative', 0)/doc.get('total_political', 1)*100:.1f}%)")
            print(f"   Neutral: {doc.get('neutral', 0):,} ({doc.get('neutral', 0)/doc.get('total_political', 1)*100:.1f}%)")
        
        elif analysis_type == "OVERALL_STATISTICS":
            print(f"\n📈 Overall Dataset Statistics:")
            print(f"   Total Tweets: {doc.get('total_tweets', 0):,}")
            print(f"   Unique Users: {doc.get('unique_users', 0):,}")
            print(f"   Unique Hashtags: {doc.get('unique_hashtags', 0):,}")
            
            if 'sentiment_breakdown' in doc:
                breakdown = doc['sentiment_breakdown']
                print(f"\n   Sentiment Breakdown:")
                print(f"   • Positive: {breakdown.get('positive', 0):,}")
                print(f"   • Negative: {breakdown.get('negative', 0):,}")
                print(f"   • Neutral: {breakdown.get('neutral', 0):,}")
    
    # Summary statistics
    print("\n" + "="*80)
    print("📊 MONGODB COLLECTION SUMMARY")
    print("="*80)
    
    tweets_coll = db["tweets"]
    total_tweets = tweets_coll.count_documents({})
    
    print(f"\n📦 Collections:")
    print(f"   • tweets: {total_tweets:,} documents")
    print(f"   • mapreduce_analysis_results: {len(all_results)} documents")
    
    # Storage stats
    try:
        db_stats = client.admin.command("dbstats", "TwitterDB")
        storage_mb = db_stats.get("storageSize", 0) / (1024 * 1024)
        data_mb = db_stats.get("dataSize", 0) / (1024 * 1024)
        
        print(f"\n💾 Storage:")
        print(f"   • Data Size: {data_mb:.2f} MB")
        print(f"   • Storage Size: {storage_mb:.2f} MB")
        print(f"   • Quota Used: {storage_mb/512*100:.1f}% of 512 MB")
        print(f"   • Available: {512 - storage_mb:.2f} MB")
    except:
        print(f"\n💾 Storage: (unable to retrieve stats)")
    
    print("\n✅ All MapReduce results successfully retrieved from MongoDB!")

if __name__ == "__main__":
    display_all_mapreduce_results()
