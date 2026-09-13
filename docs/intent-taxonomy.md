# Intent Taxonomy & Discovery Specification (@AppleSupport)

**Dataset Analyzed**: `@AppleSupport` Customer Support Conversations (`data/raw/twcs.csv`)  
**Total Conversations Inspected**: `106,648` verified `(customer_inquiry, apple_reply)` pairs  
**Taxonomy Design Principle**: Empirically grounded in actual customer support dialogs; avoids artificial fine-graining; maps cleanly to diagnostic workflows and escalation boundaries.  
**Machine-Readable Config**: [`data/processed/intent_taxonomy.yaml`](../data/processed/intent_taxonomy.yaml)

---

## 1. Intent Distribution Overview

The taxonomy comprises **10 mutually exclusive, operationally actionable intent categories**:

| Intent Identifier | Operational Domain | Volume (Est.) | Share (%) | Default Routing |
|---|---|:---:|:---:|:---:|
| `SOFTWARE_UPDATE_OS` | iOS/macOS update glitches, install loops & downgrades | 29,695 | 27.84% | `AUTO_HANDLE` |
| `BATTERY_PERFORMANCE` | Rapid battery drain, charging failures & overheating | 10,243 | 9.60% | `AUTO_HANDLE` |
| `APP_CRASH_PERFORMANCE` | App crashes, UI lag, frozen touch & system freeze | 2,962 | 2.78% | `AUTO_HANDLE` |
| `NETWORK_CONNECTIVITY` | Wi-Fi dropouts, Bluetooth pairing, cellular & hotspot | 2,362 | 2.21% | `AUTO_HANDLE` |
| `GENERAL_PRODUCT_INQUIRY` | Feature configuration, compatibility, trade-in & store info | 2,336 | 2.19% | `AUTO_HANDLE` |
| `BILLING_SUBSCRIPTIONS` | App Store charges, recurring subscriptions & refunds | 1,904 | 1.79% | `ESCALATE` |
| `HARDWARE_PHYSICAL_DAMAGE` | Screen cracks, liquid damage, broken buttons & Genius Bar | 1,489 | 1.40% | `ESCALATE` |
| `ACCOUNT_ACCESS_SECURITY` | Apple ID locks, password resets, 2FA & activation lock | 1,337 | 1.25% | `ESCALATE` |
| `AUDIO_SOUND_ISSUES` | Microphone, speaker distortion, earpiece & call sound | 1,210 | 1.13% | `AUTO_HANDLE` |
| `ICLOUD_STORAGE_SYNC` | iCloud storage full alerts, backup failures & photo sync | 558 | 0.52% | `AUTO_HANDLE` |
| *Unclassified / Media-Only* | *Image-only attachments, mid-thread follow-ups, vents* | *52,552* | *49.28%* | *Varies (See Sec. B)* |
| **Total Analyzed** | — | **106,648** | **100.00%** | — |

---

## 2. Comprehensive Intent Catalog

---

### 1. `BATTERY_PERFORMANCE`
* **Short Definition**: Customer reports rapid battery power drain, device dying with percentage remaining, slow charging, overheating while powering, or degraded battery health.
* **What Belongs**:
  - Unexplained fast battery drops (e.g., 40% to 7% in 5 minutes).
  - Device shutting down unexpectedly despite battery remaining.
  - Charging cable not recognized, slow charging, or port loose.
  - Overheating during charging or everyday usage.
  - Inquiries regarding battery replacement capacity or health percentage.
* **What Does NOT Belong**:
  - Battery drain explicitly tied to an iOS update installation bug (assign to `SOFTWARE_UPDATE_OS`).
  - Swollen battery physically separating the screen (assign to `HARDWARE_PHYSICAL_DAMAGE`).
  - Disputed credit card charges for battery repair (assign to `BILLING_SUBSCRIPTIONS`).
* **Commonly Confused With**: `SOFTWARE_UPDATE_OS` (when updates are mentioned), `HARDWARE_PHYSICAL_DAMAGE` (when physical bulging occurs).
* **Why Useful for Support**: High customer anxiety with standardized self-serve diagnostics (checking Battery Usage by App, Low Power Mode, disabling Background Refresh).
* **Suggested Default Escalation**: `AUTO_HANDLE` (Provide diagnostic settings guidance).

#### 5 Verified Real Examples:
1. **Customer** (`tweet_id: 3767`):
   > *"@AppleSupport I’m no expert in battery life but 40% doesn’t go to 7% in 5minutes"*  
   **Apple Reply** (`tweet_id: 3766`): *"@116622 We understand your concerns, and want to help. Which device is this happening on?"*
2. **Customer** (`tweet_id: 1775`):
   > *"@AppleSupport @116102 Battery life just got worst."*  
   **Apple Reply** (`tweet_id: 1777`): *"@116103 We'll make sure to get this straightened out. DM us, and we'll see you there. https://t.co/GDrqU22YpT"*
