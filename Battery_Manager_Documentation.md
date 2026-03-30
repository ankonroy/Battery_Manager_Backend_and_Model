# Battery Manager — Complete Project Documentation
### Version 1.0 | For Briefing AI Assistants and Human Collaborators

---

## DOCUMENT PURPOSE

This document is a complete technical and conceptual briefing of the Battery Manager Android app and its planned AI/ML backend extension. It is written so that any developer, AI assistant, or collaborator can pick up this project at any point and understand:

- What the app does and why
- How every file, class, and function is structured
- How data flows through the system
- How battery health is calculated (full algorithm walkthrough)
- What the planned AI/ML backend looks like and why those design decisions were made
- What datasets to use and where to get them
- The full technology stack and build roadmap

**The app repository:** `Battery_Manager-main` (Flutter + Kotlin, Android-only)
**Current state:** Core app is complete and functional. AI/ML backend is in the planning phase — no backend code written yet.
**Primary developer of existing app:** Friend/collaborator (original author)
**Person continuing development:** You (the reader), who is relatively new to Dart/Flutter

---

## TABLE OF CONTENTS

1. Project Overview
2. Technology Stack (Existing App)
3. Project Folder Structure
4. Architecture: Two-Layer System
5. Android / Kotlin Layer — Native Files
6. Dart / Flutter Layer — Complete File Reference
   - 6.1 Entry Point: main.dart
   - 6.2 Theme: app_theme.dart
   - 6.3 Models (7 files)
   - 6.4 RealBatteryService — Full Function Reference
   - 6.5 HomeScreen — UI and 6 Tabs
   - 6.6 Widgets (6 files)
7. Data Flow: End-to-End Walkthrough
8. The 8 Streams System
9. Battery Health Calculation — Full Algorithm
10. Key Dart/Flutter Concepts (For Newcomers)
11. Planned AI/ML Backend — Full Design
    - 11.1 Why AI/ML and Which Problems It Solves
    - 11.2 The Four ML Features
    - 11.3 Training Datasets
    - 11.4 Data the App Sends to the Backend
    - 11.5 Backend Response Contract
    - 11.6 Backend Architecture
    - 11.7 Technology Stack (Backend)
    - 11.8 Privacy Design
    - 11.9 Build Roadmap
12. Open Questions and Future Considerations

---

## 1. PROJECT OVERVIEW

### What the App Is

**Battery Manager** (package name: `com.example.battery_analyzer`, app name: "Battery Analyzer Pro") is an Android smartphone application built with Flutter and Dart. It monitors, analyzes, and helps users optimize their phone's battery health and longevity.

### What Problem It Solves

Android's built-in battery information is extremely limited for end users. The operating system provides a charge percentage and a vague "Good/Overheat" status, but does not expose:
- The battery's actual current capacity (vs. its original factory capacity)
- A real health percentage showing degradation over time
- How many charge cycles remain before the battery needs replacement
- Which apps are draining the most power (in mAh, not just vague rankings)
- Personalized advice based on your specific charging habits

This app fills all of those gaps by reading the raw hardware signals Android does expose (voltage, current, temperature, charge counter) and computing everything else from first principles.

### Six Core Features

1. **Live Monitoring** — Reads voltage, current (mA), temperature (°C), and charge level every second via Android's BatteryManager API.
2. **Health Estimation** — Learns the battery's real current capacity (mAh) over days of use by analyzing charging sessions, then computes health as a percentage vs. the original design capacity.
3. **Stress Scoring** — A 0–100 score showing how hard you are pushing the battery right now (heat, high voltage, fast charging). Separate from health — health is cumulative damage, stress is current rate of damage.
4. **App Drain Tracking** — Estimates which apps are consuming the most battery (mAh) by attributing drain to whichever app is in the foreground during discharge.
5. **Cycle Counting** — Counts full charge cycles (one cycle = one full design capacity worth of discharge). Most batteries are rated for 300–500 cycles.
6. **Battery-Saving Actions** — Direct actions the app can take: reduce brightness, shorten screen timeout, open Android Battery Saver, enable Ultra Battery Saver, force-stop specific apps.

### Architectural Philosophy

The app is designed with a **local-first** philosophy. Every feature works entirely offline with no server required. All data is stored on the device. The AI/ML backend (planned) adds an intelligence layer on top — it does not replace any existing functionality and the app degrades gracefully if the backend is unavailable.

---

## 2. TECHNOLOGY STACK (EXISTING APP)

| Layer | Technology | Purpose |
|---|---|---|
| UI framework | Flutter (Dart) | Cross-platform UI — though only Android is targeted |
| App language | Dart 3.x (SDK >=3.0.0 <4.0.0) | All UI, logic, and calculations |
| Native bridge | Kotlin | Direct access to Android hardware APIs |
| Local storage | SharedPreferences | Persists: capacity samples, cycle count, manual design capacity |
| Date/number formatting | intl ^0.18.0 | Formatting timestamps and numbers in the UI |
| Persistence package | shared_preferences ^2.2.3 | Key-value storage on the device |
| Minimum Android | Not specified, but uses APIs requiring Android 6+ | AccessibilityService, UsageStatsManager |

---

## 3. PROJECT FOLDER STRUCTURE

```
Battery_Manager-main/
├── lib/                                  ← All Dart/Flutter code
│   ├── main.dart                         ← Entry point — creates the app
│   ├── screens/
│   │   └── home_screen.dart              ← The entire UI (1,917 lines) — 6 tabs
│   ├── utils/
│   │   └── real_battery_service.dart     ← The brain — all logic (~1,000 lines)
│   ├── models/
│   │   ├── battery_data.dart             ← Master data snapshot class
│   │   ├── battery_history.dart          ← Per-second reading
│   │   ├── app_battery_usage.dart        ← Per-app drain estimate
│   │   ├── battery_alert.dart            ← Notification/alert item
│   │   ├── battery_achievement.dart      ← Gamification: achievements + streaks
│   │   ├── daily_battery_stats.dart      ← Aggregated daily statistics
│   │   └── capacity_sample.dart          ← Single capacity measurement
│   ├── widgets/
│   │   ├── stat_card.dart                ← Metric tile (icon + title + value)
│   │   ├── status_indicator.dart         ← Charging/discharging status row
│   │   ├── history_panel.dart            ← Scrollable history list
│   │   ├── log_panel.dart                ← Scrollable event log list
│   │   ├── frosted_panel.dart            ← Glass-effect container widget
│   │   └── line_chart.dart               ← Custom painted line/area chart
│   └── theme/
│       └── app_theme.dart                ← Light and dark Material 3 themes
│
├── android/                              ← All Kotlin/Android native code
│   └── app/src/main/kotlin/com/example/battery_analyzer/
│       ├── MainActivity.kt               ← MethodChannel + EventChannel hub (~560 lines)
│       ├── BatteryMonitoringService.kt   ← Background foreground service
│       ├── BatteryOverlayService.kt      ← Floating overlay on other apps
│       ├── AppForceStopAccessibilityService.kt  ← Auto-taps Force Stop button
│       ├── BootReceiver.kt               ← Restarts service after phone reboot
│       ├── ForceStopAutomationStore.kt   ← Stores force-stop accessibility state
│       └── OverlaySettingsStore.kt       ← Stores overlay permission state
│
├── pubspec.yaml                          ← Dependencies and app metadata
├── pubspec.lock                          ← Locked dependency versions
├── analysis_options.yaml                 ← Dart linter configuration
└── test/
    └── widget_test.dart                  ← Basic widget test (minimal)
```

---

## 4. ARCHITECTURE: TWO-LAYER SYSTEM

The app has two completely separate worlds that communicate with each other.

### Layer 1: Flutter / Dart (The UI and Brain)

Everything the user sees and all the calculations happen here. Dart cannot access Android hardware APIs directly — it is sandboxed.

Files: `main.dart`, `home_screen.dart`, `real_battery_service.dart`, all models, all widgets, `app_theme.dart`

### Layer 2: Android / Kotlin (The Hardware Bridge)

Kotlin has direct access to Android's APIs — BatteryManager, UsageStatsManager, PowerManager, Settings, etc. It acts as a bridge, performing operations on behalf of Dart and sending results back.

Files: All `.kt` files in the `android/` folder

### The Communication Channels

Two Flutter platform channels connect the two layers:

**MethodChannel** — `com.example.battery_analyzer/battery`
- Request/response style. Dart calls a named method, Kotlin executes it, returns a result.
- Used for: `getBatteryInfo`, `requestPermissions`, `hasUsageAccess`, `reduceSystemBrightness`, `requestAppForceStop`, `startBackgroundService`, etc.

**EventChannel** — `com.example.battery_analyzer/battery_events`
- Push style. Kotlin broadcasts data to Dart whenever something changes.
- Used for: Receiving `ACTION_BATTERY_CHANGED` broadcasts instantly when the user plugs in or unplugs the charger.
- This means the UI responds immediately to plug events rather than waiting for the next 1-second timer tick.

### Analogy

Think of the app like a restaurant. The Kotlin layer is the **kitchen** — it has the actual tools and ingredients (Android APIs). The Dart layer is the **dining room** — it's what the customer (user) sees. The MethodChannel and EventChannel are the **waiters** — passing orders one way and food the other.

---

## 5. ANDROID / KOTLIN LAYER — NATIVE FILES

### MainActivity.kt (~560 lines)
The central Kotlin file. It:
- Sets up both the MethodChannel and EventChannel
- Implements a handler for every method call from Dart
- Reads battery data from Android's `BatteryManager` API
- Queries `UsageStatsManager` for foreground app information
- Opens Android system settings screens on demand
- Controls brightness and screen timeout (requires WRITE_SETTINGS permission)
- Manages the background service lifecycle

