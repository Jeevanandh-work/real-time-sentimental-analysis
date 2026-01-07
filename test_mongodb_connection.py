#!/usr/bin/env python3
"""
MongoDB Atlas Connection Test
Tests the new MongoDB Atlas credentials and ServerApi connection
"""

from pymongo import MongoClient
from pymongo.server_api import ServerApi

def test_mongodb_atlas_connection():
    """
    Test connection to MongoDB Atlas with the new credentials
    """
    print("="*70)
    print("🔗 MONGODB ATLAS CONNECTION TEST")
    print("="*70)
    
    # New MongoDB Atlas credentials
    uri = "mongodb+srv://jeevanandhm_db_user:1234567jeeva@cluster0.umcf1y7.mongodb.net/?appName=Cluster0"
    
    print(f"\n📍 Connection URI: {uri[:50]}...***")
    print(f"📍 Username: jeevanandhm_db_user")
    print(f"📍 Cluster: cluster0 (umcf1y7)")
    print(f"📍 Database: TwitterDB")
    print(f"📍 Collection: tweets")
    
    try:
        print("\n⏳ Connecting to MongoDB Atlas...")
        
        # Create a new client with ServerApi
        client = MongoClient(uri, server_api=ServerApi('1'))
        
        # Send a ping to confirm a successful connection
        print("⏳ Sending ping command...")
        client.admin.command('ping')
        
        print("✅ Pinged your deployment. You successfully connected to MongoDB!")
        print("\n" + "="*70)
        print("✨ CONNECTION SUCCESSFUL ✨")
        print("="*70)
        
        # Get database and collection info
        db = client["TwitterDB"]
        collection = db["tweets"]
        
        # Get collection stats
        try:
            stats = collection.index_information()
            print(f"\n📊 Collection Stats:")
            print(f"   - Collection name: {collection.name}")
            print(f"   - Database name: {db.name}")
            print(f"   - Indexes: {len(stats)}")
            
            # Try to count documents
            count = collection.count_documents({})
            print(f"   - Total documents: {count}")
        except Exception as e:
            print(f"   - (Note: {e})")
        
        print("\n✅ Ready to run MapReduce analysis!")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Connection Failed!")
        print(f"Error: {e}")
        print("\n" + "="*70)
        print("🔧 TROUBLESHOOTING STEPS:")
        print("="*70)
        print("1. Check your internet connection")
        print("2. Verify credentials are correct:")
        print("   - Username: jeevanandhm_db_user")
        print("   - Cluster: cluster0.umcf1y7.mongodb.net")
        print("3. Check MongoDB Atlas IP Whitelist:")
        print("   - Go to Security > Network Access")
        print("   - Add your IP address or use 0.0.0.0/0 (allow all)")
        print("4. Verify firewall is not blocking MongoDB port (27017)")
        print("="*70)
        
        return False


if __name__ == "__main__":
    success = test_mongodb_atlas_connection()
    exit(0 if success else 1)
