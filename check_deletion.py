#!/usr/bin/env python3
"""
Check what data will be deleted
"""

import sys
sys.path.insert(0, 'scripts')

from pymongo import MongoClient
from pymongo.server_api import ServerApi
import certifi

def check_deletion():
    uri = 'mongodb+srv://jeevanandhm_db_user:1234567jeeva@cluster0.umcf1y7.mongodb.net/?appName=Cluster0'
    client = MongoClient(
        uri, 
        server_api=ServerApi('1'), 
        tlsCAFile=certifi.where(), 
        retryWrites=False,
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000
    )
    
    db = client['TwitterDB']
    
    print('='*70)
    print('📊 COLLECTION SIZE BREAKDOWN')
    print('='*70)
    
    total_size = 0
    collections_info = {}
    
    for coll_name in db.list_collection_names():
        coll = db[coll_name]
        doc_count = coll.count_documents({})
        stats = db.command('collStats', coll_name)
        size_mb = stats['size'] / (1024 * 1024)
        total_size += size_mb
        collections_info[coll_name] = {'docs': doc_count, 'size_mb': size_mb}
        
        print(f'\n{coll_name}:')
        print(f'  Documents: {doc_count:,}')
        print(f'  Size: {size_mb:.2f} MB')
    
    print('\n' + '='*70)
    print('🗑️  DELETION PLAN')
    print('='*70)
    
    to_delete_mb = 0
    print('\nWill DELETE:')
    if 'mapreduce_results' in collections_info:
        size_mb = collections_info['mapreduce_results']['size_mb']
        to_delete_mb = size_mb
        print(f'  ❌ mapreduce_results: {size_mb:.2f} MB')
    else:
        print(f'  ⚠️  mapreduce_results: Does not exist')
    
    print('\nWill KEEP:')
    keep_size_mb = 0
    for coll_name in collections_info:
        if coll_name != 'mapreduce_results':
            size_mb = collections_info[coll_name]['size_mb']
            keep_size_mb += size_mb
            print(f'  ✅ {coll_name}: {size_mb:.2f} MB')
    
    print('\n' + '='*70)
    print('💾 QUOTA IMPACT')
    print('='*70)
    print(f'\nCurrent Total: {total_size:.2f} MB')
    print(f'After Deletion: {keep_size_mb:.2f} MB')
    print(f'Space Freed: {to_delete_mb:.2f} MB')
    print(f'\nQuota Status: {total_size/512*100:.1f}% used')
    print(f'After Cleanup: {keep_size_mb/512*100:.1f}% used')
    print(f'Remaining Available: {512 - keep_size_mb:.2f} MB')
    
    if keep_size_mb < 512:
        print(f'\n✅ After cleanup: You will be under quota!')
        print(f'   Available for MapReduce results: {512 - keep_size_mb:.2f} MB')
    else:
        print(f'\n❌ Even after cleanup: Still over quota!')

if __name__ == "__main__":
    check_deletion()
