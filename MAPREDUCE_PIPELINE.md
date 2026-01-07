# 🚀 MapReduce Pipeline - Twitter Sentiment Analysis

## **Complete MapReduce Architecture**

This document explains how all MapReduce components connect together in the sentiment analysis pipeline.

---

## **📊 Pipeline Flow Diagram**

```
┌─────────────────────────────────────────────────────────────────────┐
│                     MAPREDUCE SENTIMENT ANALYSIS PIPELINE            │
└─────────────────────────────────────────────────────────────────────┘

INPUT: MongoDB Collection (tweets)
   │
   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          MAPREDUCE TASKS                             │
└─────────────────────────────────────────────────────────────────────┘

   ┌──────────────────────────────────┐
   │  1. SENTIMENT DISTRIBUTION       │
   ├──────────────────────────────────┤
   │ 🗺️  MAP:    sentiment → 1        │
   │ 🔄 SHUFFLE: Group by sentiment   │
   │ 🔴 REDUCE:  Sum counts per type  │
   │ OUTPUT: {positive, negative...}  │
   └──────────────────────────────────┘
         │
         ▼
   ┌──────────────────────────────────┐
   │  2. TOP HASHTAGS                 │
   ├──────────────────────────────────┤
   │ 🗺️  MAP:    hashtag → 1          │
   │ 🔄 SHUFFLE: Group by hashtag     │
   │ 🔴 REDUCE:  Sum counts per tag   │
   │ OUTPUT: [(#tag1, count)...]      │
   └──────────────────────────────────┘
         │
         ▼
   ┌──────────────────────────────────┐
   │  3. SENTIMENT OVER TIME          │
   ├──────────────────────────────────┤
   │ 🗺️  MAP:    date → {count, total}│
   │ 🔄 SHUFFLE: Group by date        │
   │ 🔴 REDUCE:  Calculate avg score  │
   │ OUTPUT: [(date, avg_sentiment)...]│
   └──────────────────────────────────┘
         │
         ▼
   ┌──────────────────────────────────┐
   │  4. TOP WORDS BY SENTIMENT       │
   ├──────────────────────────────────┤
   │ 🗺️  MAP:    word → 1             │
   │ 🔄 SHUFFLE: Group by word        │
   │ 🔴 REDUCE:  Sum word counts      │
   │ OUTPUT: [(word, count)...]       │
   └──────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    RESULTS AGGREGATION & STORAGE                    │
│              MongoDB Collection: mapreduce_analysis_results          │
└─────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         VISUALIZATIONS                              │
│  • sentiment_distribution.png                                        │
│  • sentiment_trend.png                                               │
│  • word_comparison.png                                               │
│  • top_hashtags.png                                                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## **🔌 Connection Points**

### **1. Map Phase Connection**
```python
# All MAP functions emit key-value pairs:
# 🗺️ sentiment_distribution_map(doc) → (sentiment, 1)
# 🗺️ top_hashtags_map(doc) → (hashtag, 1)
# 🗺️ sentiment_over_time_map(interval) → (date, {count, total})
# 🗺️ top_words_map(doc) → (word, 1)

# Connected through map_phase() framework function:
def map_phase(documents, map_func):
    mapped_data = []
    for doc in documents:
        for key, value in map_func(doc):
            mapped_data.append((key, value))
    return mapped_data
```

### **2. Shuffle Phase Connection**
```python
# All mapped data goes through shuffle_phase():
def shuffle_phase(mapped_data):
    """Groups values by key"""
    shuffled = defaultdict(list)
    for key, value in mapped_data:
        shuffled[key].append(value)
    return shuffled

# Result: {key1: [v1, v2, ...], key2: [v3, v4, ...], ...}
```

### **3. Reduce Phase Connection**
```python
# All REDUCE functions process grouped data:
# 🔴 sentiment_distribution_reduce(key, values) → count
# 🔴 top_hashtags_reduce(key, values) → count
# 🔴 sentiment_over_time_reduce(key, values) → {avg_sentiment, count}
# 🔴 top_words_reduce(key, values) → count

