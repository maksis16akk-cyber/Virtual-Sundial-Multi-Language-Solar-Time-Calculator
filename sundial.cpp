// sundial.cpp
#include <iostream>
#include <cmath>
#include <string>
#include <vector>
#include <ctime>
#include <iomanip>
#include <sstream>
#include <algorithm>

const double DEG = M_PI / 180.0;
const double RAD = 180.0 / M_PI;

double solarDeclination(int dayOfYear) {
    return 23.44 * DEG * sin((284 + dayOfYear) * 360 * DEG / 365);
}

double equationOfTime(int dayOfYear) {
    double B = (360.0 / 365) * (dayOfYear - 81);
    double B_rad = B * DEG;
    return 9.87 * sin(2 * B_rad) - 7.53 * cos(B_rad) - 1.5 * sin(B_rad);
}

double solarHourAngle(double solarTime) {
    return (solarTime - 12) * 15 * DEG;
}

double solarAltitude(double lat, double dec, double ha) {
    return asin(sin(lat) * sin(dec) + cos(lat) * cos(dec) * cos(ha));
}

struct SolarPosition {
    double altitude, azimuth, solarTime, eot, declination, hourAngle;
};

SolarPosition computeSolarPosition(double latDeg, double lonDeg, std::tm dt, double tzOffset) {
    double latRad = latDeg * DEG;
    int dayOfYear = dt.tm_yday + 1; // tm_yday is 0-based
    double decRad = solarDeclination(dayOfYear);
    double eot = equationOfTime(dayOfYear);

    double hourUTC = dt.tm_hour + dt.tm_min / 60.0 + dt.tm_sec / 3600.0;
    double localMeanTime = hourUTC + tzOffset;
    double solarTime = localMeanTime + (4 * lonDeg) / 60.0 + eot / 60.0;
    double haRad = solarHourAngle(solarTime);
    double altRad = solarAltitude(latRad, decRad, haRad);
    double altDeg = altRad * RAD;

    double aziRad = atan2(-sin(haRad) * cos(decRad),
                          sin(decRad) * cos(latRad) - cos(decRad) * sin(latRad) * cos(haRad));
    double aziDeg = fmod(aziRad * RAD + 360, 360);

    return {altDeg, aziDeg, solarTime, eot, decRad * RAD, haRad * RAD};
}

std::string drawSundial(double azimuthDeg) {
    int size = 13;
    int half = size / 2;
    std::vector<std::vector<char>> grid(size, std::vector<char>(size, ' '));
    for (int r = 0; r < size; r++) {
        for (int c = 0; c < size; c++) {
            double dx = c - half;
            double dy = r - half;
            double dist = hypot(dx, dy);
            if (std::abs(dist - half) < 0.5) {
                grid[r][c] = '·';
            }
        }
    }
    grid[half][half] = '●';
    double angleRad = azimuthDeg * DEG;
    double endR = half - 1;
    int dx = (int)round(endR * sin(angleRad));
    int dy = (int)round(-endR * cos(angleRad));
    int x2 = half + dx;
    int y2 = half + dy;
    x2 = std::max(0, std::min(size - 1, x2));
    y2 = std::max(0, std::min(size - 1, y2));
    int x0 = half, y0 = half;
    int steps = std::max(std::abs(x2 - x0), std::abs(y2 - y0));
    if (steps > 0) {
        for (int i = 1; i <= steps; i++) {
            int x = (int)round(x0 + (x2 - x0) * (double)i / steps);
            int y = (int)round(y0 + (y2 - y0) * (double)i / steps);
            if (x >= 0 && x < size && y >= 0 && y < size) {
                if (grid[y][x] == ' ' || grid[y][x] == '·') {
                    grid[y][x] = '*';
                }
            }
        }
        if (y2 >= 0 && y2 < size && x2 >= 0 && x2 < size) {
            grid[y2][x2] = 'X';
        }
    }
    std::string result;
    for (const auto& row : grid) {
        result += std::string(row.begin(), row.end()) + "\n";
    }
    return result;
}

