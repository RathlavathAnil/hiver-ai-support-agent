"""
Reproducible Data Inspection Script for Customer Support on Twitter Dataset
=============================================================================
This script inspects data/raw/twcs.csv without modifying it.
It computes:
- File metadata & size
- Schema & column types
- Total row count
- Missing values & completeness
- Duplicate checks
- Brand / author distributions (company vs customer)
- Conversation & thread identifier analysis
- Inbound vs Outbound message breakdown
- Timestamp range & formatting
- Text field length & lexical statistics
- Relational structure between tweets (in_reply_to, response_tweet_id)
- Specific profile for AppleSupport subset
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "twcs.csv")

def run_inspection():
    print(f"=== 1. FILE METADATA ===")
    abs_path = os.path.abspath(DATA_PATH)
    if not os.path.exists(abs_path):
        print(f"ERROR: File not found at {abs_path}")
        sys.exit(1)
    
    file_size_bytes = os.path.getsize(abs_path)
    file_size_mb = file_size_bytes / (1024 * 1024)
    print(f"File path: {abs_path}")
    print(f"File size: {file_size_bytes:,} bytes ({file_size_mb:.2f} MB)")

    print(f"\n=== 2. READING SCHEMA & PREVIEW ===")
    df_head = pd.read_csv(abs_path, nrows=10)
    print(f"Columns ({len(df_head.columns)}): {list(df_head.columns)}")
    print("\nFirst 3 rows:")
    print(df_head.head(3).to_dict(orient="records"))

    print(f"\n=== 3. FULL DATASET LOADING & SHAPE ===")
    start_time = datetime.now()
    # Read full CSV
    df = pd.read_csv(abs_path)
    load_duration = (datetime.now() - start_time).total_seconds()
    total_rows, total_cols = df.shape
    print(f"Loaded {total_rows:,} rows across {total_cols} columns in {load_duration:.2f}s")

    print(f"\n=== 4. COLUMNS, DATA TYPES & MISSING VALUES ===")
    col_stats = []
    for col in df.columns:
        null_count = int(df[col].isnull().sum())
        null_pct = (null_count / total_rows) * 100
        dtype = str(df[col].dtype)
        unique_cnt = int(df[col].nunique(dropna=True))
        col_stats.append({
            "column": col,
            "dtype": dtype,
            "non_null_count": total_rows - null_count,
            "null_count": null_count,
            "null_pct": round(null_pct, 2),
            "unique_values": unique_cnt,
            "sample_value": str(df[col].dropna().iloc[0]) if not df[col].dropna().empty else None
        })
    col_stats_df = pd.DataFrame(col_stats)
    print(col_stats_df.to_string(index=False))

    print(f"\n=== 5. DUPLICATE RECORDS ===")
    full_dupes = df.duplicated().sum()
    tweet_id_dupes = df["tweet_id"].duplicated().sum()
    print(f"Exact full-row duplicates: {full_dupes:,}")
    print(f"Duplicate tweet_id values: {tweet_id_dupes:,}")

    print(f"\n=== 6. CUSTOMER VS COMPANY / INBOUND ANALYSIS ===")
    inbound_counts = df["inbound"].value_counts(dropna=False)
    inbound_pcts = df["inbound"].value_counts(normalize=True, dropna=False) * 100
    for val in inbound_counts.index:
        print(f"inbound={val}: {inbound_counts[val]:,} ({inbound_pcts[val]:.2f}%)")

    print(f"\n=== 7. AUTHORS & BRANDS ANALYSIS ===")
    total_authors = df["author_id"].nunique()
    print(f"Total unique author_id values: {total_authors:,}")
    
    # Company authors are those where inbound=False
    company_authors = df[df["inbound"] == False]["author_id"].value_counts()
    print(f"Unique company handles (where inbound=False): {len(company_authors):,}")
    print("\nTop 20 Company Handles by Outbound Tweet Volume:")
    print(company_authors.head(20).to_string())

    # Customer authors: where inbound=True
    customer_authors = df[df["inbound"] == True]["author_id"].value_counts()
    print(f"\nUnique customer author_id count: {len(customer_authors):,}")
    print(f"Top active customer authors (max tweets by a single customer): {customer_authors.max():,}")

    print(f"\n=== 8. APPLE SUPPORT SUBSET ANALYSIS ===")
    apple_outbound = df[(df["inbound"] == False) & (df["author_id"] == "AppleSupport")]
    print(f"AppleSupport outbound tweets: {len(apple_outbound):,}")
    
    # Inbound directed to AppleSupport: either in_reply_to an Apple tweet or mentioning @AppleSupport
    mentions_apple = df["text"].astype(str).str.contains(r"@AppleSupport", case=False, na=False)
    apple_inbound = df[(df["inbound"] == True) & mentions_apple]
    print(f"Customer inbound tweets mentioning @AppleSupport: {len(apple_inbound):,}")

    print(f"\n=== 9. TIMESTAMPS & TEMPORAL COVERAGE ===")
    # Parse created_at: Twitter format '%a %b %d %H:%M:%S %z %Y'
    df["parsed_time"] = pd.to_datetime(df["created_at"], format="%a %b %d %H:%M:%S %z %Y", errors="coerce")
    valid_dates = df["parsed_time"].dropna()
    min_date = valid_dates.min()
    max_date = valid_dates.max()
    date_nulls = df["parsed_time"].isnull().sum()
    print(f"Min timestamp: {min_date}")
    print(f"Max timestamp: {max_date}")
    print(f"Time span: {(max_date - min_date).days} days")
    print(f"Unparseable timestamps: {date_nulls}")

    print(f"\n=== 10. TEXT FIELD STATISTICS ===")
    df["char_len"] = df["text"].astype(str).str.len()
    df["word_len"] = df["text"].astype(str).str.split().apply(len)
    
    print("Character length stats:")
    print(df["char_len"].describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95]))
    
    print("\nWord count stats:")
    print(df["word_len"].describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95]))

    has_url = df["text"].astype(str).str.contains(r"https?://\S+", case=False, regex=True).sum()
    has_handle = df["text"].astype(str).str.contains(r"@\w+", case=False, regex=True).sum()
    empty_or_whitespace = (df["text"].astype(str).str.strip() == "").sum()
    print(f"\nTweets containing URL: {has_url:,} ({has_url/total_rows*100:.2f}%)")
    print(f"Tweets containing @mention: {has_handle:,} ({has_handle/total_rows*100:.2f}%)")
    print(f"Empty/whitespace-only tweets: {empty_or_whitespace}")

    print(f"\n=== 11. THREAD / CONVERSATION RELATIONSHIP STRUCTURE ===")
    has_reply_to = df["in_response_to_tweet_id"].notnull().sum()
    has_response_id = df["response_tweet_id"].notnull().sum()
    print(f"Tweets with in_response_to_tweet_id: {has_reply_to:,} ({has_reply_to/total_rows*100:.2f}%)")
    print(f"Tweets with response_tweet_id: {has_response_id:,} ({has_response_id/total_rows*100:.2f}%)")
    
    # Check multi-response tweets (comma-separated response_tweet_id)
    multi_responses = df["response_tweet_id"].dropna().astype(str).str.contains(",").sum()
    print(f"Tweets with multiple comma-separated response_tweet_ids: {multi_responses:,} ({multi_responses/has_response_id*100:.2f}%)")

    # Conversation starters: inbound=True and in_response_to_tweet_id is null
    conv_starters = df[(df["inbound"] == True) & (df["in_response_to_tweet_id"].isnull())]
    print(f"Conversation starters (inbound=True and in_response_to IS NULL): {len(conv_starters):,} ({len(conv_starters)/total_rows*100:.2f}%)")

    # Save summary dictionary to scratch for automated report generation
    summary = {
        "file_size_bytes": file_size_bytes,
        "file_size_mb": round(file_size_mb, 2),
        "total_rows": total_rows,
        "total_cols": total_cols,
        "columns": list(df.columns),
        "column_stats": col_stats,
        "full_dupes": int(full_dupes),
        "tweet_id_dupes": int(tweet_id_dupes),
        "inbound_counts": {str(k): int(v) for k, v in inbound_counts.items()},
        "total_authors": total_authors,
        "unique_companies": len(company_authors),
        "top_companies": {k: int(v) for k, v in company_authors.head(15).items()},
        "apple_outbound": len(apple_outbound),
        "apple_inbound_mentions": int(len(apple_inbound)),
        "min_date": str(min_date),
        "max_date": str(max_date),
        "time_span_days": int((max_date - min_date).days),
        "has_url_pct": round(has_url/total_rows*100, 2),
        "has_handle_pct": round(has_handle/total_rows*100, 2),
        "char_len_mean": round(float(df["char_len"].mean()), 1),
        "char_len_median": float(df["char_len"].median()),
        "char_len_max": int(df["char_len"].max()),
        "word_len_mean": round(float(df["word_len"].mean()), 1),
        "word_len_median": float(df["word_len"].median()),
        "word_len_max": int(df["word_len"].max()),
        "has_reply_to_count": int(has_reply_to),
        "has_response_id_count": int(has_response_id),
        "multi_response_count": int(multi_responses),
        "conv_starters_count": len(conv_starters)
    }

    out_json = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "inspection_stats.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\nWrote full inspection summary to {out_json}")

if __name__ == "__main__":
    run_inspection()