3. **Customer** (`tweet_id: 2616`):
   > *"@AppleSupport why is my battery life short? I updated to 11.1, my battery is poor. Wife didn’t she likes her battery life"*  
   **Apple Reply** (`tweet_id: 2614`): *"@116334 Let’s work together on this situation. To clarify, did this start after updating to iOS 11.1? Also, which device are you using?"*
4. **Customer** (`tweet_id: 4900`):
   > *"@AppleSupport @116860 I have and my battery life has become even worse"*  
   **Apple Reply** (`tweet_id: 4902`): *"@116861 Let's look into this further in DM. https://t.co/GDrqU22YpT"*
5. **Customer** (`tweet_id: 745`):
   > *"@AppleSupport I need the software update urgently. The battery lasts literally half a day 🙍🏼🙁@AppleSupport"*  
   **Apple Reply** (`tweet_id: 744`): *"@115865 Hi there! What type of device are we working with?"*

---

### 2. `SOFTWARE_UPDATE_OS`
* **Short Definition**: Customer experiences failures during iOS/macOS update downloads, verification errors, boot loops, post-update system glitches, or requests to downgrade.
* **What Belongs**:
  - Stuck on "Verifying Update" or "Preparing Update".
  - OTA or iTunes update installation failures.
  - Inability to downgrade back to previous iOS version (e.g. iOS 11 $\rightarrow$ iOS 10).
  - System boot loop (stuck on Apple logo).
  - System-wide UI glitches appearing immediately after an OS update (e.g., keyboard autocorrect glitch).
* **What Does NOT Belong**:
  - Individual 3rd party app crashing (assign to `APP_CRASH_PERFORMANCE`).
  - Wi-Fi failing to connect after update (assign to `NETWORK_CONNECTIVITY`).
* **Commonly Confused With**: `APP_CRASH_PERFORMANCE`, `BATTERY_PERFORMANCE`.
* **Why Useful for Support**: Largest single volume category during release cycles; easily triaged with known recovery mode / patch information.
* **Suggested Default Escalation**: `AUTO_HANDLE` (Supply official update troubleshooting steps or patch notes).

#### 5 Verified Real Examples:
1. **Customer** (`tweet_id: 5839`):
   > *"Just updated to iOS 11.2 and my keyboard is completely screwed up and glitchy now 🤦‍♂️ @115858 @AppleSupport"*  
   **Apple Reply** (`tweet_id: 5836`): *"@117106 We'd like to assist as best we can. Do you mean iOS 11.1 which was released today?"*
2. **Customer** (`tweet_id: 10689`):
   > *"updated to iOS 11.1 @AppleSupport and there's so many glitches and bugs I found inside the update"*  
   **Apple Reply** (`tweet_id: 10688`): *"@117966 We'd be happy to help. Send us a DM and we can start there. https://t.co/GDrqU22YpT"*
3. **Customer** (`tweet_id: 10691`):
   > *"Downloaded new software update and my iPhone 6S in perfect condition magically became inoperably glitchy. What a coincidence @AppleSupport"*  
   **Apple Reply** (`tweet_id: 10690`): *"@117967 We want you to have a smooth experience with our updates. What exactly is happening with your iPhone?"*
4. **Customer** (`tweet_id: 714`):
   > *"Hey @AppleSupport and anyone else who upgraded to ios11.1, are y’all having issues with capital “I️” in the Mail app? As it puts in “A”?"*  
   **Apple Reply** (`tweet_id: 712`): *"@115856 Hey, let's work together to figure out what's going on. Meet us in DM and we'll continue from there. https://t.co/GDrqU22YpT"*
5. **Customer** (`tweet_id: 736`):
   > *"Thank you @AppleSupport I updated my phone and now it is even slower and barely works. Thank you for ruining my phone.😤"*  
   **Apple Reply** (`tweet_id: 734`): *"@115864 We'd like to help, but we'll need more details. What's happening on your device and which model is it? Do you have iOS 11.1?"*

---

### 3. `HARDWARE_PHYSICAL_DAMAGE`
* **Short Definition**: Inquiries regarding broken screen glass, chassis damage, water immersion, malfunctioning physical buttons, AppleCare+ claims, or Genius Bar repair visits.
* **What Belongs**:
  - Cracked, shattered, or splintered screen glass.
  - Liquid/water intrusion or dropped in pool/toilet.
  - Physical home button, power button, or mute switch broken.
  - Repair cost estimates, AppleCare+ deductible questions, and Genius Bar appointments.
* **What Does NOT Belong**:
  - Touchscreen unresponsive due to software freeze (assign to `APP_CRASH_PERFORMANCE`).
  - Software volume slider missing (assign to `AUDIO_SOUND_ISSUES`).
* **Commonly Confused With**: `APP_CRASH_PERFORMANCE` (when screen digitizer breaks vs software lag).
* **Why Useful for Support**: Safety and liability boundaries; software cannot fix cracked glass, requiring direct hardware handoff.
* **Suggested Default Escalation**: `ESCALATE` (Requires physical inspection and repair booking).