# Connected through reduce_phase() framework function:
def reduce_phase(shuffled_data, reduce_func):
    reduced = {}
    for key, values in shuffled_data.items():
        reduced[key] = reduce_func(key, values)
    return reduced
```

---

## **📋 Task-by-Task Connection**

### **TASK 1: Sentiment Distribution**

**Purpose:** Count tweets by sentiment type

```python
# STEP 1: MAP PHASE
# Input: All documents from collection
# 🗺️ sentiment_distribution_map(doc):
#    For each doc: yield (doc["sentiment_label"], 1)
# Output: [("positive", 1), ("negative", 1), ("positive", 1), ...]

# STEP 2: SHUFFLE PHASE
# Grouping: {
#    "positive": [1, 1, 1, ...],
#    "negative": [1, 1, ...],
#    "neutral": [1, ...]
# }

# STEP 3: REDUCE PHASE
# 🔴 sentiment_distribution_reduce("positive", [1,1,1,1,1])
#    → Returns: 5
# 🔴 sentiment_distribution_reduce("negative", [1,1,1])
#    → Returns: 3
# 🔴 sentiment_distribution_reduce("neutral", [1])
#    → Returns: 1

# FINAL OUTPUT:
{
    "positive": 5,
    "negative": 3,
    "neutral": 1,
    "total": 9
}
```

---

### **TASK 2: Top Hashtags**

**Purpose:** Find most frequently used hashtags

```python
# STEP 1: MAP PHASE
# 🗺️ top_hashtags_map(doc):
#    For each hashtag in doc["hashtags"]: yield (hashtag.lower(), 1)
# Output: [("#ai", 1), ("#ml", 1), ("#ai", 1), ("#python", 1), ...]

# STEP 2: SHUFFLE PHASE
# Grouping: {
#    "ai": [1, 1, 1, 1, 1],
#    "ml": [1, 1, 1],
#    "python": [1, 1]
# }

# STEP 3: REDUCE PHASE
# 🔴 top_hashtags_reduce("ai", [1,1,1,1,1])
#    → Returns: 5
# 🔴 top_hashtags_reduce("ml", [1,1,1])
#    → Returns: 3
# 🔴 top_hashtags_reduce("python", [1,1])
#    → Returns: 2

# FINAL OUTPUT (sorted, top 10):
[
    ("#ai", 5),
    ("#ml", 3),
    ("#python", 2)
]
```

---

### **TASK 3: Sentiment Over Time**

**Purpose:** Track sentiment score changes over days/months

```python
# STEP 1: MAP PHASE
# 🗺️ sentiment_over_time_map(interval="day"):
#    For each doc: yield (date_key, {"count": 1, "total": sentiment_score})
# Output: [
#    ("2025-10-28", {"count": 1, "total": 0.8}),
#    ("2025-10-28", {"count": 1, "total": -0.5}),
#    ("2025-10-29", {"count": 1, "total": 0.6}),
#    ...
# ]

# STEP 2: SHUFFLE PHASE
# Grouping: {
#    "2025-10-28": [{"count": 1, "total": 0.8}, {"count": 1, "total": -0.5}],
#    "2025-10-29": [{"count": 1, "total": 0.6}]
# }

# STEP 3: REDUCE PHASE
# 🔴 sentiment_over_time_reduce("2025-10-28", [{"count": 1, "total": 0.8}, 
#                                               {"count": 1, "total": -0.5}])
#    total_count = 1 + 1 = 2
#    total_score = 0.8 + (-0.5) = 0.3
#    avg = 0.3 / 2 = 0.15
#    → Returns: {"avg_sentiment": 0.15, "count": 2}

# 🔴 sentiment_over_time_reduce("2025-10-29", [{"count": 1, "total": 0.6}])
#    total_count = 1
#    total_score = 0.6
#    avg = 0.6 / 1 = 0.6
#    → Returns: {"avg_sentiment": 0.6, "count": 1}

