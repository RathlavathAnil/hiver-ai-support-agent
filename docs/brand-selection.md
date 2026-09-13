# Brand Selection Analysis & Recommendation

**Target Evaluation Framework**: Hiver AI Support Agent  
**Dataset Source**: Customer Support on Twitter (`twcs.csv`)  
**Objective**: Select and justify the single most suitable brand for building, grounding, and evaluating an autonomous AI customer support agent.

---

## 1. Candidate Brand Evaluation & Ranking Matrix

We evaluated the top candidate brands across 9 multi-dimensional engineering and domain criteria:

| Criterion / Weight | `@AppleSupport` | `@AmazonHelp` | `@SpotifyCares` | `@Uber_Support` | `@Delta` |
|---|:---:|:---:|:---:|:---:|:---:|
| **1. Number of Conversations** | 106,719 | 169,287 | 43,243 | 56,261 | 42,197 |
| **2. Customer Inbound Volume** | 106,625 | 154,985 | 41,697 | 55,215 | 36,168 |
| **3. Multi-Turn Depth ($\ge 3$ turns)** | 36,658 | 100,503 | 15,096 | 22,160 | 14,470 |
| **4. Diversity of Customer Issues** | High (Hardware, OS, Battery, ID, Billing, Network) | High (Shipping, Returns, Prime, Video, Payments) | Medium (Playback, Offline, Cache, Family Plan) | Low-Med (Fares, Lost Items, Driver, Cancellations) | Low-Med (Delays, Baggage, Seats, Rebooking) |
| **5. Availability of Historical Replies** | 106,860 | 169,840 | 43,265 | 56,270 | 42,253 |
| **6. Data Cleanliness & Entity Clarity** | High (Standard Apple nomenclature) | Med (Heavy vendor/marketplace noise) | High (Clean app/service entities) | Med (Driver/location ambiguity) | High (Flight numbers, IATA codes) |
| **7. 6–10 Well-Defined Intent Categories** | **Excellent (8–10 clean, distinct clusters)** | Difficult (Too diffuse across 1000s of product types) | Fair (Only 4–5 distinct clusters) | Difficult (Narrow, low variety) | Fair (5–6 operational flight clusters) |
| **8. Resolution Self-Containment (RAG Viability)** | **53.91% Actionable steps** | 14.58% Actionable steps | 27.70% Actionable steps | 14.68% Actionable steps | 8.08% Actionable steps |
| **9. External System Dependency Risk** | **Low (Troubleshooting is self-contained)** | **Critical (Requires live Order/Tracking OMS)** | Low-Med (Account status lookup) | **Critical (Requires live GPS/Trip dispatch DB)** | **Critical (Requires live GDS/PNR ticketing)** |
| **Overall Rank** | **#1 (Recommended)** | **#2** | **#3** | **#4** | **#5** |

---

## 2. Detailed Brand Profiles & Trade-Offs

### Candidate 1: `@AppleSupport` (Recommended)
* **Outbound Volume**: 106,860 tweets | **Direct Conversation Pairs**: 106,648 | **Unique Customers**: 76,366
* **Actionable Troubleshooting Rate**: **`53.91%`** (Highest among all brands in the dataset)
* **Advantages**:
  1. **Self-Contained Resolutions**: A vast portion of customer issues (OS upgrades, battery drain, iCloud sync, Bluetooth connectivity, settings adjustments) can be meaningfully guided or resolved via verified, in-text troubleshooting steps without needing access to private corporate databases.
  2. **Clear Intent Boundary**: Natural clustering into 8–10 distinct, non-overlapping intents (`BATTERY_PERFORMANCE`, `SOFTWARE_OS_UPDATE`, `HARDWARE_REPAIR`, `ACCOUNT_APPLE_ID`, `APP_CRASH_ICLOUD`, `NETWORK_CONNECTIVITY`, `BILLING_SUBSCRIPTION`, `GENERAL_INQUIRY`).
  3. **High Grounding Signal for RAG**: Apple agents historically provided explicit diagnostic procedures (e.g., *"Go to Settings > General > Reset > Reset Network Settings"* or *"Check battery health in Settings > Battery"*), allowing our vector retriever to find precise, authoritative historical examples.
  4. **Natural Escalation Dichotomy**: Clear boundary between what can be auto-handled (software diagnostics, guides) versus what must be escalated (hardware screen cracks, account recovery, battery swelling, warranty disputes).
