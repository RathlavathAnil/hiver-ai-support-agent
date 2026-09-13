"""
Interactive Golden Evaluation Set Human Labelling Interface
===========================================================
Allows an engineer / annotator to review every golden example, verify or correct:
- intent
- expected_decision (AUTO_HANDLE vs ESCALATE)
- expected_escalation_reason
- reference_reply
- difficulty
- annotation_notes

Saves progress incrementally to data/golden/golden_set.csv.
"""

import os
import sys
import pandas as pd

GOLDEN_CSV = os.path.join(os.path.dirname(__file__), "..", "data", "golden", "golden_set.csv")

TAXONOMY = [
    "SOFTWARE_UPDATE_OS",
    "BATTERY_PERFORMANCE",
    "HARDWARE_PHYSICAL_DAMAGE",
    "ACCOUNT_ACCESS_SECURITY",
    "APP_CRASH_PERFORMANCE",
    "NETWORK_CONNECTIVITY",
    "BILLING_SUBSCRIPTIONS",
    "AUDIO_SOUND_ISSUES",
    "ICLOUD_STORAGE_SYNC",
    "GENERAL_PRODUCT_INQUIRY"
]

def print_help():
    print("\nCommands:")
    print("  [Enter]       : Accept current labels and advance to next record")
    print("  1-10          : Change Intent to corresponding number")
    print("  d             : Toggle Expected Decision (AUTO_HANDLE <-> ESCALATE)")
    print("  reason <text> : Set expected escalation reason")
    print("  reply <text>  : Set reference reply")
    print("  diff <E/M/H>  : Set difficulty (EASY, MEDIUM, HARD)")
    print("  note <text>   : Add/update annotation notes")
    print("  b             : Go back to previous record")
    print("  jump <id>     : Jump to record ID (1-200)")
    print("  summary       : Show label distribution summary")
    print("  q             : Save and exit")

def display_record(row, current_idx, total):
    print("\n" + "="*80)
    print(f" RECORD {row['id']} / {total} (Tweet ID: {row['conversation_id']}) — Difficulty: [{row['difficulty']}] — Status: [{row.get('label_status', 'DRAFT')}]")
    print("="*80)
    print(f"CUSTOMER MESSAGE:\n  \"{row['customer_message']}\"")
    if row.get("conversation_context") and str(row["conversation_context"]).strip() not in ["", "N/A", "nan"]:
        print(f"\nCONVERSATION CONTEXT:\n  \"{row['conversation_context']}\"")
    print("\nCURRENT LABELS:")
    print(f"  [Status]            : {row.get('label_status', 'DRAFT')}")
    print(f"  [Intent]            : {row['intent']}")
    print(f"  [Decision]          : {row['expected_decision']}")
    if row["expected_decision"] == "ESCALATE":
        print(f"  [Escalation Reason] : {row['expected_escalation_reason']}")
    print(f"  [Reference Reply]   : \"{row['reference_reply']}\"")
    print(f"  [Notes]             : {row.get('annotation_notes', '')}")
    print("-" * 80)
    print("Available Intents:")
    for i, intent_name in enumerate(TAXONOMY, 1):
        marker = " [*]" if intent_name == row["intent"] else ""
        print(f"  {i:2d}. {intent_name}{marker}")

