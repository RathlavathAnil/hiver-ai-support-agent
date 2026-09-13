"""
Intent Discovery & Taxonomic Analysis on @AppleSupport Support Data
====================================================================
Analyzes actual historical @AppleSupport conversations to discover a practical,
empirically-grounded intent taxonomy (~8-10 intents).
"""

import re
import html
import json
import yaml
import pandas as pd
import numpy as np

def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = html.unescape(text)
    # Strip @mentions at start
    text = re.sub(r"^(@\w+\s*)+", "", text).strip()
    return text

def main():
    print("Loading raw dataset...")
    df = pd.read_csv("data/raw/twcs.csv")
    
    # Filter AppleSupport outbound and inbound customer pairs
    apple_out = df[(df["inbound"] == False) & (df["author_id"] == "AppleSupport")]
    pairs = apple_out.merge(
        df[["tweet_id", "author_id", "text", "created_at", "in_response_to_tweet_id"]],
        left_on="in_response_to_tweet_id",
        right_on="tweet_id",
        suffixes=("_apple", "_customer")
    )
    print(f"Total @AppleSupport conversation pairs: {len(pairs):,}")
    
    # Preprocess customer text
    pairs["clean_cust_text"] = pairs["text_customer"].apply(clean_text)
    pairs["cust_text_lower"] = pairs["clean_cust_text"].str.lower()
    
    # Define candidate intent clustering patterns
    intent_definitions = {
        "BATTERY_PERFORMANCE": {
            "name": "BATTERY_PERFORMANCE",
            "title": "Battery Drain, Charging & Power Issues",
            "regex": r"\bbatter(y|ies)\b|\bcharg(ing|er|e)\b|\bdrain(ing|s|ed)?\b|\boverheat(ing|s)?\b|\bdying (fast|quick|in)\b|\bpower off\b|\bturn(ing)? off by itself\b|\bbattery health\b|\bpercentage\b",
            "escalation": "AUTO_HANDLE",
            "description": "Issues concerning battery life degradation, rapid power drain, charging cable/port failures, overheating, and unexpected device shutdowns."
        },
        "SOFTWARE_UPDATE_OS": {
            "name": "SOFTWARE_UPDATE_OS",
            "title": "iOS & OS Updates, Glitches & Installations",
            "regex": r"\bios\s*\d+|\bupdate(d|s|ing)?\b|\bupgrad(e|ing|ed)\b|\binstall(ing|ed|ation)?\b|\bdowngrade\b|\bbeta\b|\brestore\b|\bboot loop\b|\bapple logo\b|\bsoftware\b|\bitunes update\b",
            "escalation": "AUTO_HANDLE",
            "description": "Problems updating iOS/macOS, update verification loops, installation failures, system glitches immediately following an update, or requests to revert/downgrade versions."
        },
        "HARDWARE_PHYSICAL_DAMAGE": {
            "name": "HARDWARE_PHYSICAL_DAMAGE",
            "title": "Hardware Damage, Screen Cracks & Physical Repairs",
            "regex": r"\b(crack(ed)?|broken|shatter(ed)?|damage(d)?|dropped|water|liquid|spill(ed)?|screen replacement|genius bar|apple care\+?|repair(s|ed|ing)?|cost to fix|fix my screen|physical|button broken|home button)\b",
            "escalation": "ESCALATE",
            "description": "Physical damage to device screens, chassis, buttons, water/liquid damage, or inquiries regarding repair appointments, replacement costs, and AppleCare+ warranty claims."
        },
        "ACCOUNT_ACCESS_SECURITY": {
            "name": "ACCOUNT_ACCESS_SECURITY",
            "title": "Apple ID, iCloud Lock, Passwords & Authentication",
            "regex": r"\b(apple id|icloud lock|activation lock|password|passcode|locked out|security question|verification code|two factor|2fa|forgot.*(password|pin|code)|hacked|unauthorized access|disabled id)\b",
            "escalation": "ESCALATE",
            "description": "Inability to sign in to Apple ID, forgotten passcodes, device activation locks, two-factor authentication failures, locked/disabled accounts, or potential security breaches."
        },
        "APP_CRASH_PERFORMANCE": {
            "name": "APP_CRASH_PERFORMANCE",
            "title": "App Crashes, Device Freezing & Performance Lag",
            "regex": r"\b(crash(es|ed|ing)?|freez(e|ing|es)?|lag(ging|gy|s)?|slow|unresponsive|black screen|frozen|touch.*(not working|unresponsive)|keyboard lag|app store won't open|safari crash(es)?)\b",
            "escalation": "AUTO_HANDLE",
            "description": "Native or third-party apps crashing, system UI unresponsiveness, extreme lag/sluggishness, frozen screens, or non-functional touch input."
        },
        "NETWORK_CONNECTIVITY": {
            "name": "NETWORK_CONNECTIVITY",
            "title": "Wi-Fi, Bluetooth, Cellular Data & Signal",
            "regex": r"\b(wi-?fi|bluetooth|cellular|data|no service|signal|disconnect(ing|ed|s)?|hotspot|airdrop|lte|4g|sim card|pairing|connect.*(car|speaker|headphones|airpods))\b",
            "escalation": "AUTO_HANDLE",
            "description": "Problems connecting to Wi-Fi networks, Bluetooth accessories (AirPods, car systems), cellular reception loss ('No Service'), AirDrop failure, or personal hotspot dropouts."
        },
        "BILLING_SUBSCRIPTIONS": {
            "name": "BILLING_SUBSCRIPTIONS",
            "title": "App Store Charges, Subscriptions & Refunds",
            "regex": r"\b(bill(ing|ed|s)?|charge(d|s)?|refund(s|ed|ing)?|subscript(ion|ions)|apple music|itunes store|credit card|payment|receipt|invoice|accidental purchase|in-app purchase|money)\b",
            "escalation": "ESCALATE",
            "description": "Questions regarding unauthorized or unexpected charges on credit card/iTunes, refund requests for apps/subscriptions, managing active Apple subscriptions, or payment method declines."
        },
        "AUDIO_SOUND_ISSUES": {
            "name": "AUDIO_SOUND_ISSUES",
            "title": "Microphone, Speaker, AirPods & Call Audio",
            "regex": r"\b(sound|audio|speaker|mic|microphone|volume|headphone(s)?|earpiece|can't hear|hear me|muffled|static|buzzing|airpods audio)\b",
            "escalation": "AUTO_HANDLE",
            "description": "Issues where audio is distorted, speakers produce crackling/static, callers cannot hear through the microphone, or headphones/earpieces fail to output sound."
        },
        "ICLOUD_STORAGE_SYNC": {
            "name": "ICLOUD_STORAGE_SYNC",
            "title": "iCloud Storage Full, Backup & Data Sync",
            "regex": r"\b(icloud storage|storage full|backup(s|ed|ing)?|sync(ing|ed)?|photo(s)? (not|missing|gone)|restore backup|manage storage|notes sync|contacts sync)\b",
            "escalation": "AUTO_HANDLE",
            "description": "Warnings about iCloud storage being full, backup failures, missing photos after sync, or contacts/notes failing to synchronize across devices."
        },
        "GENERAL_PRODUCT_INQUIRY": {
            "name": "GENERAL_PRODUCT_INQUIRY",
            "title": "General Inquiries, Compatibility & Feature Availability",
            "regex": r"\b(how do i|how to|feature|support|compatible|trade-?in|warranty status|store hours|when will|is it possible|which iphone|specifications)\b",
            "escalation": "AUTO_HANDLE",
            "description": "General pre-purchase questions, feature discovery, trade-in valuation, device compatibility inquiries, or general store policies."
        }
    }

    # Assign intents hierarchically / multi-match tracking
    assignments = []
    for idx, row in pairs.iterrows():
        text = row["cust_text_lower"]
        matched_intents = []
        for intent_k, intent_v in intent_definitions.items():
            if re.search(intent_v["regex"], text):
                matched_intents.append(intent_k)
        assignments.append(matched_intents)
    
    pairs["matched_intents"] = assignments
    pairs["match_count"] = pairs["matched_intents"].apply(len)
    
    # Primary intent assignment: first match or single match
    def get_primary_intent(matches):
        if len(matches) == 0:
            return "UNCLASSIFIED_OTHER"
        return matches[0]

    pairs["primary_intent"] = pairs["matched_intents"].apply(get_primary_intent)
    
    print("\n=== INTENT DISTRIBUTION ===")
    dist = pairs["primary_intent"].value_counts()
    dist_pct = pairs["primary_intent"].value_counts(normalize=True) * 100
    dist_table = pd.DataFrame({
        "Intent": dist.index,
        "Count": dist.values,
        "Percentage": dist_pct.round(2).values
    })
    print(dist_table.to_string(index=False))

    print(f"\nSingle-intent tweets: {(pairs['match_count'] == 1).sum():,} ({(pairs['match_count'] == 1).mean()*100:.2f}%)")
    print(f"Multi-intent tweets (>=2 matches): {(pairs['match_count'] >= 2).sum():,} ({(pairs['match_count'] >= 2).mean()*100:.2f}%)")
    print(f"Unclassified / Other tweets: {(pairs['match_count'] == 0).sum():,} ({(pairs['match_count'] == 0).mean()*100:.2f}%)")

    # Extract 5 real representative examples per intent
    taxonomy_output = {}
    for intent_k, intent_v in intent_definitions.items():
        subset = pairs[pairs["primary_intent"] == intent_k]
        # Filter for clean representative examples (>30 chars, <160 chars)
        good_examples = subset[
            (subset["clean_cust_text"].str.len() > 35) & 
            (subset["clean_cust_text"].str.len() < 160) &
            (subset["clean_cust_text"].str.contains(r"[a-zA-Z]{4,}", regex=True))
        ].head(10)
        
        sample_list = []
        for _, r in good_examples.head(5).iterrows():
            sample_list.append({
                "tweet_id": int(r["tweet_id_customer"]),
                "customer_text": str(r["text_customer"]).strip(),
                "clean_text": str(r["clean_cust_text"]).strip(),
                "apple_reply": str(r["text_apple"]).strip(),
                "apple_tweet_id": int(r["tweet_id_apple"])
            })
            
        count = int(dist.get(intent_k, 0))
        pct = float(round(dist_pct.get(intent_k, 0.0), 2))
        
        taxonomy_output[intent_k] = {
            "name": intent_k,
            "title": intent_v["title"],
            "definition": intent_v["description"],
            "count": count,
            "percentage": pct,
            "default_escalation": intent_v["escalation"],
            "representative_examples": sample_list
        }

    # Extract multi-intent examples
    multi_df = pairs[pairs["match_count"] >= 2].head(10)
    multi_examples = []
    for _, r in multi_df.head(5).iterrows():
        multi_examples.append({
            "tweet_id": int(r["tweet_id_customer"]),
            "text": str(r["text_customer"]).strip(),
            "matched_intents": r["matched_intents"]
        })

    # Extract ambiguous / low context examples
    ambiguous_df = pairs[(pairs["match_count"] == 0) & (pairs["clean_cust_text"].str.len() < 30)].head(10)
    ambiguous_examples = []
    for _, r in ambiguous_df.head(5).iterrows():
        ambiguous_examples.append({
            "tweet_id": int(r["tweet_id_customer"]),
            "text": str(r["text_customer"]).strip()
        })

    # Save to JSON / YAML
    with open("data/processed/intent_taxonomy.json", "w", encoding="utf-8") as f:
        json.dump(taxonomy_output, f, indent=2)
    
    with open("data/processed/intent_taxonomy.yaml", "w", encoding="utf-8") as f:
        yaml.dump(taxonomy_output, f, sort_keys=False)

    print("\nSaved taxonomy to data/processed/intent_taxonomy.yaml and .json")

if __name__ == "__main__":
    main()
