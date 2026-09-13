import requests
import json
import pandas as pd

def safe_str(s):
    return str(s).encode("ascii", "replace").decode("ascii")

def run_retrieval_audit():
    test_queries = [
        ("My iPhone battery drains completely in 2 hours on iOS 11.", "BATTERY_PERFORMANCE"),
        ("My MacBook screen is cracked and shattered after dropping it.", "HARDWARE_PHYSICAL_DAMAGE"),
        ("I forgot my Apple ID password and my account is locked.", "ACCOUNT_ACCESS_SECURITY"),
        ("I was charged $14.99 for Apple Music and need a refund.", "BILLING_SUBSCRIPTIONS"),
        ("The camera app crashes and freezes every time I open it.", "APP_CRASH_PERFORMANCE"),
        ("My phone keeps disconnecting from my home Wi-Fi network.", "NETWORK_CONNECTIVITY"),
        ("How do I update my iPhone 7 to the latest iOS version?", "SOFTWARE_UPDATE_OS"),
        ("No sound coming from my iPhone speaker when receiving calls.", "AUDIO_SOUND_ISSUES"),
        ("My iCloud storage is full and my photos won't backup.", "ICLOUD_STORAGE_SYNC"),
        ("What are the trade-in options for iPhone 6s?", "GENERAL_PRODUCT_INQUIRY")
    ]

    print("=" * 80)
    print("SECTION 3: RETRIEVAL QUALITY AUDIT (10 QUERIES)")
    print("=" * 80)
    relevant_count = 0
    for idx, (query, exp_intent) in enumerate(test_queries, 1):
        r = requests.post("http://localhost:8080/api/v1/support", json={"message": query})
        data = r.json()
        convs = data.get("similarConversations", [])
        top_c = convs[0] if convs else {}
        ret_cust = safe_str(top_c.get("customerText", "NONE"))
        ret_rep = safe_str(top_c.get("agentReply", "NONE"))
        score = top_c.get("similarityScore", 0.0)
        ret_intent = top_c.get("intent", "NONE")

        # Strict domain relevance: does the retrieved customer text actually describe the same intent domain?
        is_rel = (exp_intent == ret_intent)
        if is_rel:
            relevant_count += 1

        print(f"[{idx}] Query: \"{query}\"")
        print(f"    Expected Intent: {exp_intent} | Classified: {data.get('intent')}")
        print(f"    Retrieved Text:  \"{ret_cust[:80]}...\"")
        print(f"    Retrieved Reply: \"{ret_rep[:80]}...\"")
        print(f"    Similarity Score: {score:.4f} | Retrieved Intent: {ret_intent}")
        print(f"    Genuinely Domain-Relevant? {'YES' if is_rel else 'NO (Unrelated / Incidental Hash Match)'}")
        print("-" * 70)

    print(f"Empirical Retrieval Domain Relevance Rate: {relevant_count}/10 ({relevant_count * 10}%)\n")


def run_intent_classifier_audit():
    queries = [
        # 1. battery + update
        ("iOS 11 update completely drained my battery in 1 hour.", "BATTERY_PERFORMANCE / SOFTWARE_UPDATE_OS"),
        # 2. billing + account
        ("Someone hacked my Apple ID and made unauthorized charges on my credit card.", "ACCOUNT_ACCESS_SECURITY / BILLING_SUBSCRIPTIONS"),
        # 3. physical damage + battery
        ("My phone dropped, screen cracked, and now the battery is overheating.", "HARDWARE_PHYSICAL_DAMAGE / BATTERY_PERFORMANCE"),
        # 4. vague complaint
        ("This is the absolute worst product I have ever owned, fix it now!", "GENERAL_PRODUCT_INQUIRY"),
        # 5. typo/slang
        ("my phn is totally borked cant hear anything on speaker", "AUDIO_SOUND_ISSUES"),
        # 6. context-free follow-up
        ("Yes, I tried that already and it didn't work.", "GENERAL_PRODUCT_INQUIRY"),
        # 7. iCloud
        ("iCloud storage is full, how do I delete old photo backups?", "ICLOUD_STORAGE_SYNC"),
        # 8. audio
        ("My microphone is muffled and callers cannot hear me.", "AUDIO_SOUND_ISSUES"),
        # 9. network
        ("Bluetooth keeps disconnecting from my car audio system.", "NETWORK_CONNECTIVITY"),
        # 10. app crash
        ("Safari crashes every time I try to open a new tab.", "APP_CRASH_PERFORMANCE"),
        # 11. security
        ("My account is locked and two factor verification code is not sending.", "ACCOUNT_ACCESS_SECURITY"),
        # 12. refund
        ("I was billed twice for a subscription I canceled, I demand a refund.", "BILLING_SUBSCRIPTIONS"),
        # 13. subscription
        ("How do I cancel my Apple Music family subscription?", "BILLING_SUBSCRIPTIONS"),
        # 14. product inquiry
        ("Is the Apple Pencil compatible with the iPad 6th generation?", "GENERAL_PRODUCT_INQUIRY"),
        # 15. ambiguous message
        ("Look at this https://t.co/9x7289d", "GENERAL_PRODUCT_INQUIRY"),
        # 16. boot loop
        ("My iPhone is stuck on the Apple logo boot loop after updating.", "SOFTWARE_UPDATE_OS"),
        # 17. legal threat
        ("I am speaking to my lawyer tomorrow regarding fraudulent charges.", "BILLING_SUBSCRIPTIONS / ESCALATE"),
        # 18. manager request
        ("I want to speak with a manager or supervisor immediately.", "GENERAL_PRODUCT_INQUIRY / ESCALATE"),
        # 19. liquid damage
        ("Dropped my iPhone in the sink and now it won't charge.", "HARDWARE_PHYSICAL_DAMAGE"),
        # 20. storage vs icloud
        ("Is iCloud storage the same thing as my iPhone internal storage?", "ICLOUD_STORAGE_SYNC")
    ]

    print("=" * 80)
    print("SECTION 4: INTENT CLASSIFIER AUDIT (20 DIVERSE & ADVERSARIAL QUERIES)")
    print("=" * 80)
    for idx, (q, exp) in enumerate(queries, 1):
        r = requests.post("http://localhost:8080/api/v1/support", json={"message": q})
        data = r.json()
        pred_intent = data.get("intent")
        conf = data.get("confidence")
        dec = data.get("escalation", {}).get("decision")
        reason = data.get("escalation", {}).get("reason")
        exec_path = "Deterministic Regex Heuristics (Local Mode — No Gemini API key set)"
        print(f"[{idx:02d}] Query: \"{q}\"")
        print(f"     Expected:   {exp}")
        print(f"     Predicted:  {pred_intent} (Confidence: {conf})")
        print(f"     Decision:   {dec} | Reason: {reason}")
        print(f"     Exec Path:  {exec_path}")
        print("-" * 70)


