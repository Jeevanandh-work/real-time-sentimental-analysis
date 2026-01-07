#!/usr/bin/env python3
"""
Display all MapReduce analysis results from MongoDB in a formatted way
"""

import sys
sys.path.insert(0, 'scripts')

from pymongo import MongoClient
from pymongo.server_api import ServerApi
import certifi

def display_all_mapreduce():
    """
    Retrieve and display all MapReduce results from MongoDB
    """
    print("="*90)
    print("🚀 MAPREDUCE ANALYSIS RESULTS - ALL DATASETS FROM MONGODB")
    print("="*90)
    
    # Connect to MongoDB
    uri = "mongodb+srv://jeevanandhm_db_user:1234567jeeva@cluster0.umcf1y7.mongodb.net/?appName=Cluster0"
    client = MongoClient(
        uri, 
        server_api=ServerApi('1'),
        tlsCAFile=certifi.where(),
        retryWrites=False,
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000
    )
    
    try:
        client.admin.command('ping')
        print("\n✅ Connected to MongoDB Atlas\n")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    db = client["TwitterDB"]
    results_coll = db["mapreduce_analysis_results"]
    
    # Get all documents
    all_results = list(results_coll.find({}).sort("timestamp", 1))
    
    print(f"📚 Retrieved {len(all_results)} MapReduce documents\n")
    
    # Display each result by type
    for doc in all_results:
        doc_type = doc.get('type', 'unknown')
        
        print("="*90)
        print(f"📋 {doc_type.upper()}")
        print("="*90)
        
        if doc_type == "sentiment_distribution":
            breakdown = doc.get('breakdown', {})
            total = doc.get('total_tweets', 0)
            pos = breakdown.get('positive', 0)
            neg = breakdown.get('negative', 0)
            neu = breakdown.get('neutral', 0)
            
            print(f"\n📊 Sentiment Distribution (Total: {total:,} tweets)")
            print(f"   ✅ Positive: {pos:,} ({pos/total*100:.1f}%)")
            print(f"   ❌ Negative: {neg:,} ({neg/total*100:.1f}%)")
            print(f"   ⚪ Neutral: {neu:,} ({neu/total*100:.1f}%)")
        
        elif doc_type == "top_hashtags":
            data = doc.get('data', [])
            limit = doc.get('total_results', len(data))
            
            print(f"\n🏷️  Top {limit} Hashtags:")
            for idx, item in enumerate(data, 1):
                hashtag = item.get('hashtag', 'unknown')
                count = item.get('count', 0)
                print(f"   {idx:2d}. {hashtag:25s} : {count:6,} tweets")
        
        elif doc_type == "sentiment_by_hashtag":
            data = doc.get('data', [])
            
            print(f"\n🏷️  Sentiment by Hashtag ({len(data)} combinations)")
            
            # Group by hashtag and show sentiment distribution
            hashtags_dict = {}
            for item in data:
                hashtag = item.get('hashtag', 'unknown')
                sentiment = item.get('sentiment', 'unknown')
                count = item.get('count', 0)
                
                if hashtag not in hashtags_dict:
                    hashtags_dict[hashtag] = {}
                hashtags_dict[hashtag][sentiment] = count
            
            # Display top 15 hashtags
            for idx, (hashtag, sentiments) in enumerate(list(hashtags_dict.items())[:15], 1):
                pos = sentiments.get('positive', 0)
                neg = sentiments.get('negative', 0)
                neu = sentiments.get('neutral', 0)
                total = pos + neg + neu
                print(f"   {idx:2d}. {hashtag:20s} | Pos:{pos:5,} | Neg:{neg:5,} | Neu:{neu:5,} | Total:{total:6,}")
        
        elif doc_type == "top_users":
            data = doc.get('data', [])
            
            print(f"\n👥 Top {len(data)} Users by Tweet Count:")
            for idx, item in enumerate(data, 1):
                user = item.get('user', 'unknown')
                count = item.get('count', 0)
                print(f"   {idx:2d}. @{user:30s} : {count:6,} tweets")
        
        elif doc_type == "political_analysis":
            breakdown = doc.get('breakdown', {})
            total = doc.get('total_political_tweets', 0)
            pos = breakdown.get('positive', 0)
            neg = breakdown.get('negative', 0)
            neu = breakdown.get('neutral', 0)
            
            print(f"\n🏛️  Political Sentiment Analysis (Total: {total:,} tweets)")
            print(f"   ✅ Positive: {pos:,} ({pos/total*100:.1f}%)")
            print(f"   ❌ Negative: {neg:,} ({neg/total*100:.1f}%)")
            print(f"   ⚪ Neutral: {neu:,} ({neu/total*100:.1f}%)")
        
        elif doc_type == "overall_statistics":
            data = doc.get('data', {})
            
            print(f"\n📈 Overall Dataset Statistics:")
            print(f"   Total Tweets: {data.get('total_tweets', 0):,}")
            print(f"   Unique Users: {data.get('unique_users', 0):,}")
            print(f"   Unique Hashtags: {data.get('unique_hashtags', 0):,}")
            
            breakdown = data.get('sentiment_breakdown', {})
            if breakdown:
                print(f"\n   Sentiment Breakdown:")
                print(f"   • Positive: {breakdown.get('positive', 0):,}")
                print(f"   • Negative: {breakdown.get('negative', 0):,}")
                print(f"   • Neutral: {breakdown.get('neutral', 0):,}")
        
        print()
    
    # Summary
    print("="*90)
    print("📊 MONGODB SUMMARY")
    print("="*90)
    
    tweets_coll = db["tweets"]
    total_tweets = tweets_coll.count_documents({})
    
    print(f"\n📦 Collections in 'TwitterDB':")
    print(f"   • tweets: {total_tweets:,} documents")
    print(f"   • mapreduce_analysis_results: {len(all_results)} analysis documents")
    
    print(f"\n✅ MapReduce analysis complete and stored in MongoDB!")

if __name__ == "__main__":
    display_all_mapreduce()
