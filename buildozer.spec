[app]
# Title and package info
title = Workout Coach
package.name = workoutcoach
package.domain = com.elitecoach

# Source
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,mp3,csv

# App version
version = 1.0

# Requirements — core + pandas fallback
requirements = python3,kivy==2.3.0,pillow,pyttsx3

# Android-specific
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.archs = arm64-v8a, armeabi-v7a

# Permissions
android.permissions = INTERNET, RECORD_AUDIO

# Orientation
orientation = portrait

# Icons (place icon.png in same folder)
# icon.filename = %(source.dir)s/icon.png
# presplash.filename = %(source.dir)s/presplash.png

[buildozer]
log_level = 2
warn_on_root = 1
