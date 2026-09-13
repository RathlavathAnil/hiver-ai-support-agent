# Data Profile: Customer Support on Twitter Dataset

**Dataset Reference**: [Kaggle: thoughtvector/customer-support-on-twitter](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter)  
**Inspection Date**: September 2026  
**Inspection Script**: [`scripts/inspect_data.py`](../scripts/inspect_data.py)  
**Raw Data Integrity**: Raw CSV verified read-only and preserved unmodified in [`data/raw/twcs.csv`](../data/raw/twcs.csv).

---

## 1. File Metadata

| Attribute | Observed Statistic / Value |
|---|---|
| **Local File Path** | `data/raw/twcs.csv` |
| **File Size (Bytes)** | `516,508,641` bytes |
| **File Size (Megabytes)** | `492.58` MB (`0.48` GB) |
| **Encoding** | UTF-8 with multibyte Unicode (emojis, special punctuation) |
| **Line Delimiter** | Standard CRLF (`\r\n`) / LF (`\n`) |
| **Record Delimiter** | Comma (`,`), RFC 4180 compliant with double-quote escaping |
| **Total Rows (Records)** | `2,811,774` data rows (`2,811,775` lines including header) |

---

## 2. Schema, Columns & Missing Values

The schema was empirically discovered by parsing `data/raw/twcs.csv` with zero prior schema assumptions. The dataset consists of 7 columns:

| Column Name | Storage Type | Inferred Semantic Type | Non-Null Count | Null Count | Null % | Unique Values | Sample Value |
|---|---|---|---|---|---|---|---|
| `tweet_id` | `int64` | Primary Key Identifier | 2,811,774 | 0 | 0.00% | 2,811,774 | `1` |
| `author_id` | `string` | User / Brand Identifier | 2,811,774 | 0 | 0.00% | 702,777 | `"sprintcare"` / `"115712"` |
| `inbound` | `bool` | Boolean Directional Flag | 2,811,774 | 0 | 0.00% | 2 | `False` |
| `created_at` | `string` | UTC Timestamp (Twitter format) | 2,811,774 | 0 | 0.00% | 2,061,666 | `"Tue Oct 31 22:10:47 +0000 2017"` |
| `text` | `string` | Raw Tweet Message Body | 2,811,774 | 0 | 0.00% | 2,782,618 | `"@115712 I understand. I would like to assist you..."` |
| `response_tweet_id` | `string` | Child Tweet ID(s) | 1,771,145 | 1,040,629 | 37.01% | 1,771,145 | `"2"` or `"108,109"` |
| `in_response_to_tweet_id` | `float64` | Parent Tweet ID | 2,017,439 | 794,335 | 28.25% | 1,774,822 | `3.0` |

### Critical Schema Observations:
1. **Naming Conventions**: Notice that the column denoting parent relationship is named `in_response_to_tweet_id` (not `in_reply_to_tweet_id` as standard Twitter v1/v2 REST APIs name it).
2. **Cardinality of Primary Key**: `tweet_id` has exactly `2,811,774` unique values out of `2,811,774` rows. It is a strictly unique surrogate integer key.
3. **Completeness of Core Fields**: The core message metadata (`tweet_id`, `author_id`, `inbound`, `created_at`, and `text`) has **0 missing values (100% complete)** across all 2.81M rows.
4. **Structural Nulls in Relation Columns**:
   - `in_response_to_tweet_id` is null (`794,335` rows, 28.25%) specifically for **conversation root tweets** (tickets initiated by customers with no prior parent).
   - `response_tweet_id` is null (`1,040,629` rows, 37.01%) for **leaf tweets** in a conversation thread (tweets that concluded the interaction and received no further response).

---

## 3. Duplicate Records

* **Exact Full-Row Duplicates**: `0`
* **Duplicate `tweet_id` Instances**: `0`
* **Duplicate `text` Values**: `29,156` occurrences (1.04% of messages).  
  *Root Cause*: Automated corporate boilerplate replies (e.g., *"Please send us a DM with your account number and zip code so we can look into this"*), which repeated across identical customer inquiries.

---

## 4. Directionality: Customer vs. Company Messages

