# sundial.php
<?php
$DEG = M_PI / 180.0;
$RAD = 180.0 / M_PI;

function solarDeclination($dayOfYear) {
    global $DEG;
    return 23.44 * $DEG * sin((284 + $dayOfYear) * 360 * $DEG / 365);
}

function equationOfTime($dayOfYear) {
    global $DEG;
    $B = (360.0 / 365) * ($dayOfYear - 81);
    $B_rad = $B * $DEG;
    return 9.87 * sin(2 * $B_rad) - 7.53 * cos($B_rad) - 1.5 * sin($B_rad);
}

function solarHourAngle($solarTime) {
    global $DEG;
    return ($solarTime - 12) * 15 * $DEG;
}

function solarAltitude($lat, $dec, $ha) {
    return asin(sin($lat) * sin($dec) + cos($lat) * cos($dec) * cos($ha));
}

function computeSolarPosition($latDeg, $lonDeg, $dt, $tzOffset) {
    global $DEG, $RAD;
    $latRad = $latDeg * $DEG;
    $dayOfYear = (int)$dt->format('z') + 1;
    $decRad = solarDeclination($dayOfYear);
    $eot = equationOfTime($dayOfYear);

    $hourUTC = (float)$dt->format('G') + (float)$dt->format('i') / 60.0 + (float)$dt->format('s') / 3600.0;
    $localMeanTime = $hourUTC + $tzOffset;
    $solarTime = $localMeanTime + (4 * $lonDeg) / 60.0 + $eot / 60.0;
    $haRad = solarHourAngle($solarTime);
    $altRad = solarAltitude($latRad, $decRad, $haRad);
    $altDeg = $altRad * $RAD;

    $aziRad = atan2(-sin($haRad) * cos($decRad),
                    sin($decRad) * cos($latRad) - cos($decRad) * sin($latRad) * cos($haRad));
    $aziDeg = fmod($aziRad * $RAD + 360, 360);

    return [
        'altitude' => $altDeg,
        'azimuth' => $aziDeg,
        'solarTime' => $solarTime,
        'eot' => $eot,
        'declination' => $decRad * $RAD,
        'hourAngle' => $haRad * $RAD
    ];
}

function drawSundial($azimuthDeg) {
    $size = 13;
    $half = (int)($size / 2);
    $grid = array_fill(0, $size, array_fill(0, $size, ' '));
    for ($r = 0; $r < $size; $r++) {
        for ($c = 0; $c < $size; $c++) {
            $dx = $c - $half;
            $dy = $r - $half;
            $dist = hypot($dx, $dy);
            if (abs($dist - $half) < 0.5) {
                $grid[$r][$c] = '·';
            }
        }
    }
    $grid[$half][$half] = '●';
    $angleRad = $azimuthDeg * M_PI / 180.0;
    $endR = $half - 1;
    $dx = (int)round($endR * sin($angleRad));
    $dy = (int)round(-$endR * cos($angleRad));
    $x2 = $half + $dx;
    $y2 = $half + $dy;
    $x2 = max(0, min($size - 1, $x2));
    $y2 = max(0, min($size - 1, $y2));
    $x0 = $half;
    $y0 = $half;
    $steps = max(abs($x2 - $x0), abs($y2 - $y0));
    if ($steps > 0) {
        for ($i = 1; $i <= $steps; $i++) {
            $x = (int)round($x0 + ($x2 - $x0) * $i / $steps);
            $y = (int)round($y0 + ($y2 - $y0) * $i / $steps);
            if ($x >= 0 && $x < $size && $y >= 0 && $y < $size) {
                if ($grid[$y][$x] == ' ' || $grid[$y][$x] == '·') {
                    $grid[$y][$x] = '*';
                }
            }
        }
        if ($y2 >= 0 && $y2 < $size && $x2 >= 0 && $x2 < $size) {
            $grid[$y2][$x2] = 'X';
        }
    }
    $result = '';
    foreach ($grid as $row) {
        $result .= implode('', $row) . "\n";
    }
    return $result;
}

$opts = getopt("", ["lat:", "lon:", "d:", "t:", "tz:", "no-color"]);
if (!isset($opts['lat']) || !isset($opts['lon'])) {
    fwrite(STDERR, "Error: -lat and -lon required\n");
    exit(1);
}
$lat = (float)$opts['lat'];
$lon = (float)$opts['lon'];
$dateStr = $opts['d'] ?? null;
$timeStr = $opts['t'] ?? null;
$tzOffset = isset($opts['tz']) ? (float)$opts['tz'] : null;
$noColor = isset($opts['no-color']);

$now = new DateTime();
if ($dateStr) {
    $dt = new DateTime($dateStr);
    if ($timeStr) {
        list($h, $m) = explode(':', $timeStr);
        $dt->setTime((int)$h, (int)$m, 0);
    } else {
        $dt->setTime((int)$now->format('G'), (int)$now->format('i'), 0);
    }
} else {
    if ($timeStr) {
        list($h, $m) = explode(':', $timeStr);
        $dt = new DateTime();
        $dt->setTime((int)$h, (int)$m, 0);
    } else {
        $dt = $now;
    }
}
if ($tzOffset === null) {
    $tzOffset = -(int)$now->getOffset() / 3600.0;
}

$pos = computeSolarPosition($lat, $lon, $dt, $tzOffset);
$alt = $pos['altitude'];
$azi = $pos['azimuth'];
$solarTime = $pos['solarTime'];
$eot = $pos['eot'];

$dirNames = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
$idx = (int)round($azi / 45) % 8;
$aziDir = $dirNames[$idx];

$latStr = abs($lat) . '°' . ($lat >= 0 ? 'N' : 'S');
$lonStr = abs($lon) . '°' . ($lon >= 0 ? 'E' : 'W');
$tzSign = $tzOffset >= 0 ? '+' : '-';

echo "\n☀️ Virtual Sundial\n";
echo "Location: $latStr, $lonStr\n";
echo "Date: " . $dt->format('Y-m-d H:i') . " (UTC$tzSign" . abs($tzOffset) . ")\n";
$solarHours = (int)$solarTime;
$solarMin = (int)(($solarTime - $solarHours) * 60);
echo sprintf("Solar Time: %02d:%02d (Equation: %+.1f min)\n", $solarHours, $solarMin, $eot);
echo "Solar Altitude: " . round($alt, 1) . "°\n";
echo "Solar Azimuth: " . round($azi, 1) . "° ($aziDir)\n";
echo "\n" . str_repeat("-", 20) . "\n";
$sundial = drawSundial($azi);
if ($noColor) {
    echo $sundial;
} else {
    echo str_replace(['*', 'X'], ["\033[33m*\033[0m", "\033[32mX\033[0m"], $sundial);
}
echo "\n";
?>