#### 5 Verified Real Examples:
1. **Customer** (`tweet_id: 32433`):
   > *"@AppleSupport My iPhone screen glass is completely cracked. Still the touch screen works. Can I change the glass alone or the display too?"*  
   **Apple Reply** (`tweet_id: 32432`): *"@123192 We're glad to look into all options with you to have your iPhone serviced. Please DM us to proceed. https://t.co/GDrqU22YpT"*
2. **Customer** (`tweet_id: 94891`):
   > *"I got my phone fixed 2 weeks ago and I just dropped my phone with a case on it ON CARPET from at MOST four feet, and my screen shattered.... @AppleSupport how?"*  
   **Apple Reply** (`tweet_id: 94890`): *"@136626 We're sorry that this happened, so let us help you get it taken care of. DM us so we can better assist you: https://t.co/GDrqU22YpT"*
3. **Customer** (`tweet_id: 98873`):
   > *"My iPhone screen is broken @AppleSupport"*  
   **Apple Reply** (`tweet_id: 98872`): *"@137645 We are here to help. DM us your current country and we can take a look at this. https://t.co/GDrqU22YpT"*
4. **Customer** (`tweet_id: 143550`):
   > *"I️ think my iPhone X has water damage was in not even a foot of water for 3 seconds .... @AppleSupport is this a joke"*  
   **Apple Reply** (`tweet_id: 143549`): *"@148434 We want to help. What indication do you have that there is water damage? DM us and we'll get started. https://t.co/GDrqU22YpT"*
5. **Customer** (`tweet_id: 150034`):
   > *"@AppleSupport No, thank you. If it involves spending 2 hours at a Genius Bar and spending money on repair, I’ll pass. Thank you for your response."*  
   **Apple Reply** (`tweet_id: 150036`): *"@150209 Let us know if you change your mind, and we'll take a look at this with you."*

---

### 4. `ACCOUNT_ACCESS_SECURITY`
* **Short Definition**: Customer cannot authenticate Apple ID, has forgotten lockscreen passcode or account password, encounters 2FA code delivery failures, disabled account warnings, or suspected account compromise.
* **What Belongs**:
  - "Your Apple ID has been disabled for security reasons".
  - Forgotten password or lockscreen passcode.
  - Two-factor verification code sent to lost, stolen, or broken phone.
  - Device locked with Activation Lock / Find My iPhone.
  - Phishing emails or fraudulent SMS alerts imitating Apple.
* **What Does NOT Belong**:
  - Payment method declined in App Store (assign to `BILLING_SUBSCRIPTIONS`).
  - iCloud backup storage full (assign to `ICLOUD_STORAGE_SYNC`).
* **Commonly Confused With**: `ICLOUD_STORAGE_SYNC`, `BILLING_SUBSCRIPTIONS`.
* **Why Useful for Support**: High-security risk; strictly enforces verification protocols (`iforgot.apple.com`) without exposing agent credentials.
* **Suggested Default Escalation**: `ESCALATE` (Requires identity verification and private secure flow).

#### 5 Verified Real Examples:
1. **Customer** (`tweet_id: 42656`):
   > *"@AppleSupport Hey Apple! Having issues with my ID and already changed my password. Trying to update my computer but says ID is disabled?"*  
   **Apple Reply** (`tweet_id: 42654`): *"@125430 We can help! Check out this article for guidance with your Apple ID: https://t.co/HH37urdbz9"*
2. **Customer** (`tweet_id: 59606`):
   > *"Uhhhh @AppleSupport , this you? 🤔 why is it saying my Apple ID will be disabled? https://t.co/onVhJjkYAU"*  
   **Apple Reply** (`tweet_id: 59605`): *"@129598 This isn't us, and we'd love to see it. You can forward it to the address in this article: https://t.co/LNMCdqt6fD"*
3. **Customer** (`tweet_id: 92741`):
   > *"@AppleSupport - security patch installed automatically on Mac this morning and now NO user password works. Mac is locked. Need help ASAP"*  
   **Apple Reply** (`tweet_id: 92740`): *"@136086 We'd love to help with this. Are you able to get into the Guest user? Let us know in DM, and we'll team up to see what's going on. https://t.co/GDrqU22YpT"*
4. **Customer** (`tweet_id: 112824`):
   > *"@AppleSupport My phone got stolen but i can't change my apple id password because of the 2 step verification that requires my phone! Do you have a uk based email that i can contact about this?"*  
   **Apple Reply** (`tweet_id: 112823`): *"@141077 We'd like to help any way we can over Twitter. The first steps to take would be here: https://t.co/fUoKdx4Yut As you're unable to change your Apple ID password, we recommend reaching out to our Apple ID group using this link: https://t.co/UJm15vmMM2"*
5. **Customer** (`tweet_id: 112830`):
   > *"@AppleSupport my iCloud account was just locked down, &amp; I had to unlock it with my 2 factor code and then change my password. Was it a hacking attempt...?"*  
   **Apple Reply** (`tweet_id: 112829`): *"@141079 Thanks for reaching out to us. We have an article that can help ensure your Apple ID is secure: https://t.co/SdkqXUvz1a"*

---