# FINAL OUTPUT (sorted by date):
[
    ("2025-10-28", {"avg_sentiment": 0.15, "count": 2}),
    ("2025-10-29", {"avg_sentiment": 0.6, "count": 1})
]
```

---

### **TASK 4: Top Words by Sentiment**

**Purpose:** Find most frequently used words in each sentiment category

```python
# STEP 1: MAP PHASE (For positive sentiment)
# 🗺️ top_words_map(doc):
#    For each word in doc["clean_text"]: yield (word.lower(), 1)
# Output: [("love", 1), ("great", 1), ("love", 1), ("awesome", 1), ...]

# STEP 2: SHUFFLE PHASE
# Grouping: {
#    "love": [1, 1, 1, 1],
#    "great": [1, 1, 1],
#    "awesome": [1, 1]
# }

# STEP 3: REDUCE PHASE
# 🔴 top_words_reduce("love", [1, 1, 1, 1])
#    → Returns: 4
# 🔴 top_words_reduce("great", [1, 1, 1])
#    → Returns: 3
# 🔴 top_words_reduce("awesome", [1, 1])
#    → Returns: 2

# FINAL OUTPUT (sorted, top 10):
[
    ("love", 4),
    ("great", 3),
    ("awesome", 2)
]
```

---

## **🔗 Integration Points**

### **How Everything Connects:**

```python
# In mapreduce_aggregations.py:

def comprehensive_mapreduce_analysis():
    """Master orchestrator connecting all MapReduce tasks"""
    
    coll = get_collection()
    tweets = list(coll.find({}, {"_id": 0}))
    
    # ============ TASK 1: Sentiment Distribution ============
    dist_custom = sentiment_distribution_custom_mapreduce()
    # Internally calls:
    # - map_phase(docs, sentiment_distribution_map)
    # - shuffle_phase(mapped)
    # - reduce_phase(shuffled, sentiment_distribution_reduce)
    
    # ============ TASK 2: Top Hashtags ============
    hashtags_custom = top_hashtags_custom_mapreduce(15)
    # Internally calls:
    # - map_phase(docs, top_hashtags_map)
    # - shuffle_phase(mapped)
    # - reduce_phase(shuffled, top_hashtags_reduce)
    
    # ============ TASK 3: Sentiment Over Time ============
    trend_custom = sentiment_over_time_custom_mapreduce("day")
    # Internally calls:
    # - map_phase(docs, sentiment_over_time_map("day"))
    # - shuffle_phase(mapped)
    # - reduce_phase(shuffled, sentiment_over_time_reduce)
    
    # ============ TASK 4: Top Words ============
    pos_words = top_words_by_sentiment_custom_mapreduce("positive", 10)
    # Internally calls:
    # - map_phase(docs, top_words_map)
    # - shuffle_phase(mapped)
    # - reduce_phase(shuffled, top_words_reduce)
    
    # ============ Store Results ============
    results = {
        "timestamp": datetime.now().isoformat(),
        "custom_mapreduce_framework": {
            "sentiment_distribution": dist_custom,
            "top_hashtags": hashtags_custom,
            "sentiment_trend": trend_custom,
            "top_positive_words": pos_words
        }
    }
    
    result_coll = coll.database["mapreduce_analysis_results"]
    result_coll.insert_one(results)
    
    # ============ Visualize Results ============
    create_sentiment_bar_chart_custom(dist_custom)
    create_trend_chart_custom(trend_custom)
    create_word_comparison_chart_custom()
```

---

## **📊 Data Flow Example**

### **Sample Input Data:**
```python
tweets = [
    {"sentiment_label": "positive", "text": "I love this", "clean_text": "love this", "hashtags": ["ai", "ml"]},
    {"sentiment_label": "positive", "text": "Great work", "clean_text": "great work", "hashtags": ["ai"]},
    {"sentiment_label": "negative", "text": "Hate it", "clean_text": "hate it", "hashtags": ["bad"]},
    {"sentiment_label": "positive", "text": "Awesome", "clean_text": "awesome", "hashtags": ["ai"]}
]
```

### **Processing Flow:**

```
INPUT
  ↓
MAP PHASE (Process each document)
  ├─ sentiment_distribution_map() → [("positive", 1), ("positive", 1), ("negative", 1), ("positive", 1)]
  ├─ top_hashtags_map() → [("ai", 1), ("ml", 1), ("ai", 1), ("bad", 1), ("ai", 1)]
  ├─ top_words_map() → [("love", 1), ("great", 1), ("hate", 1), ("awesome", 1)]
  └─ sentiment_over_time_map() → [(date1, {...}), (date1, {...}), (date2, {...}), ...]
  ↓