Key method calls handled:
| Method name | What it does |
|---|---|
| `getBatteryInfo` | Returns a Map with all battery fields |
| `requestPermissions` | Requests POST_NOTIFICATIONS permission |
| `hasUsageAccess` | Checks if Usage Access permission is granted |
| `isBatterySaverEnabled` | Checks if Android Battery Saver is on |
| `isSystemWriteAccessGranted` | Checks WRITE_SETTINGS permission |
| `reduceSystemBrightness` | Lowers screen brightness |
| `shortenScreenTimeout` | Reduces screen-off timeout |
| `requestAppForceStop` | Navigates to App Info and auto-taps Force Stop |
| `startBackgroundService` | Starts BatteryMonitoringService |
| `stopBackgroundService` | Stops BatteryMonitoringService |
| `isBackgroundServiceRunning` | Returns true/false |
| `openUsageAccessSettings` | Launches Android Usage Access settings |
| `openBatterySaverSettings` | Launches Battery Saver settings |
| `openSystemWriteSettings` | Launches Write Settings permission screen |
| `openDisplaySettings` | Launches Display settings |
| `openUltraBatterySaverSettings` | Launches OEM ultra power mode screen |
| `openForceStopAccessibilitySettings` | Launches Accessibility settings |

**Raw battery data Map returned by `getBatteryInfo`:**
```
level, scale, isPlugged, status, health, temperature, voltage, technology,
current, chargeCounter, designCapacity, fullChargeCapacity,
remainingCapacityFromEnergy, manufacturer, brand, model, device,
foregroundPackage, foregroundApp
```

Note: `temperature` is in tenths of degrees Celsius (295 = 29.5°C). `voltage` is in millivolts (3842 = 3.842V). `current` is in microamps (some phones) or milliamps (other phones).

### BatteryMonitoringService.kt
An Android **foreground service** — a service that keeps running even when the app is in the background, shown to the user via a persistent notification. This is how the app continues monitoring after you minimize it. It also triggers the "unplug at 80%" reminder notification when the battery reaches 80% while charging.

### BatteryOverlayService.kt
Draws a floating overlay window on top of all other apps (requires "Display over other apps" permission). Shows live battery information without the user needing to open the app.

### AppForceStopAccessibilityService.kt
An Android **Accessibility Service** — a special service that can observe and interact with the UI of other apps. When the user requests to force-stop an app, this service navigates to that app's "App Info" screen in Android Settings and programmatically taps the "Force Stop" button. This automation requires the user to enable the Accessibility Service in Android Settings.

### BootReceiver.kt
A **BroadcastReceiver** that listens for the `ACTION_BOOT_COMPLETED` broadcast from Android. When the phone restarts, Android fires this broadcast and the receiver automatically restarts the `BatteryMonitoringService`, so monitoring resumes without the user having to open the app.

### ForceStopAutomationStore.kt / OverlaySettingsStore.kt
Small utility classes that persist the state of the accessibility service and overlay permissions using Android's SharedPreferences. Used by the rest of the Kotlin code to check whether these permissions are currently enabled.

---

## 6. DART / FLUTTER LAYER — COMPLETE FILE REFERENCE

### 6.1 Entry Point: main.dart (30 lines)

The first file that runs. Creates `BatteryAnalyzerApp`, a `StatefulWidget` (a UI component that can hold changing state). 

State it holds:
- `_themeMode` — current theme (system/light/dark), stored here at the top level so it persists across tab changes

What it creates:
- A `MaterialApp` with both light and dark themes defined by `AppTheme`
- `HomeScreen` as the root screen, passing the current theme mode and a callback (`_onThemeModeChanged`) so HomeScreen can change the theme

**Key concept:** The theme mode is stored at the top of the widget tree so a change in any nested widget propagates to the entire app.

---

### 6.2 Theme: app_theme.dart

Defines `AppTheme` — a static class with two `ThemeData` objects (light and dark), both built by the same `_buildTheme()` method.

Seed color: `0xFF0F766E` (a dark teal)

What it customizes:
- `scaffoldBackgroundColor` — page background (very dark in dark mode: `0xFF0F1415`)
- `cardTheme` — rounded corners (18px radius), subtle elevation
- `appBarTheme` — transparent background, no elevation
- `textTheme` — 6 text styles: `headlineMedium`, `titleLarge`, `titleMedium`, `bodyLarge`, `bodyMedium`, `labelLarge`
- Uses Material 3 (`useMaterial3: true`) with `ColorScheme.fromSeed()` for automatic color derivation

**Note for future development:** All colors throughout the app derive from this seed color via Material 3's color system. To change the color scheme, change `_seed` in this file.

---

### 6.3 Models (7 Files)

Models are plain Dart classes — they hold data and have no logic. They are immutable (all fields are `final`), support `copyWith()` for creating modified copies, and most support `toJson()`/`fromJson()` for persistence.

#### BatteryData (battery_data.dart) — THE most important model
A complete snapshot of everything about the battery at one moment in time. Created fresh every second by `RealBatteryService` and broadcast to the UI.

Full field list:
| Field | Type | Description |
|---|---|---|
| `level` | `int` | Battery percentage (0–100) |
| `temperature` | `double` | Temperature in °C (already converted from raw tenths) |
| `voltage` | `double` | Voltage in V (already converted from millivolts) |
| `health` | `String` | "Excellent" / "Good" / "Fair" / "Aging" / "Weak" / "Overheat" / "Dead" / etc. |
| `technology` | `String` | Battery chemistry, e.g. "Li-ion" |
| `capacity` | `int` | Remaining mAh (estimated, not from hardware directly) |
| `current` | `int` | Current flow in mA (positive = charging, negative = discharging) |
| `isCharging` | `bool` | True if plugged in |
| `chargingRate` | `double` | Charge current in mA (0 when discharging) |
| `dischargingRate` | `double` | Discharge current in mA (0 when charging) |
| `cycleCount` | `int` | Estimated full charge cycles accumulated |
| `estimatedCapacity` | `double` | Same as actualCapacity — full capacity estimate in mAh |
| `timestamp` | `DateTime` | When this snapshot was created |
| `chargingTime` | `Duration` | Total time spent charging since monitoring started |
| `dischargingTime` | `Duration` | Total time spent discharging since monitoring started |
| `healthPercentage` | `double` | 0–100, the computed health % |
| `actualCapacity` | `double` | Smoothed estimated full capacity in mAh |
| `designCapacity` | `int` | Original factory capacity in mAh |
| `chargedSinceStart` | `double` | Total mAh charged since monitoring started |
| `dischargedSinceStart` | `double` | Total mAh discharged since monitoring started |
| `netMahSinceStart` | `double` | chargedSinceStart - dischargedSinceStart |
| `averagePowerMw` | `double` | Current power draw in mW (current × voltage) |
| `stressScore` | `double` | 0–100 battery stress score |
| `projectedTimeToFullHours` | `double` | Hours until 100% at current charge rate |
| `projectedTimeToEmptyHours` | `double` | Hours until 0% at current drain rate |
| `manufacturer` | `String` | e.g. "Samsung" |
| `brand` | `String` | e.g. "samsung" |
| `model` | `String` | e.g. "SM-G991B" |
| `device` | `String` | Board/device name |
| `isDesignCapacityManual` | `bool` | True if user manually set the design capacity |
| `manualDesignCapacity` | `int?` | The manually set value, or null |
| `capacitySampleCount` | `int` | Total valid charging sessions collected |
| `confidencePercentage` | `double` | 0–100, confidence in the health estimate |

Special methods:
- `BatteryData.empty()` — factory constructor returning zeroed-out placeholder, used at startup
- `copyWith(...)` — returns a new BatteryData with only specified fields changed (required because all fields are `final`)

#### BatteryHistory (battery_history.dart)
Lightweight entry stored every second in the rolling 360-entry list.
Fields: `current` (mA), `level` (%), `isCharging` (bool), `timestamp` (DateTime)
Computed getters: `formattedTime` (HH:MM:SS string), `currentFormatted` ("+500 mA" / "-300 mA")

#### AppBatteryUsage (app_battery_usage.dart)
Tracks battery drain attribution per app.
Fields: `packageName`, `appName`, `foregroundMah`, `backgroundMah`, `lastUpdated`
Computed getter: `totalMah` = foregroundMah + backgroundMah

#### BatteryAlert (battery_alert.dart)
A notification/alert item with severity levels.
Fields: `id`, `title`, `message`, `severity` (enum: info/warning/critical), `timestamp`, `acknowledged`
Has `toJson()` and `fromJson()` for persistence.
The `BatteryAlertSeverity` enum is defined in this same file.

#### BatteryAchievement + BatteryStreak (battery_achievement.dart)
Gamification classes for the achievements system.
`BatteryAchievement` fields: `id`, `title`, `description`, `target` (int), `progress` (int), `earnedAt` (DateTime?)
`BatteryStreak` fields: `current` (days), `best` (days), `lastGoodDay` (DateTime?)
Both support `toJson()` / `fromJson()` and `copyWith()`.

#### DailyBatteryStats (daily_battery_stats.dart)
Aggregated statistics for a single calendar day.
Fields: `date`, `dischargedMah`, `chargedMah`, `avgDischargeRate`, `avgChargeRate`, `avgTemp`, `maxTemp`, `minTemp`, `minLevel`, `maxLevel`, `avgHealth`, `avgStress`, `samples` (count of readings that day)
Has `toJson()` / `fromJson()`.