### 5. `APP_CRASH_PERFORMANCE`
* **Short Definition**: Third-party or native applications repeatedly crashing, system UI lag, frozen display, unresponsive touchscreen, or extreme performance degradation.
* **What Belongs**:
  - Apps closing immediately upon launch (Instagram, WhatsApp, Safari, Camera).
  - Unresponsive touch screen or frozen UI.
  - Severe keyboard typing delay and stuttering.
  - Device freezing during everyday operations.
* **What Does NOT Belong**:
  - Device will not power on due to dead battery (assign to `BATTERY_PERFORMANCE`).
  - Physically shattered screen digitizer (assign to `HARDWARE_PHYSICAL_DAMAGE`).
* **Commonly Confused With**: `SOFTWARE_UPDATE_OS`, `HARDWARE_PHYSICAL_DAMAGE`.
* **Why Useful for Support**: Highly actionable with rapid self-serve steps (force quit app, restart device, re-install app, free device storage).
* **Suggested Default Escalation**: `AUTO_HANDLE`.

#### 5 Verified Real Examples:
1. **Customer** (`tweet_id: 1773`):
   > *"@AppleSupport I just get a white screen and nothing loads. After a short time, it just closes/crashes. Thanks for the reply."*  
   **Apple Reply** (`tweet_id: 1771`): *"@116102 Which model do you have and is iOS 11.1 installed on it? Any steps tried so far?"*
2. **Customer** (`tweet_id: 3764`):
   > *"not only does my phone keep freezing but when i screenshot things it turns out white... really not liking this iphone 8 plus @AppleSupport"*  
   **Apple Reply** (`tweet_id: 3762`): *"@116621 Let's look at this together. Are you updated to iOS 11.1?"*
3. **Customer** (`tweet_id: 3773`):
   > *"@AppleSupport iOS 11.1 - keyboard lag. 🤨 https://t.co/TdIHT9L9dt"*  
   **Apple Reply** (`tweet_id: 3772`): *"@116624 We'd like to take a look into that with you. Would you please join us in DM to get started? https://t.co/GDrqU22YpT"*
4. **Customer** (`tweet_id: 6928`):
   > *"@AppleSupport my iPhone is a fully up to date so why does my phone keep freezing 🙃???"*  
   **Apple Reply** (`tweet_id: 6927`): *"@117186 We want to help in any way we can. Which iPhone are you using? Let us know in DM, and we’ll work with you there. https://t.co/GDrqU22YpT"*
5. **Customer** (`tweet_id: 8299`):
   > *"@AppleSupport DL the latest iOS today. Very laggy 6s. Phone is running like hammered dog shit since the DL."*  
   **Apple Reply** (`tweet_id: 8298`): *"@117455 Are you seeing issues across all apps or are you noticing lag when performing specific tasks? Let us know in DM. https://t.co/GDrqU22YpT"*

---

### 6. `NETWORK_CONNECTIVITY`
* **Short Definition**: Inability to maintain Wi-Fi connection, Bluetooth pairing failures (AirPods, car audio, smart accessories), cellular signal loss ("No Service"), or AirDrop malfunctions.
* **What Belongs**:
  - Wi-Fi disconnecting, not discovering SSIDs, or grayed-out Wi-Fi toggle.
  - Bluetooth audio stuttering, pairing drops with AirPods, car kits, or Apple Watch.
  - Cellular connectivity dropping or persisting in "No Service" mode.
  - Personal Hotspot or AirDrop sharing failures.
* **What Does NOT Belong**:
  - Audio distortion due to blown speaker (assign to `AUDIO_SOUND_ISSUES`).
  - Safari browser crash while online (assign to `APP_CRASH_PERFORMANCE`).
* **Commonly Confused With**: `AUDIO_SOUND_ISSUES` (Bluetooth audio cuts vs speaker hardware), `SOFTWARE_UPDATE_OS`.
* **Why Useful for Support**: Clear step-by-step resolution path (*Settings > General > Reset > Reset Network Settings*).
* **Suggested Default Escalation**: `AUTO_HANDLE`.

#### 5 Verified Real Examples:
1. **Customer** (`tweet_id: 5849`):
   > *"I updated to iOS 11 and my iPhone 6 stopped connecting to wi-fi. Already restored the phone and the network connections @AppleSupport"*  
   **Apple Reply** (`tweet_id: 5847`): *"@117108 We are here to help. So we can best isolate the cause, could you verify your exact iOS version? https://t.co/ZTw54HL4Rm"*
2. **Customer** (`tweet_id: 25424`):
   > *"@applesupport Bluetooth connection iPhone X to Infiniti is terrible. Garbled and scratchy cutting in and out &gt;30% of time. Didn't happen W iPhone 6!!"*  
   **Apple Reply** (`tweet_id: 25422`): *"@121503 We want you to be able to enjoy your iPhone X with your Bluetooth devices. We'll do all we can to help. To start, what iOS version is currently installed? Does this issue occur with any other Bluetooth devices that you connect to?"*
