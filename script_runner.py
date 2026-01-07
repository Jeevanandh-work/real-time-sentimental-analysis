#!/usr/bin/env python3

"""
Simple script runner to test the pipeline without complex dependencies.
This bypasses Kafka and Spark to directly insert sample data with sentiment analysis.
"""

import json
import sys
import time
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

from scripts.sentiment_utils import get_sentiment

from pymongo import MongoClient
def get_collection():
    # Connect to MongoDB
    client = MongoClient("mongodb://localhost:27017/")
    db = client["twitter_db"]
    collection = db["tweets"]
    return collection

def load_kaggle_data():
    """Load data from the Kaggle Sentiment140 dataset."""
    print("Loading Kaggle Sentiment140 dataset...")
    import pandas as pd

    try:
        # Read sample of the data (file is very large)
        df = pd.read_csv("training.1600000.processed.noemoticon.csv", encoding='latin-1', header=None, nrows=10000)

        # Column names based on dataset documentation
        df.columns = ['sentiment', 'target_id', 'date', 'query_flag', 'user', 'text']

        # Map sentiment values to labels: 0 = negative, 4 = positive
        sentiment_map = {0: 'negative', 4: 'positive'}
        df['sentiment_label'] = df['sentiment'].map(sentiment_map)

        # Keep relevant columns
        df = df[['target_id', 'date', 'user', 'text', 'sentiment_label']]

        tweets = []
        for _, row in df.iterrows():
            sentiment = get_sentiment(str(row['text']))
            tweet_obj = {
                "tweet_id": str(row['target_id']),
                "created_at": str(row['date']),
                "text": str(row['text']),
                "clean_text": str(row['text']),
                "user": {"id": str(row['user']), "name": str(row['user'])},
                "sentiment_label": "Positive" if sentiment["label"].lower() == "positive" else "Negative" if sentiment["label"].lower() == "negative" else "Neutral",
                "sentiment_score": sentiment["score"],
                "hashtags": [],  # Extract hashtags from text
                "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
            tweets.append(tweet_obj)

        print(f"Loaded {len(tweets)} tweets from Kaggle dataset")
        return tweets

    except Exception as e:
        print(f"Error loading Kaggle dataset: {e}")
        return []

def populate_database():
    """Populate the database with Kaggle dataset tweets and sentiment analysis."""
    tweets = load_kaggle_data()
    if not tweets:
        print("No tweets loaded, using sample data instead.")
        tweets = [
            {
                "id": "1",
                "created_at": "2025-10-01T10:00:00Z",
                "text": "I love AI! So excited about the future.",
                "user": {"id": "u1", "name": "Alice"},
                "entities": {"hashtags": ["AI"]}
            },
            # ... rest of sample data
        ]

    coll = get_collection()
    coll.delete_many({})  # Clear existing data
    if tweets:
        # Process each tweet for proper format
        docs = []
        for tweet in tweets:
            if "id" in tweet:
                # Sample format
                text = tweet.get("text", "")
                sentiment = get_sentiment(text)
                doc = {
                    "tweet_id": tweet["id"],
                    "created_at": tweet["created_at"],
                    "text": text,
                    "clean_text": text,
                    "user": tweet["user"],
                    "hashtags": tweet["entities"]["hashtags"],
                    "sentiment_score": sentiment["score"],
                    "sentiment_label": sentiment["label"],
                    "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                }
            else:
                # Kaggle format - already processed
                doc = tweet
            docs.append(doc)

        coll.insert_many(docs)
        print(f"Inserted {len(docs)} tweets with sentiment analysis.")
    else:
        print("No docs to insert.")

if __name__ == "__main__":
    populate_database()
