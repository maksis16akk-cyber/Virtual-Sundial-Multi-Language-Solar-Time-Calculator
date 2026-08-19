// Sundial.java
import java.time.*;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoField;

public class Sundial {
    private static final double DEG = Math.PI / 180.0;
    private static final double RAD = 180.0 / Math.PI;

    public static class SolarPosition {
        public double altitude, azimuth, solarTime, eot, declination, hourAngle;
    }

    public static double solarDeclination(int dayOfYear) {
        return 23.44 * DEG * Math.sin((284 + dayOfYear) * 360 * DEG / 365);
    }

    public static double equationOfTime(int dayOfYear) {
        double B = (360.0 / 365) * (dayOfYear - 81);
        double B_rad = B * DEG;
        return 9.87 * Math.sin(2 * B_rad) - 7.53 * Math.cos(B_rad) - 1.5 * Math.sin(B_rad);
    }

    public static double solarHourAngle(double solarTime) {
        return (solarTime - 12) * 15 * DEG;
    }

    public static double solarAltitude(double lat, double dec, double ha) {
        return Math.asin(Math.sin(lat) * Math.sin(dec) + Math.cos(lat) * Math.cos(dec) * Math.cos(ha));
    }

    public static SolarPosition computeSolarPosition(double latDeg, double lonDeg, LocalDateTime dt, double tzOffset) {
        double latRad = latDeg * DEG;
        int dayOfYear = dt.getDayOfYear();
        double decRad = solarDeclination(dayOfYear);
        double eot = equationOfTime(dayOfYear);

        double hourUTC = dt.getHour() + dt.getMinute() / 60.0 + dt.getSecond() / 3600.0;
        double localMeanTime = hourUTC + tzOffset;
        double solarTime = localMeanTime + (4 * lonDeg) / 60.0 + eot / 60.0;
        double haRad = solarHourAngle(solarTime);
        double altRad = solarAltitude(latRad, decRad, haRad);
        double altDeg = altRad * RAD;

        double aziRad = Math.atan2(-Math.sin(haRad) * Math.cos(decRad),
                Math.sin(decRad) * Math.cos(latRad) - Math.cos(decRad) * Math.sin(latRad) * Math.cos(haRad));
        double aziDeg = (aziRad * RAD + 360) % 360;

        SolarPosition pos = new SolarPosition();
        pos.altitude = altDeg;
        pos.azimuth = aziDeg;
        pos.solarTime = solarTime;
        pos.eot = eot;
        pos.declination = decRad * RAD;
        pos.hourAngle = haRad * RAD;
        return pos;
    }

    public static String drawSundial(double azimuthDeg) {
        int size = 13;
        int half = size / 2;
        char[][] grid = new char[size][size];
        for (int r = 0; r < size; r++) {
            for (int c = 0; c < size; c++) {
                grid[r][c] = ' ';
            }
        }
        for (int r = 0; r < size; r++) {
            for (int c = 0; c < size; c++) {
                double dx = c - half;
                double dy = r - half;
                double dist = Math.hypot(dx, dy);
                if (Math.abs(dist - half) < 0.5) {
                    grid[r][c] = '·';
                }
            }
        }
        grid[half][half] = '●';
        double angleRad = azimuthDeg * DEG;
        double endR = half - 1;
        int dx = (int)Math.round(endR * Math.sin(angleRad));
        int dy = (int)Math.round(-endR * Math.cos(angleRad));
        int x2 = half + dx;
        int y2 = half + dy;
        x2 = Math.max(0, Math.min(size - 1, x2));
        y2 = Math.max(0, Math.min(size - 1, y2));
        int x0 = half, y0 = half;
        int steps = Math.max(Math.abs(x2 - x0), Math.abs(y2 - y0));
        if (steps > 0) {
            for (int i = 1; i <= steps; i++) {
                int x = (int)Math.round(x0 + (x2 - x0) * (double)i / steps);
                int y = (int)Math.round(y0 + (y2 - y0) * (double)i / steps);
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
        StringBuilder sb = new StringBuilder();
        for (char[] row : grid) {
            sb.append(new String(row)).append("\n");
        }
        return sb.toString();
    }

    public static void main(String[] args) {
        double lat = 0, lon = 0, tzOffset = 0;
        String dateStr = null, timeStr = null;
        boolean noColor = false;

        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "-lat": lat = Double.parseDouble(args[++i]); break;
                case "-lon": lon = Double.parseDouble(args[++i]); break;
                case "-d": dateStr = args[++i]; break;
                case "-t": timeStr = args[++i]; break;
                case "-tz": tzOffset = Double.parseDouble(args[++i]); break;
                case "--no-color": noColor = true; break;
                case "-h": System.out.println("Usage: ..."); return;
            }
        }
        if (lat == 0 && lon == 0) {
            System.err.println("Error: -lat and -lon required");
            System.exit(1);
        }

        LocalDateTime now = LocalDateTime.now();
        LocalDateTime dt;
        if (dateStr != null) {
            LocalDate date = LocalDate.parse(dateStr);
            if (timeStr != null) {
                LocalTime time = LocalTime.parse(timeStr + ":00");
                dt = LocalDateTime.of(date, time);
            } else {
                dt = LocalDateTime.of(date, now.toLocalTime());
            }
        } else {
            if (timeStr != null) {
                LocalTime time = LocalTime.parse(timeStr + ":00");
                dt = LocalDateTime.of(now.toLocalDate(), time);
            } else {
                dt = now;
            }
        }
        if (tzOffset == 0) {
            tzOffset = -ZoneOffset.systemDefault().getRules().getOffset(Instant.now()).getTotalSeconds() / 3600.0;
        }

        SolarPosition pos = computeSolarPosition(lat, lon, dt, tzOffset);
        double alt = pos.altitude;
        double azi = pos.azimuth;
        double solarTime = pos.solarTime;
        double eot = pos.eot;

        String[] dirNames = {"N", "NE", "E", "SE", "S", "SW", "W", "NW"};
        int idx = (int)Math.round(azi / 45) % 8;
        String aziDir = dirNames[idx];

        String latStr = String.format("%.2f°%c", Math.abs(lat), lat >= 0 ? 'N' : 'S');
        String lonStr = String.format("%.2f°%c", Math.abs(lon), lon >= 0 ? 'E' : 'W');
        char tzSign = tzOffset >= 0 ? '+' : '-';

        System.out.println("\n☀️ Virtual Sundial");
        System.out.println("Location: " + latStr + ", " + lonStr);
        System.out.printf("Date: %s (UTC%c%.1f)%n", dt.format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm")), tzSign, Math.abs(tzOffset));
        int solarHours = (int)solarTime;
        int solarMin = (int)Math.round((solarTime - solarHours) * 60);
        System.out.printf("Solar Time: %02d:%02d (Equation: %+.1f min)%n", solarHours, solarMin, eot);
        System.out.printf("Solar Altitude: %.1f°%n", alt);
        System.out.printf("Solar Azimuth: %.1f° (%s)%n", azi, aziDir);
        System.out.println("\n" + "--------------------");
        String sundial = drawSundial(azi);
        if (noColor) {
            System.out.print(sundial);
        } else {
            // Color: replace * with ANSI yellow, X with green
            System.out.print(sundial.replace("*", "\u001B[33m*\u001B[0m").replace("X", "\u001B[32mX\u001B[0m"));
        }
        System.out.println();
    }
}
