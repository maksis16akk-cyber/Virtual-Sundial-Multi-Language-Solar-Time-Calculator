// Sundial.cs
using System;
using System.Collections.Generic;

class Sundial
{
    const double DEG = Math.PI / 180.0;
    const double RAD = 180.0 / Math.PI;

    public class SolarPosition
    {
        public double altitude, azimuth, solarTime, eot, declination, hourAngle;
    }

    static double SolarDeclination(int dayOfYear) =>
        23.44 * DEG * Math.Sin((284 + dayOfYear) * 360 * DEG / 365);

    static double EquationOfTime(int dayOfYear)
    {
        double B = (360.0 / 365) * (dayOfYear - 81);
        double B_rad = B * DEG;
        return 9.87 * Math.Sin(2 * B_rad) - 7.53 * Math.Cos(B_rad) - 1.5 * Math.Sin(B_rad);
    }

    static double SolarHourAngle(double solarTime) => (solarTime - 12) * 15 * DEG;

    static double SolarAltitude(double lat, double dec, double ha) =>
        Math.Asin(Math.Sin(lat) * Math.Sin(dec) + Math.Cos(lat) * Math.Cos(dec) * Math.Cos(ha));

    static SolarPosition ComputeSolarPosition(double latDeg, double lonDeg, DateTime dt, double tzOffset)
    {
        double latRad = latDeg * DEG;
        int dayOfYear = dt.DayOfYear;
        double decRad = SolarDeclination(dayOfYear);
        double eot = EquationOfTime(dayOfYear);

        double hourUTC = dt.Hour + dt.Minute / 60.0 + dt.Second / 3600.0;
        double localMeanTime = hourUTC + tzOffset;
        double solarTime = localMeanTime + (4 * lonDeg) / 60.0 + eot / 60.0;
        double haRad = SolarHourAngle(solarTime);
        double altRad = SolarAltitude(latRad, decRad, haRad);
        double altDeg = altRad * RAD;

        double aziRad = Math.Atan2(-Math.Sin(haRad) * Math.Cos(decRad),
                                   Math.Sin(decRad) * Math.Cos(latRad) -
                                   Math.Cos(decRad) * Math.Sin(latRad) * Math.Cos(haRad));
        double aziDeg = (aziRad * RAD + 360) % 360;

        return new SolarPosition { altitude = altDeg, azimuth = aziDeg, solarTime = solarTime,
                                   eot = eot, declination = decRad * RAD, hourAngle = haRad * RAD };
    }

    static string DrawSundial(double azimuthDeg)
    {
        int size = 13;
        int half = size / 2;
        char[,] grid = new char[size, size];
        for (int r = 0; r < size; r++)
            for (int c = 0; c < size; c++)
                grid[r, c] = ' ';

        for (int r = 0; r < size; r++)
        {
            for (int c = 0; c < size; c++)
            {
                double dx = c - half;
                double dy = r - half;
                double dist = Math.Sqrt(dx * dx + dy * dy);
                if (Math.Abs(dist - half) < 0.5)
                    grid[r, c] = '·';
            }
        }
        grid[half, half] = '●';
        double angleRad = azimuthDeg * DEG;
        double endR = half - 1;
        int dx = (int)Math.Round(endR * Math.Sin(angleRad));
        int dy = (int)Math.Round(-endR * Math.Cos(angleRad));
        int x2 = half + dx;
        int y2 = half + dy;
        x2 = Math.Max(0, Math.Min(size - 1, x2));
        y2 = Math.Max(0, Math.Min(size - 1, y2));
        int x0 = half, y0 = half;
        int steps = Math.Max(Math.Abs(x2 - x0), Math.Abs(y2 - y0));
        if (steps > 0)
        {
            for (int i = 1; i <= steps; i++)
            {
                int x = (int)Math.Round(x0 + (x2 - x0) * (double)i / steps);
                int y = (int)Math.Round(y0 + (y2 - y0) * (double)i / steps);
                if (x >= 0 && x < size && y >= 0 && y < size)
                {
                    if (grid[y, x] == ' ' || grid[y, x] == '·')
                        grid[y, x] = '*';
                }
            }
            if (y2 >= 0 && y2 < size && x2 >= 0 && x2 < size)
                grid[y2, x2] = 'X';
        }
        var lines = new List<string>();
        for (int r = 0; r < size; r++)
        {
            char[] row = new char[size];
            for (int c = 0; c < size; c++) row[c] = grid[r, c];
            lines.Add(new string(row));
        }
        return string.Join("\n", lines);
    }

