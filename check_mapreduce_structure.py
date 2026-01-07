#!/usr/bin/env python3
"""
Check MapReduce document structure in MongoDB
"""

import sys
sys.path.insert(0, 'scripts')

from pymongo import MongoClient
from pymongo.server_api import ServerApi
import certifi
import json

uri = 'mongodb+srv://jeevanandhm_db_user:1234567jeeva@cluster0.umcf1y7.mongodb.net/?appName=Cluster0'
client = MongoClient(uri, server_api=ServerApi('1'), tlsCAFile=certifi.where(), retryWrites=False)
db = client['TwitterDB']
results = list(db['mapreduce_analysis_results'].find({}))

print("="*80)
print("📊 MAPREDUCE DOCUMENTS STRUCTURE")
print("="*80)

for i, doc in enumerate(results[:2]):
    print(f'\n=== Document {i+1} ===')
    print('Keys:', list(doc.keys()))
    
    # Print content (excluding _id)
    for key in doc.keys():
        if key != '_id':
            val = doc[key]
            if isinstance(val, dict):
                print(f'\n{key} (dict):')
                for k, v in list(val.items())[:3]:
                    print(f'  {k}: {v}')
            elif isinstance(val, list):
                print(f'\n{key} (list, {len(val)} items):')
                for item in val[:2]:
                    print(f'  {item}')
            else:
                print(f'{key}: {val}')