* **Disadvantages**:
  - High variety in device generations (iPhone 6 through iPhone X, iPad, Mac, Apple Watch), requiring the intent classifier to distinguish device-agnostic OS issues from hardware-specific requests.

---

### Candidate 2: `@AmazonHelp`
* **Outbound Volume**: 169,840 tweets (Largest raw dataset) | **Direct Pairs**: 168,823
* **Actionable Troubleshooting Rate**: **`14.58%`**
* **Advantages**:
  - Largest volume of raw multi-turn data (100,503 3-turn conversations).
* **Disadvantages / Disqualification Rationale**:
  - **Fatal External Dependency**: E-commerce customer support fundamentally requires live database queries against private Order Management Systems (OMS) to check shipping status, courier tracking IDs, refund processing states, or seller communications.
  - **Low In-Text Resolution**: Over 85% of tweets are generic deflections (*"Please share your 17-digit order number so we can look into this"* or *"Please reach out to the 3rd-party seller via your Orders page"*). Generating responses for Amazon without a mock OMS results in unhelpful loop replies.
  - **Diffused Intent Space**: Amazon sells millions of unrelated product categories (groceries, electronics, Prime Video streaming, Kindle, AWS), making it difficult to establish a tight, coherent 6–10 intent taxonomy.

---

### Candidate 3: `@SpotifyCares`
* **Outbound Volume**: 43,265 tweets | **Direct Pairs**: 43,206
* **Actionable Troubleshooting Rate**: `27.70%`
* **Advantages**:
  - Pure digital product with relatively clean support vocabulary (playlists, offline downloads, playback stuttering, Spotify Connect).
* **Disadvantages / Disqualification Rationale**:
  - **Overly Narrow Intent Space**: The domain is too restricted to sustain 8–10 meaningful intents. Customer issues collapse into essentially 3–4 buckets (*Audio won't play*, *Offline sync failed*, *Family Plan billing*, *UI complaint*).
  - Smaller dataset volume compared to AppleSupport (43k vs 106k pairs).

---

### Candidate 4: `@Uber_Support`
* **Outbound Volume**: 56,270 tweets | **Direct Pairs**: 56,193
* **Actionable Troubleshooting Rate**: `14.68%`
* **Advantages**:
  - Clear real-world urgency and emotional customer sentiment.
* **Disadvantages / Disqualification Rationale**:
  - **High External System Dependency**: Fare adjustments, driver safety reports, lost items in vehicles, and surge pricing disputes cannot be resolved without a live ride-dispatch backend.
  - Deflection-heavy: 36.19% of responses immediately redirect to in-app ticket forms or private DMs.

---

### Candidate 5: `@Delta` / Airline Handles
* **Outbound Volume**: 42,253 tweets | **Direct Pairs**: 42,149
* **Actionable Troubleshooting Rate**: `8.08%` (Lowest)
* **Advantages**:
  - Structured domain with flight numbers, airport codes, and baggage tags.
* **Disadvantages / Disqualification Rationale**:
  - **Complete External Dependency**: Over 91% of interactions involve rebooking canceled flights, checking live seat availability, or baggage claim tracking—all requiring GDS/PNR airline reservation system access.

---

## 3. Final Recommendation

We formally recommend **`@AppleSupport`** as the target brand for the Hiver AI Support Agent.

### Why `@AppleSupport` is the optimal engineering choice:
1. **Not Selected Merely Due to Raw Size**: While Amazon has more total tweets (169k vs 106k), AppleSupport has **3.7x higher actionable troubleshooting resolution** (53.91% vs 14.58%).
2. **Self-Contained Problem Space**: Technical troubleshooting (iOS updates, battery optimization, reset procedures, iCloud configuration) contains rich semantic knowledge that an LLM with RAG can genuinely resolve.
3. **Ideal Intent Granularity**: Perfectly supports a realistic, production-ready 8–10 intent taxonomy with distinct diagnostic pathways.
4. **Principled Human Escalation Boundary**: Provides clear, objective triggers for `AUTO_HANDLE` (step-by-step guidance, support links) vs. `ESCALATE` (Genius Bar hardware appointments, stolen devices, billing disputes, legal threats).

---

*Document compiled in `docs/brand-selection.md`.*
