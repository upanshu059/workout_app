# Elite AI Workout Coach — Android Build Guide

## What's included
```
workout_coach_android/
├── main.py           ← Full app (converted from PyQt6)
├── buildozer.spec    ← Android build config
├── workouts.csv      ← Default workout data
└── bell.mp3          ← (You supply this — any short beep/bell sound)
```

---

## Prerequisites

You need a **Linux machine or WSL2** (Windows Subsystem for Linux). macOS also works.

### 1. Install system dependencies (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y \
  python3-pip \
  python3-venv \
  git \
  zip \
  unzip \
  openjdk-17-jdk \
  libffi-dev \
  libssl-dev \
  autoconf \
  libtool \
  pkg-config \
  cmake \
  zlib1g-dev
```

### 2. Install Buildozer

```bash
pip3 install --user buildozer
```

> Buildozer automates downloading the Android SDK, NDK, and compiling your app.

---

## Build the APK

### 3. Place your files

Put all files into one folder:
```
my_workout_app/
├── main.py
├── buildozer.spec
├── workouts.csv
└── bell.mp3        ← supply a short beep (any free bell/beep MP3)
```

### 4. Run the build

```bash
cd my_workout_app
buildozer android debug
```

**First run takes 20–40 minutes** — it downloads the Android SDK/NDK automatically.

Subsequent builds are much faster (2–5 min).

### 5. Find your APK

```
my_workout_app/bin/workoutcoach-1.0-arm64-v8a-debug.apk
```

---

## Install on your Android phone

### Option A — USB (recommended)

1. On your phone: **Settings → Developer Options → USB Debugging → ON**
   - (To enable Developer Options: tap Build Number 7 times in About Phone)
2. Connect USB, then:

```bash
# Install ADB if needed
sudo apt install android-tools-adb

# Verify phone is detected
adb devices

# Install the APK
adb install bin/workoutcoach-1.0-arm64-v8a-debug.apk
```

### Option B — Direct file transfer

1. Copy the APK to your phone (USB, Google Drive, email, etc.)
2. On your phone: **Settings → Security → Allow Unknown Sources** (or "Install Unknown Apps")
3. Open the APK file on the phone → tap Install

---

## Customizing workouts

Edit `workouts.csv` before building. Columns:

| Column | Required | Description |
|---|---|---|
| `workout_id` | ✓ | Groups exercises into a workout (1, 2, 3...) |
| `type` | ✓ | Section name (e.g. Warm Up, Strength, HIIT) |
| `exercise` | ✓ | Exercise name |
| `sets` | ✓ | Number of rounds |
| `reps` | optional | If filled, timer = reps × 3 seconds |
| `time` | optional | Fixed duration in seconds |

---

## Timing config

Edit the top of `main.py`:

```python
START_DELAY = 10    # seconds before workout begins
REST_EXERCISE = 20  # rest between exercises
REST_SET = 40       # rest between sets
REST_TYPE = 100     # rest between sections
```

---

## Text-to-Speech (TTS)

- **On Android**: Uses Android's native TTS engine (built in, no extra setup)
- **Desktop testing**: Uses `pyttsx3` if installed (`pip install pyttsx3`)
- **Fallback**: Prints to console if neither is available

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `buildozer` not found | Run `~/.local/bin/buildozer` or add `~/.local/bin` to PATH |
| SDK license error | Run `yes \| sdkmanager --licenses` |
| Build hangs at NDK | Delete `~/.buildozer` and retry |
| APK installs but crashes | Check logs: `adb logcat \| grep python` |
| No sound | Ensure `bell.mp3` is in the project folder |

---

## Testing on desktop (without Android)

```bash
pip install kivy pyttsx3 pandas
python main.py
```
