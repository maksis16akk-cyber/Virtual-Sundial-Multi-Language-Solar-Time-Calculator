Virtual Sundial — Multi‑Language Solar Time Calculator
8 languages, one virtual sundial — compute solar time, altitude, azimuth, and see an ASCII shadow dial right in your terminal.

✨ Features
🌍 Any location – input latitude and longitude

🕐 Current or custom date/time – see solar time for any moment

📐 Solar position – altitude, azimuth, declination, equation of time

🎨 ASCII Sundial – visual representation with shadow direction

🕒 Timezone & DST – adjust clock time to local solar time

🌈 Color output (optional) – highlight the shadow

📁 Export to CSV (optional)

⚡ No external API – all calculations are internal, using standard astronomical formulas

🧰 Supported Languages
Language	File	Dependencies (if any)
Python	sundial.py	colorama (optional)
Go	sundial.go	none (standard library)
JavaScript (Node)	sundial.js	chalk (optional)
Ruby	sundial.rb	colorize (optional)
PHP	sundial.php	none (extensions built-in)
Java	Sundial.java	none (Java 11+)
C#	Sundial.cs	none (.NET Core)
C++	sundial.cpp	libcurl (optional, not used) – no external deps
🚀 Quick Start
All implementations share the same CLI interface:

bash
# Compute solar time for current time at given location
<sundial> -lat 40.7128 -lon -74.0060

# Specify a date and time
<sundial> -lat 51.5074 -lon -0.1276 -d 2026-08-19 -t 14:30

# Set timezone offset (hours from UTC, default is system's offset)
<sundial> -lat 35.6895 -lon 139.6917 -tz 9

# Disable color
<sundial> -lat 40.7128 -lon -74.0060 --no-color

# Show help
<sundial> -h
Arguments:

-lat – latitude in degrees (positive North, required)

-lon – longitude in degrees (positive East, required)

-d – date in YYYY-MM-DD (default: today)

-t – time in HH:MM (default: current system time)

-tz – timezone offset in hours (default: system's offset)

--no-color – disable color output

📸 Example Output
text
☀️ Virtual Sundial
Location: 40.71°N, 74.01°W
Date: 2026-08-19 14:30 (UTC-4)
Solar Time: 14:28 (Equation: -2.5 min)
Solar Altitude: 55.3°
Solar Azimuth: 210.7° (South-West)

    ╭──────────╮
    │    *     │
    │   / \    │
    │  /   \   │
    │ /     \  │
    │/  SHADOW│
    ╰──────────╯
📁 Repository Structure
text
.
├── README.md
├── python/
│   └── sundial.py
├── go/
│   └── sundial.go
├── javascript/
│   └── sundial.js
├── ruby/
│   └── sundial.rb
├── php/
│   └── sundial.php
├── java/
│   └── Sundial.java
├── csharp/
│   └── Sundial.cs
└── cpp/
    └── sundial.cpp
