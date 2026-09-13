# Golden Evaluation Set Labelling Protocol & Annotation Guide

**Project**: Hiver AI Support Agent  
**Dataset Target**: `@AppleSupport` Golden Evaluation Set (`data/golden/golden_set.csv`)  
**Scope**: 200 Hand-Verified Golden Evaluation Records  
**Applicability**: Human Annotators, Machine Learning Engineers, Quality Auditors  

---

## 1. Golden Set Objectives & Core Philosophy

The Golden Evaluation Set is the absolute ground truth benchmark against which all three systems (Trivial Baseline, Traditional ML Baseline, and the Spring Boot AI Support Agent) will be evaluated.

### Core Tenets:
1. **Human Ground Truth**: Automated model predictions must **never** be substituted for human review. Every example must be verified by a human annotator.
2. **Zero Data Leakage**: The 200 tweets in this dataset are recorded in [`data/golden/golden_tweet_ids.txt`](golden_tweet_ids.txt) and must be strictly excluded from vector indexing, training splits, and prompt few-shot examples.
3. **Realism**: The dataset reflects real customer support complexity, including typos, punctuation omissions, multiple symptoms, emotional frustration, and incomplete context.

---

## 2. Intent Taxonomy & Classification Rules

Annotators must select **exactly one** primary intent from the 10 approved categories:

| Intent ID | Core Domain | Primary Indicators | Exclusion Criteria |
|---|---|---|---|
| `SOFTWARE_UPDATE_OS` | iOS / macOS Updates & Bugs | Mentions iOS version (e.g. 11.1), update verification error, installation failure, bootloop, request to downgrade. | If issue is solely battery drain after update, classify under `BATTERY_PERFORMANCE`. |
| `BATTERY_PERFORMANCE` | Battery Drain & Charging | Fast battery percentage loss, dying with 20-40% left, charging cable not recognized, phone overheating. | If device is physically bulging from battery swelling, classify under `HARDWARE_PHYSICAL_DAMAGE`. |
| `HARDWARE_PHYSICAL_DAMAGE` | Screen Cracks, Drops & Repairs | Cracked/shattered glass, liquid/water damage, physically broken buttons, Genius Bar repair booking, AppleCare+ fee. | Frozen screen without physical crack belongs in `APP_CRASH_PERFORMANCE`. |
| `ACCOUNT_ACCESS_SECURITY` | Apple ID, Passwords & 2FA | Disabled Apple ID, forgotten passcode/password, 2FA code not received, activation lock, phishing alerts. | Credit card decline on App Store belongs in `BILLING_SUBSCRIPTIONS`. |
| `APP_CRASH_PERFORMANCE` | App Crashes, Lag & Freezes | Specific apps quitting (Safari, Instagram), extreme typing lag, frozen touch display, black screen with audio. | If entire phone won't turn on or has physical screen crack. |
| `NETWORK_CONNECTIVITY` | Wi-Fi, Bluetooth & Cellular | Wi-Fi dropping, Bluetooth AirPods/car audio pairing failure, "No Service" cellular error, AirDrop failure. | Built-in speaker static belongs in `AUDIO_SOUND_ISSUES`. |
| `BILLING_SUBSCRIPTIONS` | App Store Charges & Refunds | Double charges, unauthorized purchases, subscription cancellation, refund requests, receipt inquiries. | Warranty repair cost estimates belong in `HARDWARE_PHYSICAL_DAMAGE`. |
| `AUDIO_SOUND_ISSUES` | Mic, Speaker & Call Sound | Callers cannot hear user (mic), crackling loudspeaker, muffled earpiece, stuck in "Headphone" mode. | Bluetooth connection loss belongs in `NETWORK_CONNECTIVITY`. |
| `ICLOUD_STORAGE_SYNC` | iCloud Storage & Backups | "iCloud Storage is Full" warning, failed overnight backup, missing photos after sync, contacts not restoring. | Forgotten Apple ID password belongs in `ACCOUNT_ACCESS_SECURITY`. |
| `GENERAL_PRODUCT_INQUIRY` | Feature How-To & Store Info | How to change wallpaper/setting, trade-in value, device compatibility, retail store operating hours. | Any active technical malfunction or hardware breakdown. |

---

## 3. Disambiguation & Boundary Rules

