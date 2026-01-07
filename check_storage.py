#!/usr/bin/env python3
"""
Check MongoDB Atlas storage space and quota information
"""

from pymongo import MongoClient
from pymongo.server_api import ServerApi
import certifi

def check_mongodb_storage():
    """Check MongoDB Atlas storage space and usage"""
    
    print("="*70)
    print("📊 MONGODB ATLAS STORAGE INFORMATION")
    print("="*70)
    
    try:
        # Connect to MongoDB
        uri = "mongodb+srv://jeevanandhm_db_user:1234567jeeva@cluster0.umcf1y7.mongodb.net/?appName=Cluster0"
        client = MongoClient(
            uri, 
            server_api=ServerApi('1'),
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000
        )
        
        client.admin.command('ping')
        print("\n✅ Connected to MongoDB Atlas")
        
        # Get database stats
        db = client["TwitterDB"]
        
        print("\n" + "-"*70)
        print("📦 DATABASE STATISTICS")
        print("-"*70)
        
        db_stats = db.command("dbStats")
        
        # Extract storage information
        storage_size = db_stats.get('storageSize', 0) / (1024 * 1024)  # Convert to MB
        data_size = db_stats.get('dataSize', 0) / (1024 * 1024)
        file_size = db_stats.get('fileSize', 0) / (1024 * 1024) if 'fileSize' in db_stats else 0
        collections = db_stats.get('collections', 0)
        objects = db_stats.get('objects', 0)
        
        print(f"\n📊 Database: TwitterDB")
        print(f"   Storage Size: {storage_size:.2f} MB")
        print(f"   Data Size: {data_size:.2f} MB")
        print(f"   Collections: {collections}")
        print(f"   Total Objects: {objects:,}")
        
        # Get collection details
        print("\n" + "-"*70)
        print("📋 COLLECTION STATISTICS")
        print("-"*70)
        
        collections_list = db.list_collection_names()
        
        total_collection_size = 0
        total_collection_count = 0
        
        for coll_name in sorted(collections_list):
            try:
                coll_stats = db.command("collStats", coll_name)
                coll_size = coll_stats.get('size', 0) / (1024 * 1024)
                coll_count = coll_stats.get('count', 0)
                storage_bytes = coll_stats.get('storageSize', 0) / (1024 * 1024)
                
                total_collection_size += coll_size
                total_collection_count += coll_count
                
                print(f"\n{coll_name}:")
                print(f"   Documents: {coll_count:,}")
                print(f"   Data Size: {coll_size:.2f} MB")
                print(f"   Storage Size: {storage_bytes:.2f} MB")
            except Exception as e:
                print(f"\n{coll_name}: (Error reading stats)")
        
        # Storage quota information
        print("\n" + "-"*70)
        print("💾 STORAGE QUOTA & CAPACITY")
        print("-"*70)
        
        # Standard M0 tier has 512 MB, M2/M5 have limits
        cluster_tier = "M0 (Free Tier)"  # Default assumption
        max_storage_mb = 512  # M0 limit
        
        print(f"\n📈 Cluster Tier: {cluster_tier}")
        print(f"   Maximum Storage: {max_storage_mb} MB")
        print(f"   Current Used: {storage_size:.2f} MB")
        
        used_percentage = (storage_size / max_storage_mb) * 100
        remaining = max_storage_mb - storage_size
        
        print(f"\n📊 Quota Usage:")
        print(f"   Used: {used_percentage:.1f}%")
        print(f"   Remaining: {remaining:.2f} MB")
        
        if used_percentage >= 90:
            print(f"   ⚠️  WARNING: Storage quota almost full!")
        elif used_percentage >= 75:
            print(f"   ⚠️  CAUTION: Storage quota 75% full")
        else:
            print(f"   ✅ Storage quota within limits")
        
        # Recommendations
        print("\n" + "-"*70)
        print("💡 RECOMMENDATIONS")
        print("-"*70)
        
        print(f"\n1. Current Storage Status:")
        print(f"   - Using {storage_size:.2f} MB of {max_storage_mb} MB")
        print(f"   - {remaining:.2f} MB available")
        
        print(f"\n2. For Big Data Project (1.6M tweets):")
        estimated_total = (storage_size / 1175000) * 1600000  # Scale to full dataset
        print(f"   - Current tweets: 1,175,000 ({storage_size:.2f} MB)")
        print(f"   - Estimated for 1.6M tweets: {estimated_total:.2f} MB")
        
        if estimated_total > max_storage_mb:
            print(f"   - ⚠️  EXCEEDS M0 quota by {estimated_total - max_storage_mb:.2f} MB")
            print(f"\n3. Upgrade Options:")
            print(f"   - M2 Cluster: 2 GB storage (~$50-100/month)")
            print(f"   - M5 Cluster: 10 GB storage (~$100+/month)")
            print(f"   - M10+ Cluster: Up to 512 GB+ storage")
        else:
            print(f"   - ✅ Fits within current M0 quota")
        
        print(f"\n4. Data Optimization:")
        print(f"   - Remove duplicate tweets")
        print(f"   - Archive old analysis results")
        print(f"   - Use indexes efficiently")
        print(f"   - Consider sharding for very large datasets")
        
        # Get server info
        print("\n" + "-"*70)
        print("🔧 SERVER INFORMATION")
        print("-"*70)
        
        server_info = client.server_info()
        print(f"\n MongoDB Version: {server_info.get('version', 'Unknown')}")
        
    except Exception as e:
        print(f"\n❌ Error checking storage: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_mongodb_storage()