SHUFFLE PHASE (Group by key)
  ├─ sentiment: {"positive": [1,1,1], "negative": [1]}
  ├─ hashtags: {"ai": [1,1,1], "ml": [1], "bad": [1]}
  ├─ words: {"love": [1], "great": [1], "hate": [1], "awesome": [1]}
  └─ dates: {date1: [...], date2: [...]}
  ↓
REDUCE PHASE (Aggregate values)
  ├─ sentiment_reduce() → {"positive": 3, "negative": 1}
  ├─ hashtags_reduce() → {"ai": 3, "ml": 1, "bad": 1}
  ├─ words_reduce() → {"love": 1, "great": 1, "hate": 1, "awesome": 1}
  └─ dates_reduce() → {date1: {avg: 0.5, count: 2}, ...}
  ↓
OUTPUT
  ↓
VISUALIZATIONS & STORAGE
```

---

## **🎯 How to Run the Complete Pipeline**

```bash
# Execute the complete MapReduce pipeline
python scripts/mapreduce_aggregations.py
```

**This runs:**
1. ✅ MongoDB MapReduce operations
2. ✅ Python functional MapReduce
3. ✅ Custom MapReduce framework (with explicit Map, Shuffle, Reduce)
4. ✅ All 4 MapReduce tasks in parallel
5. ✅ Stores results in MongoDB
6. ✅ Generates visualizations
7. ✅ Prints analysis to console

---

## **📈 Result Structure**

```python
{
    "timestamp": "2025-10-30T10:30:45.123456",
    "mongodb_mapreduce": {
        "sentiment_distribution": {"positive": 100, "negative": 20, "neutral": 30, "total": 150},
        "top_hashtags": [("#ai", 45), ("#ml", 30), ...],
        "sentiment_trend": [{"date": "2025-10-28", "avg_sentiment": 0.5, ...}, ...]
    },
    "python_mapreduce": {
        "sentiment_distribution": {...},
        "top_hashtags": [...],
        "sentiment_trend": [...],
        "avg_tweet_length": [...]
    },
    "custom_mapreduce_framework": {
        "sentiment_distribution": {"positive": 100, ...},
        "top_hashtags": [("#ai", 45), ...],
        "sentiment_trend": [...],
        "top_positive_words": [("love", 45), ("great", 30), ...],
        "top_negative_words": [("hate", 20), ("bad", 15), ...],
        "top_neutral_words": [("news", 10), ("update", 8), ...]
    }
}
```

---

## **🔑 Key Connections**

| Component | Input | Map Function | Shuffle | Reduce Function | Output |
|-----------|-------|--------------|---------|-----------------|--------|
| **Sentiment Distribution** | All tweets | `sentiment_distribution_map()` | Group by sentiment | `sentiment_distribution_reduce()` | Sentiment counts |
| **Top Hashtags** | Tweets with hashtags | `top_hashtags_map()` | Group by hashtag | `top_hashtags_reduce()` | Top N hashtags |
| **Sentiment Trend** | Tweets with date & score | `sentiment_over_time_map()` | Group by date | `sentiment_over_time_reduce()` | Avg sentiment per date |
| **Top Words** | Tweets by sentiment | `top_words_map()` | Group by word | `top_words_reduce()` | Top words per sentiment |

---

## **✨ Summary**

The MapReduce pipeline connects all components through:
1. **Consistent Map Functions** - All emit key-value pairs
2. **Universal Shuffle Phase** - Groups all data by key
3. **Flexible Reduce Functions** - Aggregate grouped values
4. **Orchestrator Function** - `comprehensive_mapreduce_analysis()` ties everything together
5. **Storage & Visualization** - Results saved to MongoDB and visualized

**All MapReduce operations follow the same pattern:**
```
Input Data → MAP (emit key-value pairs)
          → SHUFFLE (group by key)  
          → REDUCE (aggregate values)
          → Output Results
```
