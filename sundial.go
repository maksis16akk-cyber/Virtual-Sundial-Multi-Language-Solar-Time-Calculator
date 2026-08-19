// sundial.go
package main

import (
	"flag"
	"fmt"
	"math"
	"os"
	"strconv"
	"time"
)

const (
	DEG = math.Pi / 180.0
	RAD = 180.0 / math.Pi
)

type SolarPosition struct {
	Altitude    float64
	Azimuth     float64
	SolarTime   float64
	EOT         float64
	Declination float64
	HourAngle   float64
}

func solarDeclination(dayOfYear int) float64 {
	return 23.44 * DEG * math.Sin((284+dayOfYear)*360*DEG/365)
}

func equationOfTime(dayOfYear int) float64 {
	B := (360.0 / 365) * float64(dayOfYear-81)
	B_rad := B * DEG
	return 9.87*math.Sin(2*B_rad) - 7.53*math.Cos(B_rad) - 1.5*math.Sin(B_rad)
}

func solarHourAngle(solarTime float64) float64 {
	return (solarTime - 12) * 15 * DEG
}

func solarAltitude(lat, dec, ha float64) float64 {
	return math.Asin(math.Sin(lat)*math.Sin(dec) + math.Cos(lat)*math.Cos(dec)*math.Cos(ha))
}

func computeSolarPosition(latDeg, lonDeg float64, t time.Time, tzOffset float64) SolarPosition {
	latRad := latDeg * DEG
	dayOfYear := t.YearDay()
	decRad := solarDeclination(dayOfYear)
	eot := equationOfTime(dayOfYear)

	hourUTC := float64(t.Hour()) + float64(t.Minute())/60.0 + float64(t.Second())/3600.0
	localMeanTime := hourUTC + tzOffset
	solarTime := localMeanTime + (4*lonDeg)/60.0 + eot/60.0
	haRad := solarHourAngle(solarTime)
	altRad := solarAltitude(latRad, decRad, haRad)
	altDeg := altRad * RAD

	// Azimuth from north
	aziRad := math.Atan2(-math.Sin(haRad)*math.Cos(decRad),
		math.Sin(decRad)*math.Cos(latRad)-math.Cos(decRad)*math.Sin(latRad)*math.Cos(haRad))
	aziDeg := math.Mod(aziRad*RAD+360, 360)

	return SolarPosition{
		Altitude:    altDeg,
		Azimuth:     aziDeg,
		SolarTime:   solarTime,
		EOT:         eot,
		Declination: decRad * RAD,
		HourAngle:   haRad * RAD,
	}
}

func drawSundial(azimuthDeg float64) string {
	size := 13
	half := size / 2
	grid := make([][]rune, size)
	for i := range grid {
		grid[i] = make([]rune, size)
		for j := range grid[i] {
			grid[i][j] = ' '
		}
	}
	// Circle outline
	for r := 0; r < size; r++ {
		for c := 0; c < size; c++ {
			dx := float64(c - half)
			dy := float64(r - half)
			dist := math.Hypot(dx, dy)
			if math.Abs(dist-float64(half)) < 0.5 {
				grid[r][c] = '·'
			}
		}
	}
	grid[half][half] = '●'
	// Shadow line
	angleRad := azimuthDeg * DEG
	endR := half - 1
	dx := int(math.Round(float64(endR) * math.Sin(angleRad)))
	dy := int(math.Round(-float64(endR) * math.Cos(angleRad)))
	x2 := half + dx
	y2 := half + dy
	if x2 < 0 {
		x2 = 0
	}
	if x2 >= size {
		x2 = size - 1
	}
	if y2 < 0 {
		y2 = 0
	}
	if y2 >= size {
		y2 = size - 1
	}
	x0, y0 := half, half
	steps := max(abs(x2-x0), abs(y2-y0))
	if steps > 0 {
		for i := 1; i <= steps; i++ {
			x := int(math.Round(float64(x0) + float64(x2-x0)*float64(i)/float64(steps)))
			y := int(math.Round(float64(y0) + float64(y2-y0)*float64(i)/float64(steps)))
			if x >= 0 && x < size && y >= 0 && y < size {
				if grid[y][x] == ' ' || grid[y][x] == '·' {
					grid[y][x] = '*'
				}
			}
		}
		if y2 >= 0 && y2 < size && x2 >= 0 && x2 < size {
			grid[y2][x2] = 'X'
		}
	}
	// Build string
	var result string
	for _, row := range grid {
		result += string(row) + "\n"
	}
	return result
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}

