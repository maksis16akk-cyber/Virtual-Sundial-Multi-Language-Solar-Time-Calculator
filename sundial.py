# sundial.py
import sys
import math
import argparse
from datetime import datetime, timedelta, timezone
import time as systime

try:
    from colorama import init, Fore, Style
    init()
    COLORS = True
except ImportError:
    COLORS = False
    Fore = Style = type('', (), {'RESET_ALL':'', 'RED':'', 'GREEN':'', 'YELLOW':'', 'CYAN':'', 'BLUE':''})()

# Astronomical constants
DEG = math.pi / 180.0
RAD = 180.0 / math.pi

def solar_declination(day_of_year):
    """Compute solar declination in radians."""
    return 23.44 * DEG * math.sin((284 + day_of_year) * 360 * DEG / 365)

def equation_of_time(day_of_year):
    """Compute equation of time in minutes."""
    # B is in degrees
    B = (360.0 / 365) * (day_of_year - 81)
    B_rad = B * DEG
    return (9.87 * math.sin(2 * B_rad) - 7.53 * math.cos(B_rad) - 1.5 * math.sin(B_rad))

def solar_hour_angle(local_solar_time_hours):
    """Compute solar hour angle in radians from local solar time (0-24)."""
    return (local_solar_time_hours - 12) * 15 * DEG

def solar_altitude(lat_rad, dec_rad, ha_rad):
    """Compute solar altitude angle in radians."""
    return math.asin(math.sin(lat_rad) * math.sin(dec_rad) +
                     math.cos(lat_rad) * math.cos(dec_rad) * math.cos(ha_rad))

def solar_azimuth(lat_rad, dec_rad, ha_rad, alt_rad):
    """Compute solar azimuth angle in radians (clockwise from north)."""
    # Azimuth from south
    azi = math.atan2(math.sin(ha_rad),
                     math.cos(ha_rad) * math.sin(lat_rad) - math.tan(dec_rad) * math.cos(lat_rad))
    # Convert from south to north and to degrees
    return azi  # radians from north? Actually from south; we'll adjust.

def compute_solar_position(lat_deg, lon_deg, dt, tz_offset):
    """Compute solar altitude, azimuth, solar time, etc."""
    # Convert to radians
    lat_rad = lat_deg * DEG
    # Day of year
    day_of_year = dt.timetuple().tm_yday
    # Solar declination
    dec_rad = solar_declination(day_of_year)
    # Equation of time (minutes)
    eot = equation_of_time(day_of_year)
    # Time since midnight in hours (local mean time)
    hour_utc = dt.hour + dt.minute/60.0 + dt.second/3600.0
    # Local mean time
    local_mean_time = hour_utc + tz_offset
    # Solar time (hours)
    solar_time = local_mean_time + (4 * lon_deg) / 60.0 + eot / 60.0
    # Solar hour angle
    ha_rad = solar_hour_angle(solar_time)
    # Altitude
    alt_rad = solar_altitude(lat_rad, dec_rad, ha_rad)
    alt_deg = alt_rad * RAD
    # Azimuth (from north, clockwise)
    # formula: azimuth = atan2(-sin(ha)*cos(dec), sin(dec)*cos(lat) - cos(dec)*sin(lat)*cos(ha))
    azi_rad = math.atan2(-math.sin(ha_rad) * math.cos(dec_rad),
                         math.sin(dec_rad) * math.cos(lat_rad) -
                         math.cos(dec_rad) * math.sin(lat_rad) * math.cos(ha_rad))
    azi_deg = (azi_rad * RAD) % 360.0
    return {
        'altitude': alt_deg,
        'azimuth': azi_deg,
        'solar_time': solar_time,
        'eot': eot,
        'declination': dec_rad * RAD,
        'hour_angle': ha_rad * RAD
    }

