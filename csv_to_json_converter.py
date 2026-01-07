#!/usr/bin/env python3
"""
Convert Kaggle Sentiment140 CSV to JSON
CSV format: sentiment, id, date, query, user, text
Output: tweets.json (JSONL format - one JSON object per line)
"""

import pandas as pd
import json
import sys
from datetime import datetime

# ==================== CONFIGURATION ====================

CSV_FILE = r"training.1600000.processed.noemoticon.csv"
JSON_OUTPUT_FILE = "tweets_data.json"
CHUNK_SIZE = 50000

# Sentiment mapping
SENTIMENT_MAP = {
    0: "negative",
    2: "neutral",
    4: "positive"
}

# ==================== FUNCTIONS ====================

def convert_csv_to_json(csv_file, json_file, chunk_size=50000):
    """
    Convert CSV to JSON (JSONL format - one object per line)
    """
    print("\n" + "="*70)
    print("🔄 CSV TO JSON CONVERSION")
    print("="*70)
    
    print(f"\n📂 Input CSV: {csv_file}")
    print(f"📄 Output JSON: {json_file}")
    print(f"📦 Processing in chunks of: {chunk_size:,}")
    
    total_records = 0
    chunk_count = 0
    
    try:
        with open(json_file, 'w', encoding='utf-8') as json_out:
            
            # Read CSV in chunks
            for chunk in pd.read_csv(
                csv_file,
                encoding='latin-1',
                header=None,
                names=['sentiment', 'id', 'date', 'query', 'user', 'text'],
                chunksize=chunk_size,
                dtype={'sentiment': int, 'id': str, 'date': str, 'query': str, 'user': str, 'text': str}
            ):
                chunk_count += 1
                records_in_chunk = 0
                
                for _, row in chunk.iterrows():
                    try:
                        # Map sentiment
                        sentiment_label = SENTIMENT_MAP.get(int(row['sentiment']), 'neutral')
                        
                        # Calculate sentiment score
                        if sentiment_label == "positive":
                            sentiment_score = 0.5
                        elif sentiment_label == "negative":
                            sentiment_score = -0.5
                        else:
                            sentiment_score = 0.0
                        
                        # Create JSON object
                        tweet_obj = {
                            "tweet_id": str(row['id']),
                            "created_at": str(row['date']),
                            "text": str(row['text']),
                            "clean_text": str(row['text']).lower(),
                            "user": {
                                "id": str(row['user']),
                                "name": str(row['user'])
                            },
                            "query": str(row['query']),
                            "sentiment_label": sentiment_label,
                            "sentiment_score": sentiment_score,
                            "hashtags": [],
                            "processed_at": datetime.now().isoformat()
                        }
                        
                        # Write as JSONL (one JSON object per line)
                        json_out.write(json.dumps(tweet_obj) + '\n')
                        records_in_chunk += 1
                        total_records += 1
                        
                    except Exception as e:
                        print(f"   ⚠️ Error processing row: {e}")
                        continue
                
                # Progress update
                print(f"   ✅ Chunk {chunk_count}: Processed {records_in_chunk:,} records (Total: {total_records:,})")
        
        # Completion message
        print("\n" + "="*70)
        print("✅ CONVERSION COMPLETED SUCCESSFULLY!")
        print("="*70)
        print(f"📊 Total records converted: {total_records:,}")
        print(f"📦 Total chunks processed: {chunk_count}")
        print(f"💾 Output file: {json_file}")
        print(f"📈 File size: Check file system")
        print("="*70 + "\n")
        
        return total_records
        
    except Exception as e:
        print(f"\n❌ Critical error during conversion: {e}")
        sys.exit(1)


def verify_json_file(json_file, sample_lines=3):
    """Verify the JSON output by reading a few lines"""
    print(f"\n🔍 VERIFYING JSON FILE: {json_file}")
    print("="*70)
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            print(f"\n📋 Sample records from {json_file}:\n")
            
            for i in range(sample_lines):
                line = f.readline()
                if not line:
                    break
                obj = json.loads(line)
                print(f"Record {i+1}:")
                print(f"  - Tweet ID: {obj['tweet_id']}")
                print(f"  - Sentiment: {obj['sentiment_label']} ({obj['sentiment_score']})")
                print(f"  - Text: {obj['text'][:60]}...")
                print(f"  - Date: {obj['created_at']}")
                print()
        
        print("="*70)
        print("✅ JSON file is valid and readable!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error verifying JSON file: {e}")


def main():
    """Main execution function"""
    print("\n" + "="*70)
    print("🚀 KAGGLE SENTIMENT140 - CSV TO JSON CONVERTER")
    print("="*70)
    
    print(f"\n📋 Configuration:")
    print(f"   - Input CSV: {CSV_FILE}")
    print(f"   - Output JSON: {JSON_OUTPUT_FILE}")
    print(f"   - Format: JSONL (one JSON object per line)")
    print(f"   - Chunk Size: {CHUNK_SIZE:,} records")
    
    # Convert CSV to JSON
    total = convert_csv_to_json(CSV_FILE, JSON_OUTPUT_FILE, CHUNK_SIZE)
    
    # Verify output
    verify_json_file(JSON_OUTPUT_FILE)
    
    print("✨ Ready to ingest into MongoDB or use directly!")
    print(f"✅ {total:,} tweets converted to JSON format\n")


if __name__ == "__main__":
    main()