#### CapacitySample (capacity_sample.dart)
A single capacity measurement from one charging session.
Fields: `timestamp` (DateTime), `capacityMah` (double)
Has `toJson()` / `fromJson()`.
These are the data points that feed the health estimation algorithm.

---

### 6.4 RealBatteryService — Full Function Reference

**File:** `lib/utils/real_battery_service.dart` (~1,000 lines)
**What it is:** The entire intelligence of the app. A Dart class that manages battery monitoring, runs all calculations, and broadcasts results through 8 streams. HomeScreen creates one instance of this class and uses it throughout its lifetime.

#### Communication Channels Declared Here

```dart
static const MethodChannel _platform =
    MethodChannel('com.example.battery_analyzer/battery');
static const EventChannel _eventChannel =
    EventChannel('com.example.battery_analyzer/battery_events');
```

#### The 8 StreamControllers (private) and Their Public Streams

| StreamController | Public Stream | Type | What it carries |
|---|---|---|---|
| `_batteryDataController` | `batteryDataStream` | `Stream<BatteryData>` | Full snapshot every second |
| `_historyController` | `historyStream` | `Stream<List<BatteryHistory>>` | Rolling 360-entry list |
| `_logController` | `logStream` | `Stream<List<String>>` | Last 150 timestamped log messages |
| `_appUsageController` | `appUsageStream` | `Stream<List<AppBatteryUsage>>` | Apps sorted by mAh drain |
| `_usageAccessController` | `usageAccessStream` | `Stream<bool>` | Usage Access permission status |
| `_forceStopAutomationController` | `forceStopAutomationStream` | `Stream<bool>` | Accessibility service enabled? |
| `_batterySaverController` | `batterySaverStream` | `Stream<bool>` | Battery Saver enabled? |
| `_systemWriteAccessController` | `systemWriteAccessStream` | `Stream<bool>` | Write Settings permission? |

#### Key Configuration Constants

```
_updateInterval = 1 second         ← Timer polling interval
_maxHistory = 360                   ← Max history entries kept in memory
_maxLogs = 150                      ← Max log messages kept
_maxCapacitySamples = 120           ← Max session estimates in sample pool
_highConfidenceSampleTarget = 80    ← Sessions needed for full confidence
_minSessionSocDeltaPercent = 10     ← Minimum SoC change to use a session
_fallbackSessionSocDeltaPercent = 15 ← Minimum when no charge counter available
_maxSamplingSocPercent = 85         ← Don't sample sessions that go above 85%
_minSamplingTemperatureC = 15.0     ← Too cold to trust current readings
_maxSamplingTemperatureC = 42.0     ← Too hot — thermal throttling affects readings
_maxSessionCurrentCoefficientOfVariation = 0.35 ← Current must be stable
_minChargeCounterCoverage = 0.60    ← 60% of readings must use charge counter
_minimumSamplesForOutlierFilter = 8 ← Need 8+ samples before filtering outliers
_maxSampleDeviationFromMedian = 0.18 ← Reject if >18% from median
_healthTrustConfidenceFloor = 0.45  ← Don't trust health below 45% confidence
_foregroundAttributionShare = 0.82  ← 82% of drain goes to foreground app
```

#### ALL FUNCTIONS — Complete Reference

**LIFECYCLE FUNCTIONS**

`RealBatteryService()` — Constructor
- Called once when HomeScreen initializes
- Immediately calls `_loadPreferences()` (async, runs in background)
- Immediately calls `_initializeData()` (pushes empty data to all streams)

`startMonitoring()` — async, public
- The "start button" for all monitoring
- Awaits preferences to finish loading first
- Calls `refreshAccessStatuses()` to check all 4 permissions
- Requests notification permission from Android via MethodChannel
- Calls `startBackgroundService` via MethodChannel (allows monitoring when app is minimized)
- Calls `_listenToBatteryEvents()` to subscribe to instant plug/unplug events
- Starts `Timer.periodic(_updateInterval, ...)` which calls `_fetchBatteryData()` every second
- Called automatically at app startup by `_bootstrapMonitoring()` in HomeScreen

`stopMonitoring()` — async, public
- Cancels the 1-second timer
- Cancels the EventChannel subscription
- Calls `stopBackgroundService` via MethodChannel
- Adds "Monitoring stopped" to log

`_initializeData()` — private
- Pushes empty/false placeholder values to all 8 streams
- Prevents UI from crashing while waiting for real data at startup
- Creates a `BatteryData.empty()` object and broadcasts it

`_loadPreferences()` — async, private
- Reads from device's SharedPreferences storage
- Restores: `_manualDesignCapacityMah`, `_capacitySamples` list, `_capacitySampleCount`, `_cycleCount`, `_throughputMahForCycle`, `_usageAccessHintShown`
- Validates loaded values (e.g. manual capacity must be 800–15,000 mAh)
- Recomputes smoothed capacity from loaded samples
- Logs what was restored