    static void Main(string[] args)
    {
        double lat = 0, lon = 0, tzOffset = 0;
        string dateStr = null, timeStr = null;
        bool noColor = false;

        for (int i = 0; i < args.Length; i++)
        {
            switch (args[i])
            {
                case "-lat": lat = double.Parse(args[++i]); break;
                case "-lon": lon = double.Parse(args[++i]); break;
                case "-d": dateStr = args[++i]; break;
                case "-t": timeStr = args[++i]; break;
                case "-tz": tzOffset = double.Parse(args[++i]); break;
                case "--no-color": noColor = true; break;
            }
        }
        if (lat == 0 && lon == 0)
        {
            Console.Error.WriteLine("Error: -lat and -lon required");
            return;
        }

        DateTime now = DateTime.Now;
        DateTime dt;
        if (dateStr != null)
        {
            DateTime date = DateTime.Parse(dateStr);
            if (timeStr != null)
            {
                DateTime time = DateTime.Parse(timeStr);
                dt = new DateTime(date.Year, date.Month, date.Day, time.Hour, time.Minute, 0);
            }
            else
            {
                dt = new DateTime(date.Year, date.Month, date.Day, now.Hour, now.Minute, 0);
            }
        }
        else
        {
            if (timeStr != null)
            {
                DateTime time = DateTime.Parse(timeStr);
                dt = new DateTime(now.Year, now.Month, now.Day, time.Hour, time.Minute, 0);
            }
            else
            {
                dt = now;
            }
        }
        if (tzOffset == 0)
        {
            tzOffset = -TimeZoneInfo.Local.GetUtcOffset(DateTime.UtcNow).TotalHours;
        }

        SolarPosition pos = ComputeSolarPosition(lat, lon, dt, tzOffset);
        double alt = pos.altitude;
        double azi = pos.azimuth;
        double solarTime = pos.solarTime;
        double eot = pos.eot;

        string[] dirNames = { "N", "NE", "E", "SE", "S", "SW", "W", "NW" };
        int idx = (int)Math.Round(azi / 45) % 8;
        string aziDir = dirNames[idx];

        string latStr = $"{Math.Abs(lat):F2}°{(lat >= 0 ? 'N' : 'S')}";
        string lonStr = $"{Math.Abs(lon):F2}°{(lon >= 0 ? 'E' : 'W')}";
        char tzSign = tzOffset >= 0 ? '+' : '-';

        Console.WriteLine("\n☀️ Virtual Sundial");
        Console.WriteLine($"Location: {latStr}, {lonStr}");
        Console.WriteLine($"Date: {dt:yyyy-MM-dd HH:mm} (UTC{tzSign}{Math.Abs(tzOffset):F1})");
        int solarHours = (int)solarTime;
        int solarMin = (int)Math.Round((solarTime - solarHours) * 60);
        Console.WriteLine($"Solar Time: {solarHours:D2}:{solarMin:D2} (Equation: {eot:+0.0;-0.0} min)");
        Console.WriteLine($"Solar Altitude: {alt:F1}°");
        Console.WriteLine($"Solar Azimuth: {azi:F1}° ({aziDir})");
        Console.WriteLine("\n" + new string('-', 20));
        string sundial = DrawSundial(azi);
        if (noColor)
            Console.Write(sundial);
        else
            Console.Write(sundial.Replace("*", "\u001b[33m*\u001b[0m").Replace("X", "\u001b[32mX\u001b[0m"));
        Console.WriteLine();
    }
}