3. **Customer** (`tweet_id: 27508`):
   > *"Unable to update apps when connected to WiFi. @AppleSupport"*  
   **Apple Reply** (`tweet_id: 27507`): *"@122018 Thanks for reaching out to us about this issue. We want your device to work for you and we'll be happy to help out. To get started, can you tell us which device and OS version you're having this problem with? Also, what happens when you try to update?"*
4. **Customer** (`tweet_id: 29549`):
   > *"@AppleSupport Sometimes they're connected, sometimes they're not. Sometimes it even says bluetooth not available in the bar on top yet one will be connected!? Started after I updated."*  
   **Apple Reply** (`tweet_id: 29548`): *"@122490 You mentioned the Bluetooth icon shows as not available sometimes. Is the Bluetooth icon grayed out at the top? When this occurs, are you able to toggle Bluetooth on and off via System Preferences? Let's dig into this deeper over DM: https://t.co/GDrqU22YpT"*
5. **Customer** (`tweet_id: 29553`):
   > *"Since the newest update my MAC won't stay connected to my mouse &amp; kb (bluetooth). Help @AppleSupport !?!"*  
   **Apple Reply** (`tweet_id: 29550`): *"@122490 We know how essential Bluetooth is to using wireless devices. We'll be happy to work with you to get to the bottom of this. To confirm, you updated to macOS 10.13.1, correct? Have you tried unpairing and repairing your Bluetooth devices?"*

---

### 7. `BILLING_SUBSCRIPTIONS`
* **Short Definition**: Inquiries regarding unexpected App Store / iTunes charges, subscription management/cancellations, refund requests for digital media, or payment method declines.
* **What Belongs**:
  - Overcharged or billed multiple times on iTunes / App Store.
  - Requesting refund for accidental app or in-app purchase.
  - Cancelling recurring Apple Music or third-party subscriptions.
  - Billing invoice / credit card charge disputes.
* **What Does NOT Belong**:
  - In-store repair quotes (assign to `HARDWARE_PHYSICAL_DAMAGE`).
  - Account disabled due to security/password (assign to `ACCOUNT_ACCESS_SECURITY`).
* **Commonly Confused With**: `ACCOUNT_ACCESS_SECURITY`.
* **Why Useful for Support**: Financial sensitivity requires structured deflection to `reportaproblem.apple.com` or specialized human billing advisors.
* **Suggested Default Escalation**: `ESCALATE`.

#### 5 Verified Real Examples:
1. **Customer** (`tweet_id: 23100`):
   > *"@AppleSupport, why do I keep getting charged over £20 for anything I buy from iTunes? Bought an album for £4.99 and got charged £20.67. Same thing happened a couple of weeks ago to. Why?! https://t.co/0fIDOKovNP"*  
   **Apple Reply** (`tweet_id: 23098`): *"@121031 Our iTunes Store team would be happy to look into this with you. Reach out to them here: https://t.co/SDIe7UiyJN"*
2. **Customer** (`tweet_id: 35262`):
   > *"@AppleSupport I got refunded for an in app purchase on Monday &amp; got a conformation email, but there’s no sign of it in my account yet..."*  
   **Apple Reply** (`tweet_id: 35260`): *"@123684 Hey there! Depending on your bank, it can take 3-5 business days to reflect in your account. We hope this helps."*
3. **Customer** (`tweet_id: 35976`):
   > *"@AppleSupport You guys over charged me on iTunes @AppleSupport and I want my money back I’m really upset"*  
   **Apple Reply** (`tweet_id: 35974`): *"@123826 We completely understand and want to help. Please reach out to our iTunes Support team directly here: https://t.co/SDIe7UiyJN"*
4. **Customer** (`tweet_id: 35979`):
   > *"@AppleSupport You guys over charged me on music I bought on iTunes and I want my money back I’m mad as hell"*  
   **Apple Reply** (`tweet_id: 38205`): *"@123826 We want to help. You can reach our iTunes support team here: https://t.co/SDIe7UiyJN"*
5. **Customer** (`tweet_id: 38869`):
   > *"@AppleSupport Already been told that nothing can be done cos I bought it via my design agency even though I have a receipt Your U.K. MD has avoided me."*  
   **Apple Reply** (`tweet_id: 38872`): *"@124482 We'd like to see if we can be of help. Would you mind joining us in DM? We'd like to continue our conversation there. https://t.co/GDrqU22YpT"*

---

### 8. `AUDIO_SOUND_ISSUES`
* **Short Definition**: Distorted speaker sound, crackling receivers, microphone not picking up voice during calls or Siri, low earpiece volume, or device stuck in headphone mode.
* **What Belongs**:
  - Callers cannot hear voice / microphone not working.
  - Earpiece volume too low to hear calls.
  - Speaker crackling, buzzing, or producing no sound.
  - iPhone stuck in "Headphones" mode with nothing plugged in.
* **What Does NOT Belong**:
  - Bluetooth car connection dropping (assign to `NETWORK_CONNECTIVITY`).
  - Physically crushed speaker grill (assign to `HARDWARE_PHYSICAL_DAMAGE`).