int main(int argc, char* argv[]) {
    double lat = 0, lon = 0, tzOffset = 0;
    std::string dateStr, timeStr;
    bool noColor = false;

    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];
        if (arg == "-lat" && i+1 < argc) lat = std::stod(argv[++i]);
        else if (arg == "-lon" && i+1 < argc) lon = std::stod(argv[++i]);
        else if (arg == "-d" && i+1 < argc) dateStr = argv[++i];
        else if (arg == "-t" && i+1 < argc) timeStr = argv[++i];
        else if (arg == "-tz" && i+1 < argc) tzOffset = std::stod(argv[++i]);
        else if (arg == "--no-color") noColor = true;
        else if (arg == "-h") { std::cout << "Usage: ...\n"; return 0; }
    }
    if (lat == 0 && lon == 0) {
        std::cerr << "Error: -lat and -lon required\n";
        return 1;
    }

    time_t t = time(nullptr);
    std::tm now = *localtime(&t);
    std::tm dt = now;
    if (!dateStr.empty()) {
        std::tm date = {};
        std::stringstream ss(dateStr);
        ss >> std::get_time(&date, "%Y-%m-%d");
        if (ss.fail()) { std::cerr << "Invalid date\n"; return 1; }
        dt.tm_year = date.tm_year;
        dt.tm_mon = date.tm_mon;
        dt.tm_mday = date.tm_mday;
    }
    if (!timeStr.empty()) {
        std::tm time = {};
        std::stringstream ss2(timeStr);
        ss2 >> std::get_time(&time, "%H:%M");
        if (ss2.fail()) { std::cerr << "Invalid time\n"; return 1; }
        dt.tm_hour = time.tm_hour;
        dt.tm_min = time.tm_min;
        dt.tm_sec = 0;
    } else {
        dt.tm_hour = now.tm_hour;
        dt.tm_min = now.tm_min;
        dt.tm_sec = 0;
    }
    if (tzOffset == 0) {
        tzOffset = -now.tm_gmtoff / 3600.0;
    }

    SolarPosition pos = computeSolarPosition(lat, lon, dt, tzOffset);
    double alt = pos.altitude;
    double azi = pos.azimuth;
    double solarTime = pos.solarTime;
    double eot = pos.eot;

    const std::string dirNames[] = {"N", "NE", "E", "SE", "S", "SW", "W", "NW"};
    int idx = (int)round(azi / 45) % 8;
    std::string aziDir = dirNames[idx];

    std::string latStr = std::to_string(std::abs(lat)).substr(0,6) + "°" + (lat >= 0 ? "N" : "S");
    std::string lonStr = std::to_string(std::abs(lon)).substr(0,6) + "°" + (lon >= 0 ? "E" : "W");
    char tzSign = tzOffset >= 0 ? '+' : '-';

    std::cout << "\n☀️ Virtual Sundial\n";
    std::cout << "Location: " << latStr << ", " << lonStr << "\n";
    char buf[20];
    strftime(buf, sizeof(buf), "%Y-%m-%d %H:%M", &dt);
    std::cout << "Date: " << buf << " (UTC" << tzSign << std::abs(tzOffset) << ")\n";
    int solarHours = (int)solarTime;
    int solarMin = (int)round((solarTime - solarHours) * 60);
    std::cout << "Solar Time: " << std::setw(2) << std::setfill('0') << solarHours << ":"
              << std::setw(2) << std::setfill('0') << solarMin
              << " (Equation: " << std::showpos << eot << std::noshowpos << " min)\n";
    std::cout << "Solar Altitude: " << alt << "°\n";
    std::cout << "Solar Azimuth: " << azi << "° (" << aziDir << ")\n";
    std::cout << "\n" << std::string(20, '-') << "\n";
    std::string sundial = drawSundial(azi);
    if (noColor) {
        std::cout << sundial;
    } else {
        // Replace * with ANSI yellow, X with green
        size_t pos2 = 0;
        while ((pos2 = sundial.find('*', pos2)) != std::string::npos) {
            sundial.replace(pos2, 1, "\033[33m*\033[0m");
            pos2 += 11;
        }
        pos2 = 0;
        while ((pos2 = sundial.find('X', pos2)) != std::string::npos) {
            sundial.replace(pos2, 1, "\033[32mX\033[0m");
            pos2 += 11;
        }
        std::cout << sundial;
    }
    std::cout << "\n";
    return 0;
}
