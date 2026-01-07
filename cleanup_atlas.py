#!/usr/bin/env python3
"""
Clean up MongoDB Atlas by removing temporary collections
to free up space for MapReduce analysis
"""

import sys
sys.path.insert(0, 'scripts')

from pymongo import MongoClient
from pymongo.server_api import ServerApi
import certifi

def cleanup_atlas():
    """
    Remove unnecessary collections to free up space
    """
    print("="*70)
    print("🧹 CLEANING UP MONGODB ATLAS")
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
    
    # List collections
    print("\n📋 Current collections:")
    collections = db.list_collection_names()
    
    for coll_name in collections:
        coll = db[coll_name]
        doc_count = coll.count_documents({})
        stats = db.command("collStats", coll_name)
        size_mb = stats["size"] / (1024 * 1024)
        print(f"   • {coll_name}: {doc_count} docs ({size_mb:.2f} MB)")
    
    # Delete old analysis results if it exists (keep just tweets and new analysis)
    print("\n🗑️  Removing old analysis results...")
    
    if "mapreduce_results" in collections:
        db["mapreduce_results"].drop()
        print("   ✅ Dropped 'mapreduce_results' collection")
    
    # Keep tweets and mapreduce_analysis_results
    print("\n✅ Cleanup complete!")
    
    # Show storage after cleanup
    print("\n📊 Storage after cleanup:")
    db_stats = client.admin.command("dbstats", "TwitterDB")
    total_mb = db_stats["storageSize"] / (1024 * 1024)
    data_mb = db_stats["dataSize"] / (1024 * 1024)
    
    print(f"   Storage Size: {total_mb:.2f} MB")
    print(f"   Data Size: {data_mb:.2f} MB")
    print(f"   Collections: {db_stats['collections']}")
    print(f"   Objects: {db_stats['objects']}")
    
    remaining_quota = 512 - total_mb
    print(f"\n💾 Available quota: {remaining_quota:.2f} MB of 512 MB")

if __name__ == "__main__":
    cleanup_atlas()