| Message Direction | `inbound` Flag | Total Count | Percentage | Description |
|---|---|---|---|---|
| **Customer Inquiries** | `True` | 1,537,843 | 54.69% | Incoming messages from users seeking support |
| **Brand / Company Replies** | `False` | 1,273,931 | 45.31% | Outgoing messages sent by official brand support handles |
| **Total** | — | **2,811,774** | **100.00%** | |

---

## 5. Brands & Author Distribution

* **Total Unique Authors**: `702,777`
* **Corporate Support Handles** (`inbound == False`): `108` distinct brand accounts.
* **Customer User Accounts** (`inbound == True`): `702,669` unique customer author IDs.
* **Customer Anonymization**: Customer author IDs are consistently masked in the raw dataset as numeric strings (e.g., `115712`, `115854`), protecting end-user privacy while retaining thread co-reference. Corporate handles remain unmasked plain strings (e.g., `AppleSupport`, `AmazonHelp`).

### Top 15 Corporate Brands by Outbound Volume:

| Rank | Brand Author Handle | Total Support Replies | Share of Corporate Tweets |
|---|---|---|---|
| 1 | `AmazonHelp` | 169,840 | 13.33% |
| 2 | **`AppleSupport`** | **106,860** | **8.39%** |
| 3 | `Uber_Support` | 56,270 | 4.42% |
| 4 | `SpotifyCares` | 43,265 | 3.40% |
| 5 | `Delta` | 42,253 | 3.32% |
| 6 | `Tesco` | 38,573 | 3.03% |
| 7 | `AmericanAir` | 36,764 | 2.89% |
| 8 | `TMobileHelp` | 34,317 | 2.69% |
| 9 | `comcastcares` | 33,031 | 2.59% |
| 10 | `British_Airways` | 29,361 | 2.30% |
| 11 | `SouthwestAir` | 28,977 | 2.27% |
| 12 | `VirginTrains` | 27,817 | 2.18% |
| 13 | `Ask_Spectrum` | 25,860 | 2.03% |
| 14 | `XboxSupport` | 24,557 | 1.93% |
| 15 | `sprintcare` | 22,381 | 1.76% |

---

## 6. Deep Profile: `@AppleSupport` Subset

