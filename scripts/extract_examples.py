"""
Extract rich, verified real examples for the intent taxonomy document.
"""

import os
import re
import html
import json
import yaml
import pandas as pd

def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = html.unescape(text)
    return text.strip()

def main():
    df = pd.read_csv("data/raw/twcs.csv")
    apple_out = df[(df["inbound"] == False) & (df["author_id"] == "AppleSupport")]
    pairs = apple_out.merge(
        df[["tweet_id", "author_id", "text", "created_at", "in_response_to_tweet_id"]],
        left_on="in_response_to_tweet_id",
        right_on="tweet_id",
        suffixes=("_apple", "_customer")
    )
    
    pairs["cust_clean"] = pairs["text_customer"].apply(clean_text)
    pairs["apple_clean"] = pairs["text_apple"].apply(clean_text)
    
    # Let's inspect specific categories
    intents = [
        ("BATTERY_PERFORMANCE", r"\b(battery|batteries|draining|drain|charge|charging|overheating|dies so fast|power off)\b"),
        ("SOFTWARE_UPDATE_OS", r"\b(ios\s*\d+|update|updating|updated|install|installation|downgrade|restore|beta|boot loop)\b"),
        ("HARDWARE_PHYSICAL_DAMAGE", r"\b(crack|cracked|broken|shattered|damaged|water damage|screen replacement|genius bar|repair|applecare)\b"),
        ("ACCOUNT_ACCESS_SECURITY", r"\b(apple id|icloud lock|activation lock|password|passcode|locked out|verification code|2fa|hacked)\b"),
        ("APP_CRASH_PERFORMANCE", r"\b(crash|crashes|crashing|freeze|freezing|lag|lagging|slow|unresponsive|black screen|frozen)\b"),
        ("NETWORK_CONNECTIVITY", r"\b(wi-?fi|bluetooth|cellular|no service|signal|hotspot|airdrop|lte|pairing|disconnecting)\b"),
        ("BILLING_SUBSCRIPTIONS", r"\b(billing|charge|charged|refund|subscription|subscriptions|apple music|itunes store|receipt|payment)\b"),
        ("AUDIO_SOUND_ISSUES", r"\b(sound|audio|speaker|mic|microphone|volume|earpiece|muffled|static|can't hear)\b"),
        ("ICLOUD_STORAGE_SYNC", r"\b(icloud storage|storage full|backup|sync|photos missing|restore backup|manage storage)\b"),
        ("GENERAL_PRODUCT_INQUIRY", r"\b(how do i|how to|compatible|trade-?in|warranty status|store hours|which iphone)\b")
    ]
    
    collected_examples = {}
    
    for intent_name, regex in intents:
        matched = pairs[pairs["cust_clean"].str.lower().str.contains(regex, regex=True, na=False)]
        # Filter for good clean standalone examples
        filtered = matched[
            (matched["cust_clean"].str.len() >= 40) &
            (matched["cust_clean"].str.len() <= 200) &
            (matched["cust_clean"].str.contains(r"@AppleSupport", case=False)) &
            (~matched["cust_clean"].str.contains(r"^[0-9\s]+$"))
        ]
        
        sample_list = []
        for _, r in filtered.head(5).iterrows():
            sample_list.append({
                "customer_tweet_id": int(r["tweet_id_customer"]),
                "customer_text": r["cust_clean"],
                "apple_tweet_id": int(r["tweet_id_apple"]),
                "apple_reply": r["apple_clean"]
            })
        collected_examples[intent_name] = sample_list

    # Multi-intent examples
    multi_filter = pairs[
        (pairs["cust_clean"].str.lower().str.contains(r"battery|drain", regex=True, na=False)) &
        (pairs["cust_clean"].str.lower().str.contains(r"ios\s*\d+|update", regex=True, na=False)) &
        (pairs["cust_clean"].str.len() >= 50)
    ].head(5)
    
    multi_list = []
    for _, r in multi_filter.iterrows():
        multi_list.append({
            "tweet_id": int(r["tweet_id_customer"]),
            "text": r["cust_clean"],
            "conflicting_intents": ["BATTERY_PERFORMANCE", "SOFTWARE_UPDATE_OS"],
            "resolution": "Classify as SOFTWARE_UPDATE_OS if battery drain started immediately after updating (as the update is the root cause), or BATTERY_PERFORMANCE if focus is on general battery health."
        })

    # Ambiguous examples
    ambig_filter = pairs[
        (pairs["cust_clean"].str.len() < 35) &
        (pairs["cust_clean"].str.contains(r"https://t\.co", regex=True, na=False))
    ].head(5)
    ambig_list = []
    for _, r in ambig_filter.iterrows():
        ambig_list.append({
            "tweet_id": int(r["tweet_id_customer"]),
            "text": r["cust_clean"],
            "ambiguity_reason": "Contains only a screenshot URL with minimal or no explanatory text. Requires multimodal parsing or clarification prompt."
        })

    # Account-specific / Escalation examples
    account_filter = pairs[
        pairs["cust_clean"].str.lower().str.contains(r"locked|disabled|stolen|passcode", regex=True, na=False) &
        (pairs["cust_clean"].str.len() >= 50)
    ].head(5)
    account_list = []
    for _, r in account_filter.iterrows():
        account_list.append({
            "tweet_id": int(r["tweet_id_customer"]),
            "text": r["cust_clean"],
            "escalation_reason": "Involves account security / device ownership authentication; cannot be resolved without human verification / secure DM."
        })

    # Good guidance examples
    good_filter = pairs[
        pairs["apple_clean"].str.contains(r"Settings >|restart|safari|support\.apple\.com", case=False, regex=True, na=False) &
        (pairs["cust_clean"].str.len() >= 45)
    ].head(5)
    good_list = []
    for _, r in good_filter.iterrows():
        good_list.append({
            "customer_tweet_id": int(r["tweet_id_customer"]),
            "customer_text": r["cust_clean"],
            "apple_tweet_id": int(r["tweet_id_apple"]),
            "apple_reply": r["apple_clean"],
            "why_good": "Contains precise navigation breadcrumbs (Settings > ...) or direct official Apple Support documentation links."
        })

    # Poor / Noisy historical examples
    noisy_filter = pairs[
        pairs["apple_clean"].str.contains(r"DM us|send us a DM|private link", case=False, regex=True, na=False) &
        (~pairs["apple_clean"].str.contains(r"Settings|restart|check|support\.apple", case=False, regex=True, na=False)) &
        (pairs["cust_clean"].str.len() >= 50)
    ].head(5)
    noisy_list = []
    for _, r in noisy_filter.iterrows():
        noisy_list.append({
            "customer_tweet_id": int(r["tweet_id_customer"]),
            "customer_text": r["cust_clean"],
            "apple_tweet_id": int(r["tweet_id_apple"]),
            "apple_reply": r["apple_clean"],
            "why_noisy": "Premature deflection to DM without offering standard diagnostic questions or basic troubleshooting steps."
        })

    export_data = {
        "intent_examples": collected_examples,
        "multi_intent_examples": multi_list,
        "ambiguous_examples": ambig_list,
        "account_specific_examples": account_list,
        "good_guidance_examples": good_list,
        "noisy_examples": noisy_list
    }

    with open("data/processed/discovered_examples.json", "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    print("Successfully exported discovered real examples to data/processed/discovered_examples.json")

if __name__ == "__main__":
    main()