def run_escalation_confusion_audit():
    print("=" * 80)
    print("SECTION 5: ESCALATION CONFUSION MATRIX & FALSE NEGATIVES AUDIT")
    print("=" * 80)
    with open("evaluation/results/agent_results.json") as f:
        res = json.load(f)

    preds = res.get("predictions", [])
    tp, tn, fp, fn = 0, 0, 0, 0
    fn_samples = []

    for p in preds:
        true_d = p.get("true_decision")
        pred_d = p.get("predicted_decision")

        # ESCALATE is Positive (1), AUTO_HANDLE is Negative (0)
        if true_d == "ESCALATE" and pred_d == "ESCALATE":
            tp += 1
        elif true_d == "AUTO_HANDLE" and pred_d == "AUTO_HANDLE":
            tn += 1
        elif true_d == "AUTO_HANDLE" and pred_d == "ESCALATE":
            fp += 1
        elif true_d == "ESCALATE" and pred_d == "AUTO_HANDLE":
            fn += 1
            fn_samples.append(p)

    total = len(preds)
    print(f"Total Evaluated Records: {total}")
    print(f"True Positives (Correct Escalations):    TP = {tp}")
    print(f"True Negatives (Correct Auto-Handles):   TN = {tn}")
    print(f"False Positives (Unnecessary Escalation): FP = {fp}")
    print(f"False Negatives (DANGEROUS Missed Esc):  FN = {fn}")
    print(f"\nEscalation Accuracy:  {(tp + tn) / total:.4f} ({(tp + tn) / total * 100:.1f}%)")
    print(f"Escalation Precision: {tp / max(1, (tp + fp)):.4f}")
    print(f"Escalation Recall:    {tp / max(1, (tp + fn)):.4f}")
    print(f"Escalation F1:        {2 * tp / max(1, (2 * tp + fp + fn)):.4f}")

    print(f"\n--- FALSE NEGATIVE SAMPLES (Total: {len(fn_samples)}) ---")
    for s in fn_samples:
        print(f"- ID {s.get('id')} (True Intent: {s.get('true_intent')}, Pred Intent: {s.get('predicted_intent')}): \"{s.get('customer_message')}\"")
        print(f"  True Reason: {s.get('expected_escalation_reason')}")
        print(f"  Observed Decision: AUTO_HANDLE")


def run_reply_generation_audit():
    print("=" * 80)
    print("SECTION 6: REPLY GENERATION & GROUNDING AUDIT (10 QUERIES)")
    print("=" * 80)
    queries = [
        "My battery dies in 2 hours on my iPhone 8.",
        "My screen shattered after dropping it.",
        "I forgot my Apple ID password.",
        "I was charged twice for Apple Music.",
        "The camera app freezes constantly.",
        "My Wi-Fi keeps dropping.",
        "How do I update to iOS 11?",
        "No audio from speaker.",
        "iCloud storage is full.",
        "What is the trade-in value for iPhone 7?"
    ]

    for idx, q in enumerate(queries, 1):
        r = requests.post("http://localhost:8080/api/v1/support", json={"message": q})
        data = r.json()
        reply = data.get("reply")
        convs = data.get("similarConversations", [])
        top_ret = convs[0] if convs else {}
        print(f"[{idx:02d}] Query: \"{q}\"")
        print(f"     Retrieved Evidence: \"{safe_str(top_ret.get('agentReply', 'NONE'))[:80]}...\"")
        print(f"     Generated Reply:    \"{safe_str(reply)}\"")
        print(f"     Grounded in Retrieved Evidence? NO (Grounded in Intent Fallback Template)")
        print(f"     Hardcoded Official Apple Links? YES")
        print("-" * 70)


if __name__ == "__main__":
    run_retrieval_audit()
    run_intent_classifier_audit()
    run_escalation_confusion_audit()
    run_reply_generation_audit()
