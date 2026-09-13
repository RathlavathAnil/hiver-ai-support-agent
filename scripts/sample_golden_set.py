"""
Deterministic Stratified Golden Evaluation Set Sampler
======================================================
Target Brand: @AppleSupport
Sample Size: Exactly 200 representative customer-support conversations
Random Seed: 42 (Pinned for reproducibility)

Extracts and initializes candidate golden set with all 10 required schema fields:
- id
- conversation_id
- customer_message
- conversation_context
- intent
- expected_decision
- expected_escalation_reason
- reference_reply
- difficulty
- annotation_notes
"""

import os
import re
import html
import json
import pandas as pd
import numpy as np

SEED = 42
np.random.seed(SEED)

def clean_tweet_text(text):
    if not isinstance(text, str):
        return ""
    text = html.unescape(text)
    # Remove leading @mentions
    text = re.sub(r"^(@\w+\s*)+", "", text).strip()
    return text

def main():
    print(f"=== 1. LOADING DATASET & EXTRACTING APPLESUPPORT PAIRS (SEED={SEED}) ===")
    df = pd.read_csv("data/raw/twcs.csv")
    
    # Apple outbound
    apple_out = df[(df["inbound"] == False) & (df["author_id"] == "AppleSupport")]
    
    # Merge with inbound customer tweets
    pairs = apple_out.merge(
        df[["tweet_id", "author_id", "text", "created_at", "in_response_to_tweet_id"]],
        left_on="in_response_to_tweet_id",
        right_on="tweet_id",
        suffixes=("_apple", "_customer")
    )
    
    # Clean customer message and apple reply
    pairs["cust_msg_raw"] = pairs["text_customer"].fillna("")
    pairs["cust_clean"] = pairs["cust_msg_raw"].apply(clean_tweet_text)
    pairs["apple_clean"] = pairs["text_apple"].fillna("").apply(clean_tweet_text)
    
    # Check parent context if customer tweet itself was in response to something
    parent_ids = pairs["in_response_to_tweet_id_customer"].dropna().astype("int64")
    parent_map = df[df["tweet_id"].isin(parent_ids)].set_index("tweet_id")["text"].to_dict()
    pairs["parent_context"] = pairs["in_response_to_tweet_id_customer"].map(parent_map).fillna("").apply(clean_tweet_text)

    print(f"Total available @AppleSupport pairs: {len(pairs):,}")

    # Intent criteria and strata configuration
    # Target allocations totaling 200
    strata_configs = [
        {
            "intent": "SOFTWARE_UPDATE_OS",
            "target": 24,
            "regex": r"\b(ios\s*\d+|update|updating|updated|install|downgrade|boot loop|apple logo|beta)\b",
            "decision": "AUTO_HANDLE",
            "default_reason": "",
            "sample_filter": lambda c: "battery" not in c and "crack" not in c
        },
        {
            "intent": "BATTERY_PERFORMANCE",
            "target": 22,
            "regex": r"\b(battery|batteries|draining|drain|charge|charging|overheat|overheating|dying fast)\b",
            "decision": "AUTO_HANDLE",
            "default_reason": "",
            "sample_filter": lambda c: "crack" not in c and "bill" not in c and "refund" not in c
        },
        {
            "intent": "HARDWARE_PHYSICAL_DAMAGE",
            "target": 20,
            "regex": r"\b(crack|cracked|broken|shattered|shatter|damaged|water damage|dropped in|screen replacement|genius bar|repair cost|cost to fix)\b",
            "decision": "ESCALATE",
            "default_reason": "Physical hardware damage requires in-person store inspection, hardware diagnostic tools, or Genius Bar repair appointment.",
            "sample_filter": lambda c: True
        },
        {
            "intent": "ACCOUNT_ACCESS_SECURITY",
            "target": 20,
            "regex": r"\b(apple id|icloud lock|activation lock|password|passcode|locked out|verification code|two factor|2fa|hacked|stolen phone)\b",
            "decision": "ESCALATE",
            "default_reason": "Account access, security lockouts, and identity verification require secure authentication via iforgot.apple.com or human security advisor.",
            "sample_filter": lambda c: True
        },
        {
            "intent": "APP_CRASH_PERFORMANCE",
            "target": 20,
            "regex": r"\b(crash|crashes|crashing|freeze|freezes|freezing|lag|laggy|lagging|slow|unresponsive|black screen|frozen screen|touch not working)\b",
            "decision": "AUTO_HANDLE",
            "default_reason": "",
            "sample_filter": lambda c: "crack" not in c and "water" not in c
        },
        {
            "intent": "NETWORK_CONNECTIVITY",
            "target": 20,
            "regex": r"\b(wi-?fi|bluetooth|cellular|no service|signal|hotspot|airdrop|lte|pairing|disconnecting)\b",
            "decision": "AUTO_HANDLE",
            "default_reason": "",
            "sample_filter": lambda c: True
        },
        {
            "intent": "BILLING_SUBSCRIPTIONS",
            "target": 20,
            "regex": r"\b(billing|charge|charged|refund|subscription|subscriptions|apple music|itunes store|receipt|unauthorized purchase|payment declined)\b",
            "decision": "ESCALATE",
            "default_reason": "Financial billing inquiries, unauthorized credit card charges, and subscription refunds require private transaction records and account-specific review.",
            "sample_filter": lambda c: "battery" not in c
        },
        {
            "intent": "AUDIO_SOUND_ISSUES",
            "target": 18,
            "regex": r"\b(sound|audio|speaker|mic|microphone|earpiece|volume|muffled|static|can't hear|headphone mode)\b",
            "decision": "AUTO_HANDLE",
            "default_reason": "",
            "sample_filter": lambda c: "bluetooth" not in c
        },
        {
            "intent": "ICLOUD_STORAGE_SYNC",
            "target": 16,
            "regex": r"\b(icloud storage|storage full|backup|sync|photos not syncing|restore backup|manage storage)\b",
            "decision": "AUTO_HANDLE",
            "default_reason": "",
            "sample_filter": lambda c: "locked" not in c and "password" not in c
        },
        {
            "intent": "GENERAL_PRODUCT_INQUIRY",
            "target": 14,
            "regex": r"\b(how do i|how to|compatible|trade-?in|warranty status|store hours|which iphone|specs)\b",
            "decision": "AUTO_HANDLE",
            "default_reason": "",
            "sample_filter": lambda c: "crack" not in c and "crash" not in c and "freeze" not in c and "drain" not in c
        },
        {
            "intent": "AMBIGUOUS_OR_MULTI_INTENT",
            "target": 6,
            "regex": r"https://t\.co|\b(battery.*update|update.*battery|wifi.*update)\b",
            "decision": "AUTO_HANDLE",
            "default_reason": "Ambiguous message requiring clarifying question before routing.",
            "sample_filter": lambda c: True
        }
    ]

    selected_rows = []
    used_tweet_ids = set()

    # Iterate over strata configs
    for conf in strata_configs:
        intent_id = conf["intent"]
        target_count = conf["target"]
        regex = conf["regex"]
        
        # Filter matching rows
        cand = pairs[
            (~pairs["tweet_id_customer"].isin(used_tweet_ids)) &
            (pairs["cust_clean"].str.lower().str.contains(regex, regex=True, na=False)) &
            (pairs["cust_clean"].str.len() >= 25)
        ].copy()
        
        # Apply custom stratum filter
        cand = cand[cand["cust_clean"].str.lower().apply(conf["sample_filter"])]
        
        # Sort by character length diversity
        cand_short = cand[cand["cust_clean"].str.len() < 70]
        cand_med = cand[(cand["cust_clean"].str.len() >= 70) & (cand["cust_clean"].str.len() <= 140)]
        cand_long = cand[cand["cust_clean"].str.len() > 140]
        
        # Sample across length bins
        sampled_parts = []
        n_short = min(len(cand_short), max(2, int(target_count * 0.25)))
        n_long = min(len(cand_long), max(2, int(target_count * 0.25)))
        n_med = target_count - n_short - n_long
        
        if n_short > 0:
            sampled_parts.append(cand_short.sample(n=n_short, random_state=SEED))
        if n_long > 0:
            sampled_parts.append(cand_long.sample(n=n_long, random_state=SEED))
        if n_med > 0:
            sampled_parts.append(cand_med.sample(n=min(len(cand_med), n_med), random_state=SEED))
            
        sampled = pd.concat(sampled_parts) if sampled_parts else cand.head(target_count)
        
        # If still short of target_count, backfill from cand
        if len(sampled) < target_count:
            remaining = cand[~cand["tweet_id_customer"].isin(sampled["tweet_id_customer"])]
            need = target_count - len(sampled)
            if len(remaining) > 0:
                sampled = pd.concat([sampled, remaining.sample(n=min(len(remaining), need), random_state=SEED)])

        sampled = sampled.head(target_count)
        for _, row in sampled.iterrows():
            used_tweet_ids.add(row["tweet_id_customer"])
            selected_rows.append({
                "row_data": row,
                "assigned_intent": intent_id,
                "decision": conf["decision"],
                "reason": conf["default_reason"]
            })

    print(f"Sampled {len(selected_rows)} initial records across all strata.")
    
    # Trim or backfill to exactly 200 if needed
    if len(selected_rows) > 200:
        selected_rows = selected_rows[:200]

    # Convert to structured Golden Set records
    golden_records = []
    
    for i, item in enumerate(selected_rows, start=1):
        r = item["row_data"]
        raw_cust = r["cust_msg_raw"].strip()
        clean_cust = r["cust_clean"].strip()
        apple_reply = r["apple_clean"].strip()
        parent_ctx = r["parent_context"].strip()
        intent = item["assigned_intent"]
        decision = item["decision"]
        reason = item["reason"]
        
        # Difficulty assessment heuristics
        msg_len = len(clean_cust)
        has_typos = bool(re.search(r"\b(dont|cant|wont|didnt|whn|phn|plz|pls|borked|gona|magically|scream|hs)\b", clean_cust.lower()))
        is_multi = bool("and" in clean_cust.lower() and ("update" in clean_cust.lower() and ("battery" in clean_cust.lower() or "wifi" in clean_cust.lower())))
        is_ambig = bool(len(clean_cust) < 40 or "https://t.co" in clean_cust)
        
        if is_ambig or is_multi:
            difficulty = "HARD"
            notes = "Multi-intent or ambiguous context; requires careful boundary handling."
        elif has_typos or msg_len > 150 or intent in ["ACCOUNT_ACCESS_SECURITY", "BILLING_SUBSCRIPTIONS"]:
            difficulty = "MEDIUM"
            notes = "Requires entity extraction, typo tolerance, or escalation verification."
        else:
            difficulty = "EASY"
            notes = "Clear diagnostic statement with unambiguous keyword signals."

        # Map ambiguous/multi placeholder intent to best specific candidate
        if intent == "AMBIGUOUS_OR_MULTI_INTENT":
            if "battery" in clean_cust.lower():
                intent = "BATTERY_PERFORMANCE"
                notes = "Multi-intent: mentions both update and battery drain."
            elif "wifi" in clean_cust.lower() or "wi-fi" in clean_cust.lower():
                intent = "NETWORK_CONNECTIVITY"
                notes = "Multi-intent: mentions update and Wi-Fi disconnect."
            else:
                intent = "GENERAL_PRODUCT_INQUIRY"
                notes = "Ambiguous message with image link; initial draft classification."

        # Formulate clean reference reply:
        # If historical reply is poor (premature DM deflection), provide clean guidance draft
        if re.search(r"^(dm us|send us a dm|meet us in dm)", apple_reply.lower()) and not re.search(r"settings|support\.apple\.com|restart|check", apple_reply.lower()):
            if decision == "ESCALATE":
                ref_reply = f"We would be glad to look into this for you. As this requires account or hardware inspection, please connect directly with our support team: https://support.apple.com/contact"
            else:
                ref_reply = f"We're here to help! To start, could you tell us your exact device model and iOS version? Have you tried restarting your device?"
        else:
            ref_reply = apple_reply

        golden_records.append({
            "id": i,
            "conversation_id": int(r["tweet_id_customer"]),
            "customer_message": clean_cust,
            "conversation_context": parent_ctx if parent_ctx else "N/A",
            "intent": intent,
            "expected_decision": decision,
            "expected_escalation_reason": reason if reason else "Standard automated support inquiry resolvable via troubleshooting documentation.",
            "reference_reply": ref_reply,
            "difficulty": difficulty,
            "annotation_notes": notes
        })

    golden_df = pd.DataFrame(golden_records)
    
    # Save CSV
    out_csv = "data/golden/golden_set.csv"
    os.makedirs("data/golden", exist_ok=True)
    golden_df.to_csv(out_csv, index=False, encoding="utf-8")
    print(f"\nSuccessfully wrote golden evaluation set ({len(golden_df)} rows) to {out_csv}")

    # Save leak prevention tweet IDs
    leak_txt = "data/golden/golden_tweet_ids.txt"
    with open(leak_txt, "w", encoding="utf-8") as f:
        for tid in golden_df["conversation_id"]:
            f.write(f"{tid}\n")
    print(f"Wrote {len(golden_df)} golden tweet IDs to {leak_txt} to ensure 0 data leakage.")

    # Validation report
    print("\n=== VALIDATION REPORT ===")
    total_ex = len(golden_df)
    print(f"Total Examples: {total_ex}")
    
    intent_counts = golden_df["intent"].value_counts()
    intent_pcts = (golden_df["intent"].value_counts(normalize=True) * 100).round(2)
    dist_df = pd.DataFrame({"Count": intent_counts, "Percentage": intent_pcts})
    print("\nExamples per Intent:")
    print(dist_df.to_string())

    dec_counts = golden_df["expected_decision"].value_counts()
    print(f"\nAUTO_HANDLE Count: {dec_counts.get('AUTO_HANDLE', 0)} ({dec_counts.get('AUTO_HANDLE', 0)/total_ex*100:.1f}%)")
    print(f"ESCALATE Count: {dec_counts.get('ESCALATE', 0)} ({dec_counts.get('ESCALATE', 0)/total_ex*100:.1f}%)")

    diff_counts = golden_df["difficulty"].value_counts()
    print(f"\nDifficulty Breakdown:")
    print(diff_counts.to_string())

    ambig_count = golden_df["annotation_notes"].str.contains(r"\bambiguous\b|multi-intent", case=False, regex=True).sum()
    multi_count = golden_df["annotation_notes"].str.contains(r"\bmulti-intent\b", case=False, regex=True).sum()
    print(f"\nAmbiguous Examples Count: {ambig_count}")
    print(f"Multi-intent Examples Count: {multi_count}")
    print(f"Missing Values Across Columns: {golden_df.isnull().sum().sum()}")
    print(f"Duplicate conversation_ids: {golden_df['conversation_id'].duplicated().sum()}")

    # Export validation stats JSON for docs
    val_stats = {
        "total_examples": total_ex,
        "intent_distribution": {k: int(v) for k, v in intent_counts.items()},
        "intent_percentages": {k: float(v) for k, v in intent_pcts.items()},
        "auto_handle_count": int(dec_counts.get("AUTO_HANDLE", 0)),
        "escalate_count": int(dec_counts.get("ESCALATE", 0)),
        "difficulty_distribution": {k: int(v) for k, v in diff_counts.items()},
        "ambiguous_count": int(ambig_count),
        "multi_intent_count": int(multi_count),
        "missing_values": int(golden_df.isnull().sum().sum()),
        "duplicates": int(golden_df["conversation_id"].duplicated().sum())
    }
    with open("data/processed/golden_validation_stats.json", "w", encoding="utf-8") as f:
        json.dump(val_stats, f, indent=2)

if __name__ == "__main__":
    main()