* **Commonly Confused With**: `NETWORK_CONNECTIVITY`, `HARDWARE_PHYSICAL_DAMAGE`.
* **Why Useful for Support**: Differentiates cleanable port issues / software glitches from hardware repairs.
* **Suggested Default Escalation**: `AUTO_HANDLE` (Provide audio troubleshooting steps).

#### 5 Verified Real Examples:
1. **Customer** (`tweet_id: 14326`):
   > *"Updated my phone last night &amp; now its stuck in headphone mode, cant hear anything on video, FaceTime &amp; call sound goes in&amp;out @AppleSupport"*  
   **Apple Reply** (`tweet_id: 14325`): *"@119051 We'd like to help. Let's take this to DM and we'll explore ways to provide you assistance. https://t.co/GDrqU22YpT"*
2. **Customer** (`tweet_id: 35281`):
   > *"@AppleSupport why is my alarm sound not working when on silent and volume on lock screen not working after the update??"*  
   **Apple Reply** (`tweet_id: 35280`): *"@123689 We're here for you. Does this happen when Do Not Disturb is enabled? Do newly created alarms have the same issue?"*
3. **Customer** (`tweet_id: 38882`):
   > *"@applesupport My iphone 6s hs crackling sound coming on call and whn I hold phn a little away from mouth, the person cannot hear my voice"*  
   **Apple Reply** (`tweet_id: 38881`): *"@124483 We're here to help! Which version of the iOS is on the iPhone and when did you first notice this issue?"*
4. **Customer** (`tweet_id: 39619`):
   > *"@AppleSupport since updating to 11.1 this am, sound volume on phone calls (handset) very quite - speaker and Bluetooth works fine - pls help"*  
   **Apple Reply** (`tweet_id: 39618`): *"@124664 We want to help with this. Do you experience the volume issue in all locations? Let us know in DM. https://t.co/GDrqU22YpT"*
5. **Customer** (`tweet_id: 40453`):
   > *"@AppleSupport My iPhone speaker doesnt work after ios 11.1 update"*  
   **Apple Reply** (`tweet_id: 40451`): *"@124866 That's definitely not expected behavior. Let's figure this out. Is this happening with all sounds? Have you restarted?"*

---

### 9. `ICLOUD_STORAGE_SYNC`
* **Short Definition**: System warnings regarding full iCloud storage, failed automated iCloud backups, missing photos after synchronization, or data restore errors.
* **What Belongs**:
  - "iCloud Storage is Full" warning alerts.
  - Failed overnight iCloud backups.
  - Photos, Notes, or Contacts failing to sync across devices.
  - Managing iCloud storage tiers.
* **What Does NOT Belong**:
  - Forgotten iCloud Apple ID password (assign to `ACCOUNT_ACCESS_SECURITY`).
  - Credit card declined for iCloud subscription (assign to `BILLING_SUBSCRIPTIONS`).
* **Commonly Confused With**: `ACCOUNT_ACCESS_SECURITY`, `BILLING_SUBSCRIPTIONS`.
* **Why Useful for Support**: Clear step-by-step guidance on managing storage breakdowns (*Settings > [Name] > iCloud > Manage Storage*).
* **Suggested Default Escalation**: `AUTO_HANDLE`.

#### 5 Verified Real Examples:
1. **Customer** (`tweet_id: 14313`):
   > *"Can’t share any photos from iCloud with iOS 11.1 @AppleSupport https://t.co/Ef0VgWX6US"*  
   **Apple Reply** (`tweet_id: 14312`): *"@119046 We'd like to help. Let's take this to DM and we'll explore ways to provide you assistance. https://t.co/GDrqU22YpT"*
2. **Customer** (`tweet_id: 31873`):
   > *"My iPhone just signed itself out of iCloud and I lost all of my synced contacts when I tried to sign back in. @AppleSupport"*  
   **Apple Reply** (`tweet_id: 31872`): *"@123041 Are these contacts on the iCloud website? Check here from a computer and let us know: https://t.co/tmRhWEkIq4"*
3. **Customer** (`tweet_id: 38885`):
   > *"@AppleSupport I'm using iCloud etc all of your shit but I cannot restore my data after a simple clean refresh. It seems I'm stupid :/"*  
   **Apple Reply** (`tweet_id: 38883`): *"@124484 Let us help. Follow up with us in DM. Tell us if the data is also missing from the iPhone 6 Activity App. https://t.co/GDrqU22YpT"*
4. **Customer** (`tweet_id: 42643`):
   > *"@AppleSupport Thank you. Twitter didn’t notify me of your reply :( so restored phone &amp; ok now. Was phone storage not iCloud."*  
   **Apple Reply** (`tweet_id: 42645`): *"@125426 We're glad to hear the issue has since been resolved. Let us know if you have any further questions..."*
5. **Customer** (`tweet_id: 48044`):
   > *"@AppleSupport Hi, I've just reset my phone and restored from icloud but none of my apps are downloading."*  
   **Apple Reply** (`tweet_id: 48042`): *"@126743 We are here to help you get your apps back. Are you connected to Wi-Fi? Did other things such as your Messages come back?"*

---

