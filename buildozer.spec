[app]

# (str) Title of your application
title = Lecteur Vocal OCR

# (str) Package name
package.name = ocrvoice

# (str) Package domain (needed for android/ios packaging)
package.domain = org.accessibility

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,txt

# (str) Application versioning (method 1)
version = 1.0

# (list) Application requirements
requirements = python3,kivy,opencv-python,pytesseract,pyttsx3,plyer,pillow

# (str) Supported orientation (portrait, sensorPortrait, userPortrait, landscape, sensorLandscape, userLandscape)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

[android]

# (str) Android entry point, default is ok for Kivy-based app
# android.entrypoint = org.kivy.android.PythonActivity

# (list) Pattern to whitelist for the whole project
android.whitelist = lib/python*/site-packages/cv2/*

# (str) Android app theme, default is ok for Kivy-based app
# android.theme = "@android:style/Theme.NoTitleBar"

# (list) Android application meta-data to set (key=value format)
android.meta_data = android.max_aspect=2.1

# (list) Android library project to add (will be added in the
# project.properties automatically.)
# android.library_references = @(name)

# (str) Android logcat filters to use
android.logcat_filters = *:S python:D

# (bool) Copy library instead of making a libpymodules.so
android.copy_libs = 1

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a, armeabi-v7a

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

# (str) XML file for custom backup rules (see official auto backup documentation)
# android.backup_rules =

# (str) If you need to insert variables into your AndroidManifest.xml file,
# you can do so with the manifestPlaceholders property.
# This property takes a map of key-value pairs.
# android.manifest_placeholders = [:]

# (bool) Skip byte compile for .py files
# android.no-byte-compile-python = False

# (str) The format used to package the app for release mode (aab or apk).
# android.release_artifact = aab

[android.permissions]
# (list) Android permissions your app needs
CAMERA = 1
WRITE_EXTERNAL_STORAGE = 1
READ_EXTERNAL_STORAGE = 1
RECORD_AUDIO = 1
INTERNET = 0