func abs(a int) int {
	if a < 0 {
		return -a
	}
	return a
}

func main() {
	latPtr := flag.Float64("lat", 0, "Latitude in degrees (positive North)")
	lonPtr := flag.Float64("lon", 0, "Longitude in degrees (positive East)")
	datePtr := flag.String("d", "", "Date YYYY-MM-DD")
	timePtr := flag.String("t", "", "Time HH:MM")
	tzPtr := flag.Float64("tz", 0, "Timezone offset in hours")
	noColor := flag.Bool("no-color", false, "Disable color")
	flag.Parse()

	if *latPtr == 0 && *lonPtr == 0 {
		fmt.Fprintln(os.Stderr, "Error: -lat and -lon required")
		os.Exit(1)
	}

	now := time.Now()
	var t time.Time
	if *datePtr != "" {
		date, err := time.Parse("2006-01-02", *datePtr)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Invalid date: %v\n", err)
			os.Exit(1)
		}
		if *timePtr != "" {
			timePart, err := time.Parse("15:04", *timePtr)
			if err != nil {
				fmt.Fprintf(os.Stderr, "Invalid time: %v\n", err)
				os.Exit(1)
			}
			t = time.Date(date.Year(), date.Month(), date.Day(),
				timePart.Hour(), timePart.Minute(), 0, 0, time.UTC)
		} else {
			t = time.Date(date.Year(), date.Month(), date.Day(),
				now.Hour(), now.Minute(), now.Second(), 0, time.UTC)
		}
	} else {
		if *timePtr != "" {
			timePart, err := time.Parse("15:04", *timePtr)
			if err != nil {
				fmt.Fprintf(os.Stderr, "Invalid time: %v\n", err)
				os.Exit(1)
			}
			t = time.Date(now.Year(), now.Month(), now.Day(),
				timePart.Hour(), timePart.Minute(), 0, 0, time.UTC)
		} else {
			t = now
		}
	}

	tzOffset := *tzPtr
	if tzOffset == 0 {
		// Use system's offset from UTC
		_, offset := now.Zone()
		tzOffset = -float64(offset) / 3600.0
	}

	pos := computeSolarPosition(*latPtr, *lonPtr, t, tzOffset)
	alt := pos.Altitude
	azi := pos.Azimuth
	solarTime := pos.SolarTime
	eot := pos.EOT

	dirNames := []string{"N", "NE", "E", "SE", "S", "SW", "W", "NW"}
	idx := int(math.Round(azi/45)) % 8
	aziDir := dirNames[idx]

	fmt.Println("\n☀️ Virtual Sundial")
	latStr := fmt.Sprintf("%.2f°%c", math.Abs(*latPtr), 'N')
	if *latPtr < 0 {
		latStr = fmt.Sprintf("%.2f°%c", math.Abs(*latPtr), 'S')
	}
	lonStr := fmt.Sprintf("%.2f°%c", math.Abs(*lonPtr), 'E')
	if *lonPtr < 0 {
		lonStr = fmt.Sprintf("%.2f°%c", math.Abs(*lonPtr), 'W')
	}
	fmt.Printf("Location: %s, %s\n", latStr, lonStr)
	tzSign := '+'
	if tzOffset < 0 {
		tzSign = '-'
	}
	fmt.Printf("Date: %s (UTC%c%.1f)\n", t.Format("2006-01-02 15:04"), tzSign, math.Abs(tzOffset))
	solarHours := int(solarTime)
	solarMin := int((solarTime - float64(solarHours)) * 60)
	fmt.Printf("Solar Time: %02d:%02d (Equation: %+.1f min)\n", solarHours, solarMin, eot)
	fmt.Printf("Solar Altitude: %.1f°\n", alt)
	fmt.Printf("Solar Azimuth: %.1f° (%s)\n", azi, aziDir)
	fmt.Println("\n" + "--------------------")
	fmt.Println(drawSundial(azi))
}