### 10. `GENERAL_PRODUCT_INQUIRY`
* **Short Definition**: General how-to questions, device compatibility, trade-in valuations, store hours, or general hardware specifications.
* **What Belongs**:
  - How to configure specific features (e.g. changing wallpaper, Do Not Disturb).
  - Apple trade-in program policies.
  - Accessory compatibility questions.
  - Apple Retail Store hours and locations.
* **What Does NOT Belong**:
  - Specific technical errors or hardware failures.
  - Screen repair appointment bookings (assign to `HARDWARE_PHYSICAL_DAMAGE`).
* **Commonly Confused With**: `SOFTWARE_UPDATE_OS`, `HARDWARE_PHYSICAL_DAMAGE`.
* **Why Useful for Support**: Direct link deflection to official Apple documentation.
* **Suggested Default Escalation**: `AUTO_HANDLE`.

#### 5 Verified Real Examples:
1. **Customer** (`tweet_id: 1759`):
   > *"Why is “I️” keep changing to this and how do I️ stop it🤦🏽‍♀️ @115858 @AppleSupport #anybody https://t.co/urzAfSZL5z"*  
   **Apple Reply** (`tweet_id: 1758`): *"@116098 We definitely understand your concern. Please backup your iPhone, update and let us know the result: https://t.co/ahjigcvFRG"*
2. **Customer** (`tweet_id: 1770`):
   > *"@AppleSupport why is my home sharing not working and how do i fix it"*  
   **Apple Reply** (`tweet_id: 1769`): *"@116101 We're happy to help. Has Home Sharing worked with these devices before?"*
3. **Customer** (`tweet_id: 2638`):
   > *"@AppleSupport ...cost for sending in for diagnosing a problem if it's out of warranty?"*  
   **Apple Reply** (`tweet_id: 2636`): *"@116340 We can help. Let’s start with the following steps to see if we can save you a trip in for service: https://t.co/RqWW0duJ0U"*
4. **Customer** (`tweet_id: 5819`):
   > *"@AppleSupport I can’t change lock screen anymore from ‘wallpaper’ in settings. How do I do it now?"*  
   **Apple Reply** (`tweet_id: 5817`): *"@117099 We'd be happy to help. Check out this link to for more information: https://t.co/hSnkM7JIIS"*
5. **Customer** (`tweet_id: 8308`):
   > *"@AppleSupport I don’t know. I need the space though. How do I get rid of some snapshots"*  
   **Apple Reply** (`tweet_id: 8307`): *"@117459 Finder and Get Info windows don't include snapshots in their calculations so that's not the root cause. Let's meet within DM: https://t.co/GDrqU22YpT"*

---

## 3. Special Case Analysis & Edge Cases

### A. Intent Distribution Summary
```
SOFTWARE_UPDATE_OS       [████████████████████████████] 27.84% (29,695)
BATTERY_PERFORMANCE      [██████████]                   9.60%  (10,243)
APP_CRASH_PERFORMANCE    [███]                          2.78%  (2,962)
NETWORK_CONNECTIVITY     [██]                           2.21%  (2,362)
GENERAL_PRODUCT_INQUIRY  [██]                           2.19%  (2,336)
BILLING_SUBSCRIPTIONS    [██]                           1.79%  (1,904)
HARDWARE_PHYSICAL_DAMAGE [█]                            1.40%  (1,489)
ACCOUNT_ACCESS_SECURITY  [█]                            1.25%  (1,337)
AUDIO_SOUND_ISSUES       [█]                            1.13%  (1,210)
ICLOUD_STORAGE_SYNC      [ ]                            0.52%  (558)
Unclassified / Media     [█████████████████████████████████████████████████] 49.28%
```

---

### B. Examples of Ambiguous Messages
These messages lack sufficient semantic tokens to determine intent with certainty:

1. **`tweet_id: 698`**:
   > *"@AppleSupport https://t.co/NV0yucs0lB"*  
   *Ambiguity Root Cause*: Pure image link with zero text. Requires multimodal vision or a clarification response.
2. **`tweet_id: 2618`**:
   > *"@AppleSupport Tried resetting my settings .. restarting my phone .. all that"*  
   *Ambiguity Root Cause*: Mid-thread follow-up describing actions taken without stating the underlying defect.
3. **`tweet_id: 112845`**:
   > *"@AppleSupport This is what it looks like https://t.co/XCQU2l4xUB"*  
   *Ambiguity Root Cause*: Deictic reference to an external image attachment.
4. **`tweet_id: 143570`**:
   > *"@AppleSupport why does this keep happening"*  
   *Ambiguity Root Cause*: Context-free complaint lacking product, feature, or symptom keywords.

---

### C. Examples of Multi-Intent Messages
These messages span two or more distinct intent categories:

1. **`tweet_id: 745`**:
   > *"@AppleSupport I need the software update urgently. The battery lasts literally half a day 🙍🏼🙁@AppleSupport"*  
   *Overlapping Intents*: `SOFTWARE_UPDATE_OS` + `BATTERY_PERFORMANCE`.  
   *Disambiguation Rule*: Primary intent is `BATTERY_PERFORMANCE` (the core customer symptom), while software update is the user's presumed remedy.