### A. Symptom vs. Suspected Cause (Multi-Intent)
* **Scenario**: Customer writes *"Updated to iOS 11 and now my battery drains in 2 hours"*
* **Annotation Heuristic**: Label by the **primary operational defect** rather than the suspected trigger.
  - Primary symptom = Battery $\rightarrow$ Assign **`BATTERY_PERFORMANCE`**.
  - If the customer reports multiple distinct subsystems failing (e.g. *"Updated to 11.1 and now Wi-Fi drops and screen freezes"*), label by the first actionable symptom (`NETWORK_CONNECTIVITY`) and mark `difficulty = HARD` with an explanatory note.

### B. Ambiguous / Insufficient Context Messages
* **Scenario**: Short tweet like *"@AppleSupport this keeps happening https://t.co/xyz"*
* **Annotation Heuristic**:
  1. Inspect the conversation context field. If the customer is following up on a known thread, annotate using the parent context.
  2. If the tweet is completely standalone and context-free, assign the most plausible intent from the image description or fallback to `GENERAL_PRODUCT_INQUIRY`. Mark `difficulty = HARD` and set `annotation_notes = "Ambiguous message with image link"`.

### C. Physical Damage vs. Software Glitch
* **Scenario**: Customer states *"My touch screen stopped working"*
* **Annotation Heuristic**:
  - If the customer mentions dropping the device or visible glass cracks $\rightarrow$ **`HARDWARE_PHYSICAL_DAMAGE`**.
  - If the screen is physically intact but unreactive to touch $\rightarrow$ **`APP_CRASH_PERFORMANCE`** (can be tested via force restart).

---

## 4. Routing Decision: `AUTO_HANDLE` vs. `ESCALATE`

Every record must have `expected_decision` marked as either `AUTO_HANDLE` or `ESCALATE`:

### When to Assign `AUTO_HANDLE`:
The issue can be safely guided or resolved through step-by-step diagnostic procedures, settings adjustments, or links to official Apple Knowledge Base articles:
- Software configuration & settings navigation (*Settings > General > ...*).
- General battery health tips & power management.
- Network reset instructions (*Reset Network Settings*).
- App update, force quit, and device restart guidance.
- Public feature information and documentation links.

### When to Assign `ESCALATE`:
Mandatory human intervention is required due to physical, legal, security, or private transactional barriers:
- **Physical Hardware Repairs**: Shattered screens, battery swelling, water damage, or booking a physical Genius Bar appointment.
- **Account Security & Lockouts**: Disabled Apple ID, lost/stolen device with 2FA, activation lock (requires proof of purchase).
- **Financial & Billing Transactions**: Unauthorized charges, payment disputes, or processing monetary refunds.
- **Extreme Customer Frustration / Legal Threats**: Hostile sentiment, threats of litigation, or severe repetitive unresolved failures.

> When marking `ESCALATE`, annotators must provide a concise, explicit reason in `expected_escalation_reason` (e.g., *"Unauthorized credit card charges require account-specific transaction inspection by a billing advisor."*).

---

## 5. Crafting Ideal Reference Replies

Historical human tweets often contain undesirable shortcuts (e.g. *"DM us"* with no explanation). An ideal `reference_reply` must meet these standards:
1. **Empathy & Professionalism**: Acknowledge the issue courteously without excessive sycophancy.
2. **Actionable First Step**: Ask the critical isolating question (device model, iOS version) or provide the verified setting path.
3. **No Dead Ends**: If escalating, explain *why* and provide the authoritative URL (`https://support.apple.com/contact`, `https://iforgot.apple.com`, or `https://reportaproblem.apple.com`).
4. **Length**: Concise and within standard support communication constraints (under 280 characters).

---

## 6. Difficulty Classification Criteria

* **`EASY`**:
  - Single, unambiguous defect stated clearly.
  - Standard technical terminology present (*"battery draining"*, *"Wi-Fi disconnecting"*, *"screen cracked"*).
  - Clear routing path.
* **`MEDIUM`**:
  - Contains typos, informal slang, or colloquial phrasing (*"phone is borked"*, *"dying quick"*).
  - Longer multi-sentence descriptions.
  - Edge-case escalation requiring policy boundary judgment.
* **`HARD`**:
  - Multi-intent messages with competing symptoms.
  - Ambiguous context or reliance on image attachments.
  - Contradictory customer statements (*"updated to iOS 11.2"* when only 11.1 exists).

---

*Use `python scripts/label_golden_set.py` to review, edit, and confirm each record.*