As established in architectural decision [D1](../DECISION_LOG.md#d1-single-brand-focus-applesupport), this project focuses on **AppleSupport**:

| Metric | Value | Engineering Significance |
|---|---|---|
| **Outbound AppleSupport Tweets** | `106,860` | Massive ground truth demonstration corpus for RAG vector index |
| **Inbound Tweets Mentioning `@AppleSupport`** | `97,896` | Rich pool for customer inquiry intent discovery |
| **Direct Conversation Pairs Formed** | `106,648` | Matched `(customer_inquiry, apple_reply)` training/golden pairs |
| **Unique Customers Served** | `76,366` | Broad distribution with minimal customer-specific bias |
| **Median Response Time ($p50$)** | **70.97 minutes** | Real-world benchmark for human support delay (vs. $<3$s AI agent) |
| **$p25$ Response Time** | `24.80` minutes | First-quartile response window |
| **$p75$ Response Time** | `207.90` minutes | Third-quartile response window (~3.4 hours) |

### Sample Observed `@AppleSupport` Interaction Pair:
* **Customer Inquiry** (`tweet_id: 698`, `author_id: 115854`, `2017-10-31 22:17:40 UTC`):
  > *"@AppleSupport https://t.co/NV0yucs0lB"* *(Customer attached screenshot/link showing iOS glitch)*
* **AppleSupport Ground Truth Reply** (`tweet_id: 696`, `author_id: AppleSupport`, `2017-10-31 22:27:49 UTC`):
  > *"@115854 We're here for you. Which version of the iOS are you running? Check from Settings > General > About."*
  *(Response time: 10 minutes 9 seconds)*

---

## 7. Timestamps & Temporal Distribution

* **Raw Format**: RFC 2822 / Twitter format: `"%a %b %d %H:%M:%S %z %Y"` (e.g., `Tue Oct 31 22:10:47 +0000 2017`)
* **Earliest Observed Timestamp**: `2008-05-08 20:13:59+00:00`
* **Latest Observed Timestamp**: `2017-12-03 23:14:01+00:00`
* **Total Time Span**: `3,496` days (~9.5 years)
* **Unparseable Timestamps**: `0` (100% parseable)
* **Temporal Density**: Over 85% of conversation pairs are concentrated between **October 2017 and December 2017**, providing high temporal coherence in terminology, software versions (iOS 11), and product lines (iPhone X, iPhone 8).

---

## 8. Text Field Lexical & Structural Properties

### Length Distributions:

| Metric | Character Count | Word Count |
|---|---|---|
| **Minimum** | 1 | 1 |
| **5th Percentile ($p5$)** | 34 | 5 |
| **25th Percentile ($p25$)** | 78 | 13 |
| **Median ($p50$)** | **115** | **19** |
| **Mean** | 113.9 | 19.5 |
| **75th Percentile ($p75$)** | 139 | 24 |
| **95th Percentile ($p95$)** | 215 | 38 |
| **Maximum** | 513 | 137 |

### Special Token & Entity Occurrences:
1. **User Mentions (`@handle`)**: Present in **`97.88%`** of all tweets (`2,752,045` tweets). Every support interaction either addresses a brand or a customer.
2. **Hyperlinks / URLs (`https://t.co/...`)**: Present in **`22.46%`** of all tweets (`631,420` tweets). Often used by brands linking to knowledge base articles or DM links.
3. **HTML Escaped Entities**: High prevalence of entities like `&gt;`, `&lt;`, and `&amp;` (e.g., `Settings &gt; General &gt; About`). Must be unescaped during preprocessing.
4. **Empty or Whitespace-Only Messages**: **`0`**. Every row has substantive text content.
5. **Twitter Character Limit Shift**: Tweets prior to November 2017 adhere to the legacy 140-character limit; tweets after November 2017 reach up to 280 characters.

---

## 9. Thread & Graph Relationships Between Tweets

The dataset encodes conversational threads via a doubly-linked relational graph:

```
[Inbound Inquiry] ──(response_tweet_id)──> [Outbound Reply]
        ▲                                          │
        └────────(in_response_to_tweet_id)─────────┘
```

* **Tweets with `in_response_to_tweet_id` (Child Tweets)**: `2,017,439` (71.75%)
* **Tweets with `response_tweet_id` (Parent Tweets)**: `1,771,145` (62.99%)
* **Conversation Starter Inquiries**: `787,346` tweets (inbound customer messages with `in_response_to_tweet_id IS NULL`). These represent clean, unconditioned initial customer tickets.
* **1-to-Many Fan-Out (Multi-Response Tweets)**: `222,426` tweets (12.56% of parent tweets) contain **comma-separated values** in `response_tweet_id` (e.g., `"108,109,110"`). This occurs when an agent splits a long response across multiple tweets or when multiple agents reply to the same user tweet.

---

## 10. Key Engineering Implications for Hiver AI Support Agent

1. **Deterministic Conversation Pair Extraction**:  
   We can reconstruct complete `(Customer Ticket, Ground Truth Reply)` dyads with $100\%$ precision by performing an inner join on `author_id == 'AppleSupport'` where `apple.in_response_to_tweet_id == customer.tweet_id`.
2. **Text Normalization Requirements**:  
   Raw tweets require deterministic cleanup before ingestion into the vector store:
   - Decode HTML entities (`&gt;` $\rightarrow$ `>`, `&amp;` $\rightarrow$ `&`).
   - Strip leading `@mentions` to prevent brand persona confusion in prompt context.
   - Retain knowledge base URL tokens while masking personal link tokens.
3. **Vector Database Sizing**:  
   With 106,648 AppleSupport conversation pairs, indexing a high-signal subset (~10,000–25,000 most descriptive conversation pairs) into PostgreSQL `pgvector` will consume $< 150\text{ MB}$ of RAM and deliver sub-millisecond retrieval latency.
4. **Golden Evaluation Set Feasibility**:  
   With 787,346 conversation starters and 106,648 AppleSupport pairs, sampling a balanced, highly stratified 150–250 example golden test set is well-supported with zero synthetic data generation required.

---

*Inspection executed and verified reproducibly via `scripts/inspect_data.py`.*