`clearData()` — public
- Resets: history list, app usage map, capacity samples, EWMA averages, session tracking, charging/discharging time totals
- Intentionally PRESERVES cycle count (physical property, shouldn't be erased)
- Removes capacity samples from SharedPreferences
- Called from the UI when user taps "Reset samples" in the menu

`dispose()` — public
- Called by Flutter when HomeScreen is removed from the widget tree
- Cancels timer, cancels EventChannel subscription
- Closes all 8 StreamControllers (prevents memory leaks)

---

**DATA FETCHING FUNCTIONS**

`_fetchBatteryData()` — async, private
- Called every second by the timer
- Sends `getBatteryInfo` MethodChannel call to Kotlin
- Receives a raw `Map<String, dynamic>` back
- Passes the map to `_processBatteryData()`

`_listenToBatteryEvents()` — private
- Subscribes to the EventChannel's broadcast stream
- Receives data when Android fires `ACTION_BATTERY_CHANGED` (plug/unplug events)
- Also passes received maps to `_processBatteryData()`
- Cancels any existing subscription before creating a new one

`_processBatteryData(Map<String, dynamic> data)` — private — THE MOST IMPORTANT FUNCTION
- Orchestrates everything. Called by both the timer and the EventChannel listener.
- Step by step:
  1. Parses raw values using `_toInt()`, `_toDouble()`, `_cleanString()` helpers
  2. Converts temperature (÷10), voltage (÷1000), current (÷1000 for microamps)
  3. Updates device info fields (manufacturer, brand, model, device)
  4. Calls `_tryUpdateDetectedDesignCapacity()` to update the known design capacity
  5. Calls `_updatePhaseDurations()` to track charging vs discharging time
  6. Calculates elapsed seconds since last sample via `_resolveElapsedSeconds()`
  7. Calls `_integrateCharge()` to compute mAh transferred this tick
  8. Calls `_updateAppUsageAttribution()` to credit drain to foreground app
  9. Calls `_updateCycleCount()` to accumulate cycle data
  10. Calls `_updateSignalAverages()` to update EWMA smoothed signals
  11. Calls `_updateStressExposure()` to accumulate long-term stress scores
  12. Calls `_calculateStressScore()` to compute the current stress number
  13. Calls `_calculateHealthConfidence()` to compute confidence %
  14. Calls `_calculateHealthPercentage()` to compute health %
  15. Calls `_getHealthString()` to get the text label
  16. Computes projected time to full/empty
  17. Assembles all values into a new `BatteryData` object
  18. Broadcasts via `_batteryDataController.add(batteryData)`
  19. Calls `_addToHistory(batteryData)`
  20. Updates `_lastSampleTime = now`

`_addToHistory(BatteryData data)` — private
- Creates a lightweight `BatteryHistory` entry from the full BatteryData
- Appends to the `_history` list
- Removes the oldest entry if list exceeds 360 entries
- Broadcasts updated list via `_historyController.add(...)`

`_addLog(String message)` — private
- Prepends a timestamped message to the `_logs` list (newest first)
- Format: `"HH:MM:SS  message text"`
- Trims list to 150 entries
- Broadcasts via `_logController.add(...)`

---

**DESIGN CAPACITY DETECTION FUNCTIONS**

`_tryUpdateDetectedDesignCapacity(data, levelPercent)` — private
- Called every tick. Tries multiple Android fields to find the design capacity, in priority order:
  1. `designCapacity` field (most phones don't expose this)
  2. `fullChargeCapacity` field
  3. `chargeCounter` + SoC estimate (`_estimateFromChargeCounterAndSoc`)
  4. Raw `chargeCounter` parsing (`_parseChargeCounter`)
  5. `remainingCapacityFromEnergy` + SoC (`_estimateFromEnergyAndSoc`)
- Accepts the first valid candidate in range 1,000–30,000 mAh
- Logs when a new capacity is detected

`_parseCapacityField(rawValue)` — returns `int?`
- Validates a capacity field value: must be between 1,000 and 30,000 mAh

`_parseChargeCounter(rawValue)` — returns `int?`
- Handles the inconsistency: some phones report charge counter in µAh (>30,000), others in mAh
- Divides by 1,000 if the value suggests µAh units

`_estimateFromChargeCounterAndSoc(rawChargeCounter, soc)` — returns `int?`
- If charge counter shows remaining mAh and SoC% is known: `estimate = remaining / (soc/100)`

`_estimateFromEnergyAndSoc(rawRemainingFromEnergy, soc)` — returns `int?`
- Same logic as above but using the energy remaining field

---

**CHARGE INTEGRATION FUNCTIONS**

`_integrateCharge(currentMagnitudeMah, isCharging, levelPercent, chargeCounterMah, elapsedSeconds, currentMa, temperatureC)` — returns `double`
- Called every tick. Computes how many mAh were charged or discharged since the last tick.
- Prefers using the hardware charge counter delta (more accurate) over current × time
- Calls `_consumeChargeCounterDelta()` to get the counter delta
- Accumulates `_chargedSinceStartMah` or `_dischargedSinceStartMah`
- Detects charging phase transitions (charging → discharging or vice versa)
- On a transition, calls `_commitSessionEstimate()` to potentially add a new capacity sample
- Also calls `_trackSessionQuality()` during charging sessions

`_parseChargeCounterMah(rawValue)` — returns `double?`
- Converts raw charge counter to mAh, handling µAh vs mAh ambiguity

`_consumeChargeCounterDelta(chargeCounterMah, elapsedSeconds)` — returns `double?`
- Computes the change in charge counter since last tick
- Rejects deltas that imply impossible charge rates (>6× the battery capacity per hour)
- Returns `null` if the delta is invalid or this is the first reading

`_trackSessionQuality(currentMa, usedChargeCounter)` — private
- Accumulates current magnitude samples for stability analysis
- Tracks how many readings used the charge counter vs. current integration

`_resetSessionTracking()` — private
- Resets all session-level quality tracking counters to zero
- Called at the start of each new charging session

`_isSessionCurrentStable()` — returns `bool`, private
- Checks coefficient of variation of current across the session
- Returns true if CV ≤ 0.35 (current was steady enough to trust the integration)
- Requires at least 4 current samples

---

**CAPACITY ESTIMATION FUNCTIONS**

`_commitSessionEstimate(currentLevel, temperatureC)` — private
- Called at the end of each charging session (or during if the session is ongoing)
- Quality gate checks (all must pass):
  - Session must be a CHARGING session (not discharging)
  - Max SoC in session must not exceed 85%
  - Temperature must be between 15°C and 42°C
  - SoC delta must be ≥ 10% (≥ 15% if no charge counter)
  - Current must be stable (`_isSessionCurrentStable()`)
  - If charge counter was used, coverage must be ≥ 60%
- If all pass: `estimate = sessionChargedMah × 100 ÷ deltaPercent`
- Calls `_pushCapacitySample(estimate)` with the result

`_pushCapacitySample(estimateMah)` — private
- Range filter: must be between 45% and 170% of design capacity
- Outlier filter (if ≥ 8 samples exist): must be within 18% of median
- If passes: adds to `_capacitySamples` list, increments `_capacitySampleCount`
- Trims list to `_maxCapacitySamples` (120) by removing oldest
- Calls `_recomputeSmoothedCapacity()`
- Calls `_persistCapacitySamples()`
- Logs every 10 successful samples

`_recomputeSmoothedCapacity()` — private
- Computes the smoothed capacity from the sample pool using two averages blended 70/30:
  - **Trimmed mean (70%):** sorts samples, removes bottom 10% and top 10%, averages the rest — stable against outliers
  - **Recency-weighted mean (30%):** weights samples linearly by position (newer = up to 3× heavier) — responsive to real degradation
- Final result clamped to minimum of 650 mAh or 35% of design capacity

`_trimmedSamples(samples)` — returns `List<double>`, private
- Sorts input list, removes bottom 10% and top 10%
- Returns the trimmed middle portion
- Returns the full list unchanged if fewer than 5 samples

`_calculateMedian(values)` — returns `double`, private
- Standard statistical median: sort, return middle value (or average of two middle values for even-length lists)

`_persistCapacitySamples()` — private
- Saves the sample list (as List<String>) and sample count to SharedPreferences
- Runs asynchronously in a fire-and-forget Future — doesn't block anything
- Called after every new sample is successfully added

`setManualDesignCapacity(int? capacityMah)` — async, public
- Called from the UI when user manually enters their phone's battery specification
- Clamps input to 800–15,000 mAh
- Pass `null` to clear and revert to auto-detection
- Saves to SharedPreferences
- Re-fetches battery data to update display

---

**HEALTH CALCULATION FUNCTIONS**

`_calculateHealthConfidence()` — returns `double` (0.0–1.0), private
- Two factors, combined:
  - **Coverage (75% weight):** `_capacitySampleCount / 80` (80 is the target for "full confidence")
  - **Consistency (25% weight):** `1 - (coefficientOfVariation / 0.20)` — samples that agree with each other increase this
- Returns 0.0 on day one, approaches 1.0 after ~80 consistent sessions

`_calculateHealthPercentage(healthStatus, measuredCapacityMah, designCapacityMah)` — returns `double`, private
- Step 1 — Raw capacity health: `(measuredCapacityMah / designCapacityMah) × 100`
- Step 2 — Android status adjustment (subtract points based on hardware status):
  - Status 2 (Good): subtract 0
  - Status 3 (Overheat): subtract 2
  - Status 4 (Dead): subtract 8
  - Status 5 (Over voltage): subtract 3
  - Status 6 (Failure): subtract 4
  - Status 7 (Cold): subtract 2
- Step 3 — Confidence gating:
  - `trust = clamp((confidence - 0.45) / (1.0 - 0.45), 0.0, 1.0)`
  - `trustedTarget = 100% × (1-trust) + adjustedTarget × trust`
  - When confidence < 45%: displayed health stays near 100% (safe default)
  - When confidence is high: displayed health reflects the measured value
- Step 4 — EWMA smoothing:
  - `alpha = clamp(0.03 + trust × 0.20, 0.03, 0.23)`
  - `_smoothedHealthPercentage += (trustedTarget - _smoothedHealthPercentage) × alpha`
  - Alpha between 3%–23% — the number moves gradually, not instantly

`_getHealthString(status, healthPercentage)` — returns `String`, private
- Hardware fault states take priority:
  - Status 3 → "Overheat", 4 → "Dead", 5 → "Over voltage", 6 → "Failure", 7 → "Cold"
- Otherwise maps percentage to label:
  - ≥92% → "Excellent"
  - ≥84% → "Good"
  - ≥74% → "Fair"
  - ≥60% → "Aging"
  - <60% → "Weak"

---

**STRESS SCORE FUNCTIONS**

`_updateSignalAverages(temperatureC, voltageV, currentMa, elapsedSeconds)` — private
- Maintains EWMA (Exponentially Weighted Moving Average) for 3 signals:
  - `_ewmaTemperatureC`, `_ewmaVoltageV`, `_ewmaCurrentMa`
- `alpha = clamp(elapsedSeconds / 15, 0.05, 0.40)` — adapts to how long since last sample
- Prevents a single spike from inflating the stress score

`_updateStressExposure(elapsedSeconds, temperatureC, voltageV, currentMa, measuredCapacityMah)` — private
- Accumulates 3 long-term exposure scores that slowly decay:
  - `_thermalExposureScore`: accumulates every second above 35°C
  - `_highVoltageExposureScore`: accumulates every second above 4.15V
  - `_highCRateExposureScore`: accumulates every second where current/capacity > 0.8
- Each score decays by 0.1% per second (`×0.999`)
- Result: recent bad behavior matters more than old behavior

`_calculateStressScore(measuredCapacityMah)` — returns `double` (0–100), private
- Combines instant stress with accumulated exposure:
  - **Thermal instant:** 0 if ≤35°C; above that: `(temp-35)^1.35 × 1.4` (exponential — 45°C is much worse than 36°C)
  - **Voltage instant:** penalizes above 4.2V (overcharge) AND below 3.35V (deep discharge)
  - **C-rate instant:** penalizes current/capacity ratio above 0.8
  - **Exposure penalty:** adds `_thermalExposureScore×0.06 + _highVoltageExposureScore×0.08 + _highCRateExposureScore×0.09`
- Clamped to 0–100

---

**CYCLE COUNTING FUNCTIONS**

`_updateCycleCount(throughputMah, designCapacityMah, isCharging)` — private
- Only runs during discharge (skips charging ticks)
- Accumulates discharged mAh in `_throughputMahForCycle`
- When accumulated total ≥ design capacity: increments `_cycleCount`, subtracts one design capacity (excess carries forward)
- Example: 4,200 mAh discharged on a 4,000 mAh phone = 1 cycle counted + 200 mAh carry-forward
- Calls `_persistCycleState()` after each update

`_persistCycleState()` — private
- Saves `_cycleCount` and `_throughputMahForCycle` to SharedPreferences
- Runs asynchronously — doesn't block the main update loop

`_updatePhaseDurations(now, isCharging)` — private
- Detects charging phase transitions (isCharging flips from true to false or vice versa)
- When a transition is detected, adds the elapsed phase duration to `_totalChargingTime` or `_totalDischargingTime`
- Resets `_phaseStartTime` and `_activePhaseCharging` for the new phase

`_currentChargingDuration(now, isCharging)` — returns `Duration`
`_currentDischargingDuration(now, isCharging)` — returns `Duration`
- Returns the total accumulated time plus any ongoing current phase duration

---

**APP USAGE ATTRIBUTION FUNCTIONS**

`_updateAppUsageAttribution(throughputMah, isCharging, foregroundPackage, foregroundApp)` — private
- Only runs during discharge when throughputMah > 0
- Attribution logic:
  - If foreground app is known: 82% of mAh → foreground app, 18% → `__background__` bucket
  - If no foreground app known: 100% → `__background__` bucket
- Calls `_mergeAppUsage()` for each attributed bucket
- Calls `_emitAppUsage()` to broadcast the updated list

`_mergeAppUsage(packageName, appName, foregroundDeltaMah, backgroundDeltaMah, timestamp)` — private
- Looks up the app in `_appUsageByPackage` map by package name
- If new: creates a new `AppBatteryUsage` entry
- If existing: uses `copyWith()` to add the new mAh values to the running totals

`_emitAppUsage()` — private
- Converts `_appUsageByPackage` map values to a List
- Sorts by `totalMah` descending (highest drainer first)
- Broadcasts via `_appUsageController.add(...)`

---

**SETTINGS / ACTION FUNCTIONS (all public)**

`refreshAccessStatuses()` — async
- Calls all four refresh methods in sequence
- Called on app resume and when user taps "Refresh data"

`_refreshUsageAccessStatus()` — async, private
`_refreshForceStopAutomationStatus()` — async, private
`_refreshBatterySaverStatus()` — async, private
`_refreshSystemWriteAccessStatus()` — async, private
- Each: queries its specific Android permission via MethodChannel
- Only broadcasts on the stream if the status actually changed since last check

`openUsageAccessSettings()` — async, public
`openBatterySaverSettings()` — async, public
`openSystemWriteSettings()` — async, public
`openDisplaySettings()` — async, public
`openUltraBatterySaverSettings()` — async, public
`openForceStopAccessibilitySettings()` — async, public
- Each: sends a MethodChannel call to Kotlin to launch the corresponding Android settings screen
- Android requires users to manually grant sensitive permissions — the app can only navigate them to the right page

`reduceSystemBrightness()` — async, public — returns `bool`
- Sends MethodChannel call to Kotlin to reduce screen brightness
- Requires WRITE_SETTINGS permission
- Returns true on success, false on failure

`shortenScreenTimeout()` — async, public — returns `bool`
- Sends MethodChannel call to Kotlin to reduce screen-off timeout
- Also requires WRITE_SETTINGS permission

`requestAppForceStop(String packageName)` — async, public — returns `AppStopRequestResult`
- Sends MethodChannel call with the target package name
- Kotlin navigates to App Info screen and uses the accessibility service to tap Force Stop
- Returns `AppStopRequestResult` with `started` bool, `accessibilityEnabled` bool, `message` string

`isBackgroundServiceRunning()` — async, public — returns `bool`
- Asks Kotlin if the background monitoring service is currently running
- Used on startup to show correct monitoring state without requiring the user to tap Start

---

**HELPER FUNCTIONS (all private)**

`_toInt(value, {required int fallback})` — returns `int`
- Safe conversion: handles `int`, `num`, `String`, and `null` input
- Returns fallback if parsing fails

`_toDouble(value, {required double fallback})` — returns `double`
- Same as `_toInt` but for doubles

`_cleanString(value)` — returns `String`
- Returns "Unknown" for null or empty input
- Trims whitespace from strings

`_resolveElapsedSeconds(now)` — returns `double`
- Returns real elapsed seconds since last sample
- Clamps to minimum 1.0 to prevent division-by-zero errors

`_formatDuration(Duration duration)` — returns `String`
- Formats duration as "2h 15m", "15m 30s", or "45s"
- Used for log messages about phase durations

---

**STATE VARIABLES REFERENCE**

Important private fields maintained across ticks:

```
Capacity tracking:
_smoothedCapacityMah         ← Current best capacity estimate
_capacitySamples             ← List<double>, up to 120 session estimates
_capacitySampleCount         ← Total valid sessions ever (persisted)
_detectedDesignCapacityMah   ← Auto-detected (default 4000)
_manualDesignCapacityMah     ← User override (nullable)
_smoothedHealthPercentage    ← EWMA health %, prevents UI jumping
_capacityReceivedFromDevice  ← True once Android gave us a real capacity

Session tracking:
_sessionCharging             ← Is current session a charge session?
_sessionStartLevel           ← Battery % when session began
_sessionChargedMah           ← mAh accumulated this session
_lastChargeCounterMah        ← Previous charge counter (for delta)
_sessionCurrentSamples       ← Count of current readings this session
_sessionCurrentAbsSumMa      ← Sum of |current| for CoV calculation
_sessionCurrentAbsSquaredSumMa ← Sum of current² for CoV calculation
_sessionCounterSamples       ← Readings that used charge counter
_sessionFallbackSamples      ← Readings that used current integration

EWMA signals:
_ewmaTemperatureC            ← Smoothed temperature
_ewmaVoltageV                ← Smoothed voltage
_ewmaCurrentMa               ← Smoothed current

Stress accumulators:
_thermalExposureScore        ← Accumulated thermal stress (decays over time)
_highVoltageExposureScore    ← Accumulated voltage stress
_highCRateExposureScore      ← Accumulated C-rate stress

Totals:
_chargedSinceStartMah        ← Total charged since app started
_dischargedSinceStartMah     ← Total discharged since app started
_totalChargingTime           ← Total Duration spent charging
_totalDischargingTime        ← Total Duration spent discharging
_cycleCount                  ← Cycle counter (persisted)
_throughputMahForCycle       ← Partial cycle accumulator (persisted)
```

---

### 6.5 HomeScreen — UI and 6 Tabs

**File:** `lib/screens/home_screen.dart` (1,917 lines)

`HomeScreen` is a `StatefulWidget` with `SingleTickerProviderStateMixin` (for tab animation) and `WidgetsBindingObserver` (to detect app lifecycle events like backgrounding).

**State it holds:**
```
_batteryService     ← Single instance of RealBatteryService
_tabController      ← TabController for 6 tabs
_batteryData        ← Current BatteryData (updated by stream)
_history            ← Current history list (updated by stream)
_logs               ← Current log list (updated by stream)
_appUsage           ← Current app usage list (updated by stream)
_isMonitoring       ← Bool: is monitoring currently active?
_hasUsageAccess     ← Permission status (updated by stream)
_hasForceStopAutomation ← Permission status
_isBatterySaverEnabled  ← Status
_hasSystemWriteAccess   ← Permission status
```

**Initialization sequence (`initState`):**
1. `WidgetsBinding.instance.addObserver(this)` — registers for app lifecycle events
2. `_tabController = TabController(length: 6, vsync: this)` — sets up 6-tab controller
3. `_setupListeners()` — subscribes to all 8 streams
4. `_bootstrapMonitoring()` — checks if background service is running, then starts monitoring

**Stream listeners (`_setupListeners`):**
Each stream's `.listen()` callback simply calls `setState()` to update the corresponding state field. This triggers Flutter to rebuild the relevant widget subtree.

**The 6 Tabs:**

| Tab | Method | Content |
|---|---|---|
| Overview | `_buildOverviewTab()` | StatusIndicator, grid of StatCards (level, current, voltage, temp, capacity, power), throughput counters, line chart |
| Health | `_buildHealthTab()` | Device info (manufacturer/model/board), health %, design vs actual capacity, confidence, cycle count, projections, stress score, stress breakdown |
| Apps | `_buildAppUsageTab()` | Permission status, app list sorted by mAh (with foreground/background split), force-stop buttons |
| History | `_buildHistoryTab()` | HistoryPanel widget displaying the rolling 360-entry list |
| Logs | `_buildLogsTab()` | LogPanel widget displaying the last 150 event messages |
| Backup Enhancement | `_buildBackupEnhancementTab()` | Action buttons: Reduce Brightness, Shorten Screen Timeout, Battery Saver toggle, Ultra Battery Saver, display settings |

**App Bar:**
- Title: "Battery Analyzer"
- Start/Stop button (IconButton) — toggles monitoring
- Overflow menu (`PopupMenuButton`) with actions:
  - Tutorial (shows full tutorial dialog)
  - Refresh data (calls `_refreshDashboardData()`)
  - Theme (submenu: system/light/dark)
  - Set design capacity (dialog to enter mAh manually)
  - Reset samples (calls `clearData()`)
  - About

**Tutorial system:**
`_TutorialSectionData` — a const data class with `title`, `icon`, `details`, `howToUse`, `note?`
7 tutorial sections are defined as a const list at the top of the file (outside the class).

---

### 6.6 Widgets (6 Files)

All widgets are `StatelessWidget` — they receive data and render it. No logic.

#### StatCard (`widgets/stat_card.dart`)
A small metric tile: icon + title + value, displayed in a grid in the Overview and Health tabs.
Props: `icon` (IconData), `title` (String), `value` (String), `color` (Color)
Uses `AnimatedContainer` for smooth transitions when values change.
Title is always rendered in uppercase.

#### StatusIndicator (`widgets/status_indicator.dart`)
A card row showing the current session status.
Props: `isCharging` (bool), `health` (String), `current` (int mA)
Color logic: green if charging, red if discharging with current > 900 mA, otherwise primary color.
Icon: battery-charging-full if charging, battery-6-bar if discharging.
Displays: "Charging/Discharging session active" + "Health: X | Current: ±YYY mA"

#### HistoryPanel (`widgets/history_panel.dart`)
A fixed 280px-height scrollable list of BatteryHistory entries.
Props: `history` (List<BatteryHistory>)
Displays newest entry first (iterates list in reverse).
Each entry shows: charge direction icon (green ↗ or red ↘), formatted mA, level%, and timestamp.

#### LogPanel (`widgets/log_panel.dart`)
A fixed 420px-height scrollable list of log strings.
Props: `logs` (List<String>)
No processing — each string is already formatted as "HH:MM:SS  message" by the service.
Shows "No events yet" if list is empty.

#### FrostedPanel (`widgets/frosted_panel.dart`)
A decorative container with a frosted-glass visual effect using `BackdropFilter` blur.
Props: `child`, `padding`, `radius`, `accentColor?`, `compact` (bool)
Uses `ImageFilter.blur` with `sigmaX/Y` of 8 (dark mode) or 18 (light mode).
Uses a `LinearGradient` from top-left to bottom-right with semi-transparent colors.
Includes a box shadow for subtle depth.

#### LineChart (`widgets/line_chart.dart`)
A custom drawn area chart using Flutter's `CustomPainter`.
Props: `values` (List<double>), `lineColor` (Color), `fillColor` (Color), `emptyLabel?`, `minY?`, `maxY?`
Shows `emptyLabel` text if fewer than 2 data points.
Draws: a filled area under the line + a 2.2px stroke line on top.
Normalizes values to the canvas height using min/max range.
`shouldRepaint` returns true when values or colors change.

---

## 7. DATA FLOW: END-TO-END WALKTHROUGH

This is the complete journey of data from battery hardware chip to the screen, repeated every second.

**Step 1 — Android reads the battery chip (Kotlin)**
Android's `BatteryManager` system reads raw numbers from the battery chip: voltage in millivolts, temperature in tenths of a degree Celsius, current in microamps, charge level as a fraction, etc. This happens inside `MainActivity.kt`'s `getBatteryInfo()` method.

**Step 2 — Kotlin packs into a Map and sends across the channel**
All raw values are assembled into a `Map<String, Any>` and returned to Dart via the MethodChannel's response mechanism.

**Step 3 — Dart receives and parses the raw Map**
Inside `_processBatteryData()`, the raw values are pulled out using `_toInt()`, `_toDouble()`, `_cleanString()` helpers. Unit conversions happen here: temperature ÷ 10 → °C, voltage ÷ 1000 → V, current ÷ 1000 → mA (for phones that report microamps).

**Step 4 — The service runs all calculations**
`_processBatteryData()` calls all the calculation functions in sequence: capacity detection, charge integration, EWMA updates, stress exposure updates, stress score calculation, health calculation.

**Step 5 — A BatteryData object is created**
All computed values are assembled into a new immutable `BatteryData` object. Every second, a fresh one replaces the old one.

**Step 6 — The Stream broadcasts the object**
`_batteryDataController.add(batteryData)` pushes the new object into the broadcast stream. Any subscriber receives it immediately.

**Step 7 — HomeScreen receives it and triggers UI rebuild**
The stream listener in `_setupListeners()` calls `setState(() => _batteryData = data)`. Flutter rebuilds the affected widget subtree.

**Step 8 — Widgets render the values**
The active tab's widgets read their properties from the `_batteryData` object. StatCards display individual fields. LineChart reads from the history list. Each widget is responsible for displaying one piece of data.

**Parallel path — EventChannel:**
Android's `BroadcastReceiver` listens for `ACTION_BATTERY_CHANGED`. When the user plugs in or unplugs the charger, Android fires this broadcast immediately. Kotlin passes the data through the EventChannel to Dart, triggering the same `_processBatteryData()` call — so the UI updates instantly, not waiting for the next 1-second tick.

---

## 8. THE 8 STREAMS SYSTEM

Each stream only updates when its data actually changes, preventing unnecessary rebuilds.

| Stream | Data Type | Update Frequency | What triggers it |
|---|---|---|---|
| `batteryDataStream` | `BatteryData` | Every second | Every timer tick |
| `historyStream` | `List<BatteryHistory>` | Every second | Every new BatteryData |
| `logStream` | `List<String>` | On events | When `_addLog()` is called |
| `appUsageStream` | `List<AppBatteryUsage>` | Every second during discharge | When app attribution updates |
| `usageAccessStream` | `bool` | On change only | When permission status changes |
| `forceStopAutomationStream` | `bool` | On change only | When accessibility service status changes |
| `batterySaverStream` | `bool` | On change only | When battery saver status changes |
| `systemWriteAccessStream` | `bool` | On change only | When write settings permission changes |

**Why separate streams?** Each stream can have different subscribers. If you later build a background widget or a notification system, it can subscribe to just the streams it needs without receiving irrelevant data.

---

## 9. BATTERY HEALTH CALCULATION — FULL ALGORITHM

This is the most complex and most important system in the app. Full details:

### The Core Formula
```
health % = actual_current_capacity_mAh ÷ original_design_capacity_mAh × 100
```

### The Problem
Android does not expose the actual current capacity directly. The app must measure it indirectly from real charging behavior.

### The Key Insight
If the phone charges from 20% to 60% (a 40% SoC change) and 1,500 mAh flows in during that time:
```
full capacity = 1,500 mAh × 100 ÷ 40 = 3,750 mAh
```

### Phase 1: Collecting Session Estimates

**Quality gate** — a charging session is ONLY used if ALL of these pass:
- Session type is charging (not discharging)
- Maximum SoC during session did not exceed 85%
- Temperature stayed between 15°C and 42°C
- SoC change was at least 10% (15% if no charge counter data available)
- Current was stable: coefficient of variation ≤ 0.35
- If charge counter was used: ≥60% of readings used it (counter coverage)

**Estimate formula:**
```
estimate = mAh_charged_this_session × 100 ÷ soc_delta_percent
```

### Phase 2: Outlier Filtering

**Range filter:** estimate must be between 45% and 170% of design capacity
- Below 45%: physically impossible (battery can't degrade that fast)
- Above 170%: physically impossible (can't exceed spec by that much)

**Median deviation filter** (requires 8+ existing samples):
- Sort all existing samples, find median
- If new estimate is more than 18% away from median → reject
- Purpose: catches "glitch sessions" where the phone was interrupting the charge

### Phase 3: Sample Pool Management

- Pool holds up to 120 samples (rolling window, oldest dropped first)
- Persisted to SharedPreferences after every new sample
- `_capacitySampleCount` tracks total ever collected (including dropped ones)

### Phase 4: Smoothing the Pool

Two averages are computed and blended 70/30:

**Trimmed mean (70% weight):**
- Sort all samples
- Remove bottom 10% and top 10% (at least 1 from each end)
- Average the remaining middle values
- Effect: stable, resistant to extreme outliers

**Recency-weighted mean (30% weight):**
- Weight each sample linearly by its position in the list (newer = heavier)
- Newest sample gets weight = 3, oldest gets weight = 1
- Effect: responsive to genuine recent degradation

**Final formula:**
```
smoothedCapacity = (robustMean × 0.70) + (recencyWeighted × 0.30)
```

### Phase 5: Confidence Gating

**Confidence score** (0.0 – 1.0):
```
coverage = clamp(capacitySampleCount / 80, 0, 1)     ← 75% weight
consistency = clamp(1 - (CoV / 0.20), 0.0, 1.0)     ← 25% weight
confidence = (coverage × 0.75) + (consistency × 0.25)
```

**Trust calculation:**
```
trust = clamp((confidence - 0.45) / (1.0 - 0.45), 0.0, 1.0)
```
- Below 45% confidence: trust = 0, health stays near 100% (safe default)
- Full confidence: trust = 1, full measured value shown

**Blending formula:**
```
trustedTarget = (100.0 × (1.0 - trust)) + (capacityHealth × trust)
```

### Phase 6: Android Status Adjustment

Small penalty applied based on Android's hardware health status:
- Good: −0 pts
- Cold: −2 pts
- Overheat: −2 pts
- Over voltage: −3 pts
- Failure: −4 pts
- Dead: −8 pts

### Phase 7: EWMA Smoothing

Prevents the displayed number from jumping between ticks:
```
alpha = clamp(0.03 + (trust × 0.20), 0.03, 0.23)
_smoothedHealthPercentage += (trustedTarget - _smoothedHealthPercentage) × alpha
```
- Low trust: alpha ≈ 0.03 (moves at 3% per second toward target)
- High trust: alpha ≈ 0.23 (moves at 23% per second — more responsive)

### Phase 8: Label Mapping
```
≥92% → "Excellent"
≥84% → "Good"
≥74% → "Fair"
≥60% → "Aging"
<60% → "Weak"
```
Hardware faults (Overheat, Dead, Over voltage, Cold, Failure) override these labels entirely.

---

## 10. KEY DART/FLUTTER CONCEPTS (FOR NEWCOMERS)

### Class
A template/blueprint. `BatteryData` is a blueprint for a battery snapshot object. Every second, a new object is created from this blueprint with current values.

### `final` field
A field that cannot change after the object is created. All fields in `BatteryData` are `final`. To "change" a value, use `copyWith()` to create a new object with only the changed fields.

### Stream
Like a TV channel. The service is the broadcaster (`StreamController.add()`), the UI is the viewer (`.listen()`). Multiple parts of the app can subscribe to the same stream simultaneously.

### `async` / `await`
`async` marks a function that might take time (like reading from storage or calling Android). `await` pauses execution at that line until the slow operation completes, but doesn't freeze the whole app while waiting.

### `setState()`
A Flutter command that says "my data changed — please redraw." Without calling this, the screen never updates even if data changed. Flutter only redraws widgets that depend on the changed data.

### Widget
Everything visible in Flutter is a Widget. A button, a text label, a card, the entire screen — all widgets. They are descriptions of how to draw something. When data changes and `setState()` is called, Flutter rebuilds the affected widgets from scratch.

### `StatefulWidget` vs `StatelessWidget`
- `StatelessWidget` — displays data it receives via props, never changes
- `StatefulWidget` — holds its own state that can change over time, has `setState()`

### `MethodChannel`
A named pipe between Dart and Kotlin. Dart calls `channel.invokeMethod('name', args)` and Kotlin listens for that name and executes corresponding code.

### `EventChannel`
Like a MethodChannel but for continuous push events. Android pushes data at any time; Dart receives it via a stream listener.

### `SharedPreferences`
Android's simple key-value storage. Works like a small persistent dictionary on the device. Used here to store capacity samples, cycle count, and manual capacity between app sessions.

---

## 11. PLANNED AI/ML BACKEND — FULL DESIGN

### 11.1 Why AI/ML and Which Problems It Solves

Not every problem needs ML. The following problems DO benefit from ML here (rule-based logic cannot solve them):

| Problem | Why ML wins |
|---|---|
| Remaining Useful Life prediction | Requires learning degradation curves from real data. No formula can predict when a specific battery will fail. |
| Anomaly detection | Requires learning "normal" for this specific device and flagging deviations. Normal varies by user, time of day, phone model. |
| Smart time-to-empty | Current drain rate doesn't predict future drain. ML can incorporate time-of-day patterns, weekly rhythms, and usage context. |
| Personalized charging advice | Rule-based tips are generic. ML can cluster users into habit archetypes and give specific recommendations for this user's actual behavior. |

The following problems do NOT benefit from ML and should stay as-is:
- Health % calculation — already a solid statistical estimator grounded in physics
- Stress score — based on known electrochemistry, no training data would improve this
- Per-app battery attribution — Android doesn't expose true per-app power, so training on estimated inputs compounds uncertainty

### 11.2 The Four ML Features

---

#### Feature 1: Remaining Useful Life (RUL) Prediction

**What it answers:** "How many charge cycles does this battery have left before health drops below 80%?"

**Model type:** Gradient Boosted Regression (XGBoost or LightGBM)
- Tree-based models handle non-linear battery degradation curves well
- Interpretable via SHAP values — can tell users what's driving the prediction
- Trains and runs on CPU — no GPU needed
- Alternative: LSTM recurrent neural network (better if long per-device history is available)

**Input features:**
- Current health % and rate of change over last 30 days
- Current cycle count
- Smoothed capacity history (mAh trajectory over time)
- Confidence % of health estimate
- Average thermal exposure score
- Average high-voltage exposure score
- Average charging C-rate
- % of sessions charged above 80% SoC
- Device model (for model-specific degradation priors)

**Output:**
- `rul_cycles_median` — most likely cycles remaining
- `rul_cycles_low` / `rul_cycles_high` — confidence interval
- `rul_months_estimate` — at this user's charging frequency
- `top_degradation_driver` — "thermal" / "high_voltage" / "high_crate" / "age"

---

#### Feature 2: Anomaly Detection

**What it answers:** "Is this battery behaving unusually compared to its own history?"

**Model type:** Isolation Forest (tabular) + Autoencoder (time-series curve shapes)
- Isolation Forest: fast, no labels needed, good for per-session feature vectors
- Autoencoder: learns the normal shape of voltage/current curves, flags deviations
- Combining both gives better coverage across session-level and signal-level anomalies

**Input signals:**
- Discharge rate (mAh/hour) vs. time-of-day baseline for this device
- Temperature during charge vs. historical norm for this device
- Voltage curve shape during discharge
- Session duration vs. SoC gained
- Rolling 7-day average drain rate
- Deviation from user's typical daily battery cycle
- Capacity estimate vs. 30-day moving average
- Frequency of deep discharges (<15%)

**Output:**
- `anomaly_score` — 0–100 (above 70 = alert-worthy)
- `anomaly_type` — "none" / "drain" / "thermal" / "charge" / "capacity"
- `anomaly_explanation` — plain-language string, e.g. "Discharge rate 2.4× above your normal Tuesday pattern"

---

#### Feature 3: Smart Time-to-Empty

**What it answers:** "When will the battery actually die, accounting for your usage patterns?"

**Current approach:** `remaining_mAh ÷ current_drain_rate` — accurate only if drain is constant.

**ML approach:** Forecasts the battery level curve over the next several hours using the user's historical pattern for this time of day and day of week.

**Model type:** LSTM (Long Short-Term Memory) recurrent neural network, or Temporal Fusion Transformer (TFT) for higher accuracy
- Start with LSTM — simpler, less compute
- TFT if accuracy improvement justifies the compute cost

**Input features:**
- Current battery level and drain rate
- Time of day and day of week
- Current temperature and voltage
- Screen on/off state
- Last 30 minutes of drain history
- Drain rates at this time on previous days (historical pattern)
- Day-of-week usage variation for this device

**Output:**
- `tte_minutes_ml` — ML-predicted minutes until empty
- `predicted_soc_in_2h` — expected % in 2 hours
- `predicted_soc_in_4h` — expected % in 4 hours

---

#### Feature 4: Personalized Charging Advice

**What it answers:** "What specific habit change would most extend this battery's life?"

**Model type:** K-Means Clustering + Rule Engine
- K-Means clusters all users into charging habit archetypes (unsupervised — no labels needed)
- A rule engine maps each archetype to specific recommendations
- More explainable than a black-box classifier — users can understand why they're getting a recommendation
- Archetypes improve over time as more users join

**What the model learns:**
- Typical plug-in time and plug-out time
- Average SoC when plugging in
- How often charged above 80% / below 20%
- Average charge session duration
- Frequency and severity of thermal events
- Average C-rate
- % of time battery spends above 80%
- Deep discharge events per week

**Output:**
- `habit_archetype` — "overnight_charger" / "top_up_charger" / "deep_cycler" / "healthy"
- `longevity_score` — 0–100 (how healthy the user's charging habits are)
- `top_recommendation` — one specific, actionable string
- `projected_health_12mo_current` — predicted health % in 12 months at current habits
- `projected_health_12mo_improved` — predicted health % if recommendation followed

---

### 11.3 Training Datasets

**Two-phase training strategy:**
1. **Pre-train** on public research datasets to learn general battery physics
2. **Fine-tune** on each user's own app data to personalize predictions for their specific phone

#### Public Dataset 1: NASA Prognostics Center — Battery Dataset
- **URL:** https://ti.arc.nasa.gov/tech/dash/groups/pcoe/prognostic-data-repository
- **Best for:** RUL prediction, general degradation curves
- **What it contains:** Real 18650 Li-ion cells charged/discharged to end-of-life. Every cycle recorded with impedance, capacity fade, voltage/current curves, temperature. Cells go from 100% health down to ~70% over hundreds to thousands of cycles.
- **Key columns:** cycle_number, capacity_mah, voltage_curve, current_curve, temperature, internal_resistance, charge_time, discharge_time
- **License:** Free, public domain

#### Public Dataset 2: CALCE Battery Research Group Dataset
- **URL:** https://calce.umd.edu/battery-data
- **Best for:** Anomaly detection training, degradation under varied conditions
- **What it contains:** Multiple Li-ion cell chemistries tested under varying temperatures, charge rates, and depths of discharge. Good for training anomaly models to recognize what heat stress or high C-rate stress looks like in voltage curves.
- **Key columns:** multiple cell chemistries, varied charge rates, varied temperatures, capacity fade over cycles, EIS measurements
- **License:** Free for research use

#### Public Dataset 3: Stanford Fast Charging Dataset (Severson et al. 2019)
- **URL:** https://data.matr.io/1
- **Published in:** Nature Energy
- **Best for:** Charging advice model (directly shows which charging protocols cause faster degradation)
- **What it contains:** 124 Li-ion cells cycled to end-of-life under 72 different fast-charging protocols. Shows which protocols cause faster degradation. The landmark paper showed early-cycle voltage curves could predict RUL with 9% error.
- **Key columns:** 72 charge protocols, 124 cells, discharge_capacity_per_cycle, internal_resistance, voltage_time_curves, cycle_lifetime
- **License:** Free, CC BY 4.0

#### Public Dataset 4: Toyota Research — Battery Degradation Dataset
- **URL:** https://github.com/rdbraatz/data-driven-prediction-of-battery-cycle-life
- **Best for:** Supplementing the Stanford dataset with more diversity
- **What it contains:** Companion to the Stanford paper. More cells, more diverse charge conditions. Together with the Stanford set, covers a wide range of protocols for generalizable training.
- **License:** Free, public

#### App-Generated Data (from real users)
Over time, the most valuable dataset will be the app's own session uploads. Fields available from the app:

Per session: `session_type`, `start_soc_pct`, `end_soc_pct`, `duration_minutes`, `mah_transferred`, `avg_current_ma`, `avg_temp_c`, `max_temp_c`, `avg_voltage_v`, `current_cv`, `capacity_estimate_mah`, `health_pct`, `cycle_count`, `stress_score`, `voltage_samples[20]`, `current_samples[20]`

Per device (long-term): health trajectory over months, cycle accumulation rate, habit patterns by time-of-day and day-of-week

---

### 11.4 Data the App Sends to the Backend

#### Session Upload (sent at end of each charging/discharging session)
**Why sessions, not per-second?** Batching by session keeps data volume manageable and is more privacy-preserving than a constant stream.

```
Device identity (anonymous):
  device_id                 ← SHA-256 hash of device fingerprint, never linked to account
  manufacturer              ← e.g. "Samsung"
  model                     ← e.g. "Galaxy S21"
  design_capacity_mah       ← Original rated capacity

Session summary:
  session_type              ← "charge" or "discharge"
  start_soc_pct             ← Battery % at session start
  end_soc_pct               ← Battery % at session end
  duration_minutes          ← How long the session lasted
  mah_transferred           ← Total mAh charged or discharged
  session_timestamp_utc     ← Unix epoch (hour-of-day patterns, not exact time)

Session quality signals:
  avg_current_ma            ← Average current magnitude
  avg_temp_c                ← Average temperature
  max_temp_c                ← Peak temperature
  avg_voltage_v             ← Average voltage
  current_cv                ← Coefficient of variation of current
  capacity_estimate_mah     ← App's current smoothed capacity
  health_pct                ← App's current health estimate
  cycle_count               ← Cumulative cycles at time of session
  stress_score              ← App's stress score at session end

Voltage-current curve (downsampled to 20 points):
  voltage_samples[20]       ← Evenly-spaced voltage readings across the session
  current_samples[20]       ← Evenly-spaced current readings (curve shape for anomaly detection)
```

#### Daily Inference Ping (sent once daily or on user request)
A lightweight call asking for the latest ML predictions.

```
  device_id
  current_health_pct
  current_cycle_count
  current_capacity_mah
  sessions_last_30_days
  current_soc_pct
  current_drain_rate_mah_hr
  local_hour_of_day         ← 0–23
  day_of_week               ← 0–6
```

---

### 11.5 Backend Response Contract

The backend returns a single JSON object per inference ping with all four model outputs:

```json
{
  "rul": {
    "cycles_median": 340,
    "cycles_low": 270,
    "cycles_high": 420,
    "months_estimate": 14.2,
    "top_degradation_driver": "thermal"
  },
  "anomaly": {
    "score": 0,
    "type": "none",
    "explanation": null
  },
  "time_to_empty": {
    "tte_minutes_ml": 187,
    "predicted_soc_in_2h": 58,
    "predicted_soc_in_4h": 31
  },
  "charging_advice": {
    "habit_archetype": "overnight_charger",
    "longevity_score": 42,
    "top_recommendation": "Your battery stays above 90% for 8 hours every night. Set a charging limit of 80% or unplug before sleeping.",
    "projected_health_12mo_current": 74.0,
    "projected_health_12mo_improved": 83.5
  }
}
```

---

### 11.6 Backend Architecture

**Components:**

1. **API Gateway (FastAPI)** — Receives session uploads and inference pings from the app. Handles authentication (JWT tokens), rate limiting, and routes requests to the appropriate service.

2. **Ingest Service** — Validates incoming session data (Pydantic schemas), normalizes units, writes to the time-series database. Triggered by session uploads.

3. **ML Inference Service** — Loads trained models from the Model Registry, runs predictions, returns results. Triggered by daily inference pings.

4. **Training Pipeline (Celery worker)** — Runs nightly in the background. Re-trains personalization models (anomaly baselines, time-to-empty LSTMs, clustering) on newly collected user data. Logs experiments to MLflow. Updates model registry on improvement.

5. **Notification Service** — When the anomaly detection model flags a session above threshold (score > 70), this service sends a push notification to the device via Firebase Cloud Messaging (FCM).

6. **TimescaleDB** — PostgreSQL extension optimized for time-series. Stores all session upload records efficiently. Supports fast time-range queries like "give me all sessions for device X in the last 30 days."

7. **PostgreSQL** — Stores per-device state: latest health trajectory, current predictions, habit archetype, cycle count, last model update timestamp.

8. **Redis** — Caches the latest ML inference response per device for 24 hours. Prevents re-running expensive inference on every app open.

9. **MLflow (Model Registry)** — Version-controls all trained models. Tracks experiment results. Allows rollback if a new training run performs worse. Serves the production model to the inference service.

**Data flow summary:**
```
App → HTTPS → API Gateway → Ingest Service → TimescaleDB
                          ↓
                   ML Inference Service ← Model Registry (MLflow)
                          ↓
                   JSON Response → App
                          
Nightly: Training Pipeline reads TimescaleDB + public datasets → trains models → MLflow
         If anomaly detected: Notification Service → FCM → App push notification
```

---

### 11.7 Technology Stack (Backend)

**API Layer:**
- **FastAPI (Python)** — REST API framework. Chosen because Python is the ML ecosystem's native language, FastAPI is async, fast, and auto-generates API documentation.
- **Pydantic** — Request/response validation. Validates incoming JSON and gives clear error messages.
- **JWT Auth** — Token-based device authentication. Each device gets a token on first registration — no user accounts required.

**ML / Data Science:**
- **scikit-learn** — Isolation Forest (anomaly detection), K-Means (clustering). Mature, no GPU needed.
- **XGBoost / LightGBM** — RUL regression model. Best-in-class for tabular regression, interpretable, CPU-only.
- **PyTorch** — LSTM for time-to-empty forecasting and Autoencoder for curve-level anomaly detection.
- **pandas + NumPy** — Data cleaning, normalization, and feature engineering.
- **MLflow** — Model registry, experiment tracking, model versioning.
- **SHAP** — Model explainability library. Generates the "what's driving this prediction" explanations shown to users.

**Data Storage:**
- **TimescaleDB** — PostgreSQL extension for time-series. Stores all session upload records.
- **PostgreSQL** — Per-device profile and predictions storage.
- **Redis** — Prediction caching (24-hour TTL per device).

**Infrastructure:**
- **Docker + Docker Compose** — Each service runs in its own container. Easy to deploy anywhere.
- **Celery + Redis** — Background task queue for nightly model retraining.
- **Firebase Cloud Messaging (FCM)** — Push notifications to Android devices when anomalies are detected.

---

### 11.8 Privacy Design

The core principle: **the backend should never need to know who the user is.**

**What is NOT sent to the backend:**
- No GPS or location data
- No app names (only aggregate drain rates)
- No exact timestamps (only hour-of-day and day-of-week)
- No account linkage (device_id is a local hash, not tied to any login)
- No raw per-second data stream (only downsampled 20-point curves per session)

**Data minimization strategies:**
- Session-level uploads only (not every second)
- Aggregation happens on the device; the backend receives summaries
- Opt-in data sharing — users choose whether to contribute training data
- Local-first fallback — all existing app features work offline if backend is unavailable
- device_id is a SHA-256 hash of device properties, never linked to an account

---

### 11.9 Build Roadmap

**Phase 1 — Foundation (Weeks 1–3)**
Goal: Real battery session data flowing into the database.
- Set up FastAPI project, Docker Compose, PostgreSQL + TimescaleDB
- Build device registration endpoint (generates device_id + JWT token)
- Build session upload endpoint with Pydantic validation
- Add session upload call to the Android app (triggered at end of each charging/discharging session)
- Download all 4 public datasets, understand their structure
- Build data preprocessing pipeline (normalize, engineer features)

Deliverable: The app uploads sessions to the backend. The database contains real battery data.

**Phase 2 — First ML Model: RUL Prediction (Weeks 4–6)**
Goal: The app shows "~340 cycles remaining (~14 months)" in the Health tab.
- Train XGBoost RUL model on NASA + Stanford datasets
- Evaluate with cross-validation (target: <15% mean absolute error)
- Set up MLflow to track experiments and register the best model
- Build inference endpoint (receives device state, returns RUL prediction)
- Add SHAP explainability — identify top degradation driver per prediction
- Add "AI Insights" section to the Health tab in the app to display RUL

Deliverable: Working RUL model displayed in the app.

**Phase 3 — Anomaly Detection + Push Alerts (Weeks 7–9)**
Goal: Users receive push alerts when unusual battery behavior is detected.
- Train Isolation Forest on accumulated user session data
- Build per-device baseline profiles (rolling 30-day normal behavior)
- Score each new session upload against the device's baseline
- Integrate Firebase Cloud Messaging — backend pushes alerts to device
- Add anomaly alert card to the app's Overview tab
- Train Autoencoder on voltage curve shapes for signal-level anomalies

Deliverable: Push notification system for battery anomalies.

**Phase 4 — Personalization: Smart TTE + Charging Advice (Weeks 10–14)**
Goal: Fully personalized AI layer.
- Train LSTM time-to-empty model on per-device session history
- Run K-Means clustering across all devices to find habit archetypes
- Build the charging advice rule engine mapped to each archetype
- Add nightly Celery job to retrain personalization models on new data
- Add "Smart Forecast" and "Habit Score" sections to the app UI
- A/B test ML time-to-empty vs. current linear formula — measure improvement

Deliverable: Every user gets predictions and advice tuned to their specific phone and habits.

---

## 12. OPEN QUESTIONS AND FUTURE CONSIDERATIONS

### Technical questions to resolve before Phase 1:

1. **Server hosting:** Where will the backend run? Options: a personal VPS (DigitalOcean, Linode), a free tier cloud (Railway, Render), or a managed service (Google Cloud Run). The backend is stateful (databases), so serverless functions alone won't work.

2. **App authentication:** How will the app get its initial JWT token? The simplest approach is an anonymous device registration endpoint that issues a token on first launch, stored in SharedPreferences alongside the capacity samples.

3. **Offline sync:** If the user was offline for several days and accumulated many sessions, should the app batch-upload them all at once when it reconnects? Yes — the ingest service should handle out-of-order session timestamps gracefully.

4. **Model cold start:** A new device has no history, so personalized models can't run. The fallback is using the global population model (trained on public datasets + anonymized user data) until enough per-device history accumulates (~30 sessions).

5. **Consent and opt-in:** Before sending any data to the backend, the app should show a clear, simple consent screen explaining what data is collected, why, and how to opt out. This is both legally important and builds user trust.

### Possible future features (not currently planned):

- **Cross-device comparison:** "Your battery is degrading faster than the average for your phone model" — requires enough devices of the same model in the database.
- **Battery replacement recommendation:** When health drops below 80% and cycles are high, proactively recommend replacement with estimated cost.
- **Charging schedule optimizer:** "Based on your wake-up time and typical overnight drain, start charging at 5:30 AM instead of midnight."
- **Fleet monitoring:** Enterprise version tracking battery health across a company's device fleet.
- **Widget / notification shade card:** Show the AI insights (RUL, anomaly score) without opening the app.

---

*End of documentation — Battery Manager v1.0*
*Document generated: March 2026*
*Total scope: Existing Flutter/Kotlin app + planned Python/ML backend*