def draw_sundial(azimuth_deg, use_color=True):
    """Draw an ASCII sundial with shadow direction."""
    # Approximate direction from azimuth (0=N, 90=E, 180=S, 270=W)
    # We'll draw a circle of radius 6 and a line from center in the direction
    # We'll map azimuth to coordinates in a grid (row, col)
    # Create a 13x13 grid (centered)
    size = 13
    half = size // 2
    grid = [[' ' for _ in range(size)] for _ in range(size)]
    # Draw circle outline
    for r in range(size):
        for c in range(size):
            dx = c - half
            dy = r - half
            dist = math.hypot(dx, dy)
            if abs(dist - half) < 0.5:
                grid[r][c] = '·'
    # Draw center
    grid[half][half] = '●'
    # Draw shadow line from center outward in azimuth direction
    # Azimuth is measured from north (up) clockwise; in screen coords, y is down.
    # We'll compute endpoint at radius 5 (inside circle)
    angle_rad = math.radians(azimuth_deg)
    # In screen: x = right, y = down; angle from north (up) clockwise: we need to rotate
    # standard: x = r*sin(θ), y = -r*cos(θ) where θ is from north clockwise
    end_r = half - 1
    dx = int(round(end_r * math.sin(angle_rad)))
    dy = int(round(-end_r * math.cos(angle_rad)))
    x2 = half + dx
    y2 = half + dy
    # Clamp
    x2 = max(0, min(size-1, x2))
    y2 = max(0, min(size-1, y2))
    # Draw line using Bresenham or simple stepping
    x0, y0 = half, half
    steps = max(abs(x2-x0), abs(y2-y0))
    if steps > 0:
        for i in range(1, steps+1):
            x = int(round(x0 + (x2-x0) * i / steps))
            y = int(round(y0 + (y2-y0) * i / steps))
            if 0 <= x < size and 0 <= y < size:
                if grid[y][x] == ' ' or grid[y][x] == '·':
                    grid[y][x] = '*' if use_color else '*'
        # mark endpoint
        if 0 <= y2 < size and 0 <= x2 < size:
            grid[y2][x2] = 'X' if use_color else 'X'
    # Print grid
    lines = []
    for row in grid:
        lines.append(''.join(row))
    return '\n'.join(lines)

def main():
    parser = argparse.ArgumentParser(description="Virtual Sundial")
    parser.add_argument('-lat', type=float, required=True, help="Latitude in degrees (positive North)")
    parser.add_argument('-lon', type=float, required=True, help="Longitude in degrees (positive East)")
    parser.add_argument('-d', '--date', help="Date YYYY-MM-DD (default: today)")
    parser.add_argument('-t', '--time', help="Time HH:MM (default: current system time)")
    parser.add_argument('-tz', type=float, help="Timezone offset in hours (default: system's)")
    parser.add_argument('--no-color', action='store_true', help="Disable color output")
    args = parser.parse_args()

    # Get current datetime
    now = datetime.now()
    if args.date:
        dt_date = datetime.strptime(args.date, '%Y-%m-%d').date()
    else:
        dt_date = now.date()
    if args.time:
        dt_time = datetime.strptime(args.time, '%H:%M').time()
    else:
        dt_time = now.time().replace(second=0, microsecond=0)
    dt = datetime.combine(dt_date, dt_time)

    # Timezone offset
    if args.tz is not None:
        tz_offset = args.tz
    else:
        # Use system's offset (local)
        tz_offset = -now.astimezone().utcoffset().total_seconds() / 3600.0

    # Compute solar position
    pos = compute_solar_position(args.lat, args.lon, dt, tz_offset)
    alt = pos['altitude']
    azi = pos['azimuth']
    solar_time = pos['solar_time']
    eot = pos['eot']

    # Determine direction names
    dir_names = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    idx = int(round((azi % 360) / 45)) % 8
    azi_dir = dir_names[idx]

    use_color = not args.no_color and COLORS

    # Output
    print("\n☀️ Virtual Sundial")
    lat_str = f"{abs(args.lat):.2f}°{'N' if args.lat>=0 else 'S'}"
    lon_str = f"{abs(args.lon):.2f}°{'E' if args.lon>=0 else 'W'}"
    print(f"Location: {lat_str}, {lon_str}")
    print(f"Date: {dt.strftime('%Y-%m-%d %H:%M')} (UTC{'+' if tz_offset>=0 else ''}{tz_offset:.1f})")
    solar_hours = int(solar_time)
    solar_min = int((solar_time - solar_hours) * 60)
    print(f"Solar Time: {solar_hours:02d}:{solar_min:02d} (Equation: {eot:+.1f} min)")
    print(f"Solar Altitude: {alt:.1f}°")
    print(f"Solar Azimuth: {azi:.1f}° ({azi_dir})")
    print("\n" + ("-"*20))
    # Draw sundial
    sundial = draw_sundial(azi, use_color)
    if use_color:
        # Colorize the shadow line
        # We'll replace '*' with Fore.YELLOW + '*' + Style.RESET_ALL, etc.
        # But we'll just print with color wrapper for the whole thing? Simple: just print
        pass
    print(sundial)
    print()

if __name__ == '__main__':
    main()