def main():
    if not os.path.exists(GOLDEN_CSV):
        print(f"Error: Golden set not found at {GOLDEN_CSV}")
        sys.exit(1)
        
    df = pd.read_csv(GOLDEN_CSV)
    if "label_status" not in df.columns:
        df["label_status"] = "DRAFT"

    total = len(df)
    verified = (df["label_status"] == "HUMAN_VERIFIED").sum()
    print(f"Loaded {total} golden set records ({verified} HUMAN_VERIFIED, {total - verified} DRAFT)")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--summary":
        print("\nCurrent Golden Set Distribution:")
        print(f"\nVerification Status:\n{df['label_status'].value_counts().to_string()}")
        print(f"\nIntents:\n{df['intent'].value_counts().to_string()}")
        print(f"\nDecisions:\n{df['expected_decision'].value_counts().to_string()}")
        print(f"\nDifficulty:\n{df['difficulty'].value_counts().to_string()}")
        return

    # Auto-resume at first unverified DRAFT record if available
    draft_indices = df[df["label_status"] != "HUMAN_VERIFIED"].index
    idx = int(draft_indices[0]) if len(draft_indices) > 0 else 0
    if idx > 0:
        print(f"[INFO] Resuming review at first unverified record: #{df.iloc[idx]['id']} (Index {idx + 1}/{total})")

    while 0 <= idx < total:
        row = df.iloc[idx].copy()
        display_record(row, idx + 1, total)
        
        cmd = input("\nEnter command (? for help): ").strip()
        
        if cmd == "":
            # User accepted current labels for this record
            df.at[idx, "label_status"] = "HUMAN_VERIFIED"
            df.to_csv(GOLDEN_CSV, index=False, encoding="utf-8")
            print(f"[OK] Record #{row['id']} verified.")
            idx += 1
            continue
        elif cmd == "?":
            print_help()
            input("\nPress Enter to continue...")
            continue
        elif cmd.lower() == "q":
            df.to_csv(GOLDEN_CSV, index=False, encoding="utf-8")
            verified_count = (df["label_status"] == "HUMAN_VERIFIED").sum()
            print(f"\nSaved progress to {GOLDEN_CSV}. ({verified_count}/{total} records HUMAN_VERIFIED). Exiting.")
            break
        elif cmd.lower() == "b":
            if idx > 0:
                idx -= 1
            else:
                print("Already at first record.")
            continue
        elif cmd.lower().startswith("jump "):
            try:
                target_id = int(cmd.split()[1])
                target_idx = df[df["id"] == target_id].index
                if len(target_idx) > 0:
                    idx = target_idx[0]
                else:
                    print("Invalid ID.")
            except Exception as e:
                print(f"Error parsing ID: {e}")
            continue
        elif cmd.lower() == "d":
            new_dec = "ESCALATE" if row["expected_decision"] == "AUTO_HANDLE" else "AUTO_HANDLE"
            df.at[idx, "expected_decision"] = new_dec
            df.at[idx, "label_status"] = "HUMAN_VERIFIED"
            if new_dec == "ESCALATE" and not df.at[idx, "expected_escalation_reason"]:
                df.at[idx, "expected_escalation_reason"] = "Requires human agent intervention or account verification."
            df.to_csv(GOLDEN_CSV, index=False, encoding="utf-8")
            print(f"Updated expected_decision to: {new_dec} [HUMAN_VERIFIED]")
            continue
        elif cmd.isdigit() and 1 <= int(cmd) <= len(TAXONOMY):
            new_intent = TAXONOMY[int(cmd) - 1]
            df.at[idx, "intent"] = new_intent
            df.at[idx, "label_status"] = "HUMAN_VERIFIED"
            df.to_csv(GOLDEN_CSV, index=False, encoding="utf-8")
            print(f"Updated intent to: {new_intent} [HUMAN_VERIFIED]")
            continue
        elif cmd.lower().startswith("reason "):
            reason_text = cmd[7:].strip()
            df.at[idx, "expected_escalation_reason"] = reason_text
            df.at[idx, "label_status"] = "HUMAN_VERIFIED"
            df.to_csv(GOLDEN_CSV, index=False, encoding="utf-8")
            print(f"Updated escalation reason [HUMAN_VERIFIED].")
            continue
        elif cmd.lower().startswith("reply "):
            reply_text = cmd[6:].strip()
            df.at[idx, "reference_reply"] = reply_text
            df.at[idx, "label_status"] = "HUMAN_VERIFIED"
            df.to_csv(GOLDEN_CSV, index=False, encoding="utf-8")
            print(f"Updated reference reply [HUMAN_VERIFIED].")
            continue
        elif cmd.lower().startswith("diff "):
            d = cmd[5:].strip().upper()
            mapping = {"E": "EASY", "M": "MEDIUM", "H": "HARD", "EASY": "EASY", "MEDIUM": "MEDIUM", "HARD": "HARD"}
            if d in mapping:
                df.at[idx, "difficulty"] = mapping[d]
                df.at[idx, "label_status"] = "HUMAN_VERIFIED"
                df.to_csv(GOLDEN_CSV, index=False, encoding="utf-8")
                print(f"Updated difficulty to: {mapping[d]} [HUMAN_VERIFIED]")
            else:
                print("Invalid difficulty. Choose E, M, or H.")
            continue
        elif cmd.lower().startswith("note "):
            note_text = cmd[5:].strip()
            df.at[idx, "annotation_notes"] = note_text
            df.at[idx, "label_status"] = "HUMAN_VERIFIED"
            df.to_csv(GOLDEN_CSV, index=False, encoding="utf-8")
            print(f"Updated annotation notes [HUMAN_VERIFIED].")
            continue
        elif cmd.lower() == "summary":
            print("\nCurrent Verification Status:")
            print(df["label_status"].value_counts().to_string())
            print("\nCurrent Intent Breakdown:")
            print(df["intent"].value_counts().to_string())
            input("\nPress Enter to continue...")
            continue
        else:
            print("Unrecognized command. Type ? for help.")
            continue

if __name__ == "__main__":
    main()