2. **`tweet_id: 42656`**:
   > *"@AppleSupport Hey Apple! Having issues with my ID and already changed my password. Trying to update my computer but says ID is disabled?"*  
   *Overlapping Intents*: `ACCOUNT_ACCESS_SECURITY` + `SOFTWARE_UPDATE_OS`.  
   *Disambiguation Rule*: Primary intent is `ACCOUNT_ACCESS_SECURITY` (the blocking error is a disabled Apple ID).
3. **`tweet_id: 5849`**:
   > *"I updated to iOS 11 and my iPhone 6 stopped connecting to wi-fi. Already restored the phone and the network connections @AppleSupport"*  
   *Overlapping Intents*: `SOFTWARE_UPDATE_OS` + `NETWORK_CONNECTIVITY`.  
   *Disambiguation Rule*: Primary intent is `NETWORK_CONNECTIVITY` (specific failing subsystem).

---

### D. Examples Requiring Customer / Account-Specific Information
These messages cannot be resolved by generic troubleshooting and require private human handoff (`ESCALATE`):

1. **`tweet_id: 112824`**:
   > *"@AppleSupport My phone got stolen but i can't change my apple id password because of the 2 step verification that requires my phone! Do you have a uk based email that i can contact about this?"*  
   *Escalation Reason*: Stolen device + locked 2FA recovery requiring account security verification.
2. **`tweet_id: 23100`**:
   > *"@AppleSupport, why do I keep getting charged over £20 for anything I buy from iTunes? Bought an album for £4.99 and got charged £20.67. Same thing happened a couple of weeks ago to. Why?! https://t.co/0fIDOKovNP"*  
   *Escalation Reason*: Financial charge investigation requiring private billing record inspection.
3. **`tweet_id: 156039`**:
   > *"@AppleSupport Your Apple ID has been disabled.... That's all it says. Thanks @AppleSupport"*  
   *Escalation Reason*: Security lockout on Apple backend; requires identity verification.

---

### E. Examples Where Historical Responses Provide Useful Resolution Guidance
These show high-quality historical grounding suitable for RAG demonstrations:

1. **Customer** (`tweet_id: 44626`): *"@AppleSupport help I logged out of my Apple ID account and the verification code is sent to a broken phone????"*  
   **Apple Reply** (`tweet_id: 44624`): *"@125905 We can assist you. You can change a trusted device if you are using two-factor authentication: https://t.co/RONuUjClwW"*  
   *Why Useful*: Provides direct, authoritative Apple Support KB link for 2FA trusted device management.
2. **Customer** (`tweet_id: 31873`): *"My iPhone just signed itself out of iCloud and I lost all of my synced contacts when I tried to sign back in. @AppleSupport"*  
   **Apple Reply** (`tweet_id: 31872`): *"@123041 Are these contacts on the iCloud website? Check here from a computer and let us know: https://t.co/tmRhWEkIq4"*  
   *Why Useful*: Provides diagnostic verification step (checking iCloud web interface) to isolate cloud vs local corruption.
3. **Customer** (`tweet_id: 5819`): *"@AppleSupport I can’t change lock screen anymore from ‘wallpaper’ in settings. How do I do it now?"*  
   **Apple Reply** (`tweet_id: 5817`): *"@117099 We'd be happy to help. Check out this link to for more information: https://t.co/hSnkM7JIIS"*  
   *Why Useful*: Direct feature documentation link.

---

### F. Examples Where Historical Responses Are Poor / Noisy
These historical responses exhibit premature deflection or lack substantive value and must NOT be blindly copied:

1. **Customer** (`tweet_id: 1775`): *"@AppleSupport @116102 Battery life just got worst."*  
   **Apple Reply** (`tweet_id: 1777`): *"@116103 We'll make sure to get this straightened out. DM us, and we'll see you there. https://t.co/GDrqU22YpT"*  
   *Why Noisy*: Pure canned deflection to DM without asking device model or providing basic battery tips.
2. **Customer** (`tweet_id: 94891`): *"I got my phone fixed 2 weeks ago and I just dropped my phone with a case on it ON CARPET from at MOST four feet, and my screen shattered.... @AppleSupport how?"*  
   **Apple Reply** (`tweet_id: 94890`): *"@136626 We're sorry that this happened, so let us help you get it taken care of. DM us so we can better assist you: https://t.co/GDrqU22YpT"*  
   *Why Noisy*: Generic boilerplate without acknowledging warranty repair context or AppleCare terms.
3. **Customer** (`tweet_id: 35979`): *"@AppleSupport You guys over charged me on music I bought on iTunes and I want my money back I’m mad as hell"*  
   **Apple Reply** (`tweet_id: 38205`): *"@123826 We want to help. You can reach our iTunes support team here: https://t.co/SDIe7UiyJN"*  
   *Why Noisy*: Blunt link dump without empathetic acknowledgement or instructions on navigating the link.

---

*Taxonomy derived and documented in `docs/intent-taxonomy.md`.*
