// sundial.js
const chalk = require('chalk');
const yargs = require('yargs/yargs');
const { hideBin } = require('yargs/helpers');

const DEG = Math.PI / 180;
const RAD = 180 / Math.PI;

function solarDeclination(dayOfYear) {
    return 23.44 * DEG * Math.sin((284 + dayOfYear) * 360 * DEG / 365);
}

function equationOfTime(dayOfYear) {
    const B = (360.0 / 365) * (dayOfYear - 81);
    const B_rad = B * DEG;
    return 9.87 * Math.sin(2 * B_rad) - 7.53 * Math.cos(B_rad) - 1.5 * Math.sin(B_rad);
}

function solarHourAngle(solarTime) {
    return (solarTime - 12) * 15 * DEG;
}

function solarAltitude(lat, dec, ha) {
    return Math.asin(Math.sin(lat) * Math.sin(dec) + Math.cos(lat) * Math.cos(dec) * Math.cos(ha));
}

function computeSolarPosition(latDeg, lonDeg, dt, tzOffset) {
    const latRad = latDeg * DEG;
    const dayOfYear = Math.floor((dt - new Date(dt.getFullYear(), 0, 0)) / (1000 * 60 * 60 * 24));
    const decRad = solarDeclination(dayOfYear);
    const eot = equationOfTime(dayOfYear);

    const hourUTC = dt.getHours() + dt.getMinutes() / 60 + dt.getSeconds() / 3600;
    const localMeanTime = hourUTC + tzOffset;
    const solarTime = localMeanTime + (4 * lonDeg) / 60 + eot / 60;
    const haRad = solarHourAngle(solarTime);
    const altRad = solarAltitude(latRad, decRad, haRad);
    const altDeg = altRad * RAD;

    const aziRad = Math.atan2(-Math.sin(haRad) * Math.cos(decRad),
                              Math.sin(decRad) * Math.cos(latRad) -
                              Math.cos(decRad) * Math.sin(latRad) * Math.cos(haRad));
    const aziDeg = (aziRad * RAD + 360) % 360;

    return {
        altitude: altDeg,
        azimuth: aziDeg,
        solarTime: solarTime,
        eot: eot,
        declination: decRad * RAD,
        hourAngle: haRad * RAD
    };
}

function drawSundial(azimuthDeg) {
    const size = 13;
    const half = Math.floor(size / 2);
    const grid = Array.from({ length: size }, () => Array(size).fill(' '));
    for (let r = 0; r < size; r++) {
        for (let c = 0; c < size; c++) {
            const dx = c - half;
            const dy = r - half;
            const dist = Math.hypot(dx, dy);
            if (Math.abs(dist - half) < 0.5) {
                grid[r][c] = '·';
            }
        }
    }
    grid[half][half] = '●';
    const angleRad = azimuthDeg * DEG;
    const endR = half - 1;
    const dx = Math.round(endR * Math.sin(angleRad));
    const dy = Math.round(-endR * Math.cos(angleRad));
    let x2 = half + dx;
    let y2 = half + dy;
    x2 = Math.max(0, Math.min(size - 1, x2));
    y2 = Math.max(0, Math.min(size - 1, y2));
    const x0 = half, y0 = half;
    const steps = Math.max(Math.abs(x2 - x0), Math.abs(y2 - y0));
    if (steps > 0) {
        for (let i = 1; i <= steps; i++) {
            const x = Math.round(x0 + (x2 - x0) * i / steps);
            const y = Math.round(y0 + (y2 - y0) * i / steps);
            if (x >= 0 && x < size && y >= 0 && y < size) {
                if (grid[y][x] === ' ' || grid[y][x] === '·') {
                    grid[y][x] = '*';
                }
            }
        }
        if (y2 >= 0 && y2 < size && x2 >= 0 && x2 < size) {
            grid[y2][x2] = 'X';
        }
    }
    return grid.map(row => row.join('')).join('\n');
}

async function main() {
    const argv = yargs(hideBin(process.argv))
        .option('lat', { type: 'number', demandOption: true, description: 'Latitude in degrees (positive North)' })
        .option('lon', { type: 'number', demandOption: true, description: 'Longitude in degrees (positive East)' })
        .option('d', { type: 'string', description: 'Date YYYY-MM-DD' })
        .option('t', { type: 'string', description: 'Time HH:MM' })
        .option('tz', { type: 'number', description: 'Timezone offset in hours' })
        .option('no-color', { type: 'boolean', description: 'Disable color', default: false })
        .argv;

    const now = new Date();
    let dt = new Date(now);
    if (argv.d) {
        const parts = argv.d.split('-').map(Number);
        dt.setFullYear(parts[0], parts[1]-1, parts[2]);
    }
    if (argv.t) {
        const [h, m] = argv.t.split(':').map(Number);
        dt.setHours(h, m, 0, 0);
    } else {
        dt.setHours(now.getHours(), now.getMinutes(), 0, 0);
    }
    let tzOffset = argv.tz;
    if (tzOffset === undefined) {
        tzOffset = -now.getTimezoneOffset() / 60;
    }

    const pos = computeSolarPosition(argv.lat, argv.lon, dt, tzOffset);
    const alt = pos.altitude;
    const azi = pos.azimuth;
    const solarTime = pos.solarTime;
    const eot = pos.eot;

    const dirNames = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
    const idx = Math.round(azi / 45) % 8;
    const aziDir = dirNames[idx];

    const latStr = `${Math.abs(argv.lat).toFixed(2)}°${argv.lat >= 0 ? 'N' : 'S'}`;
    const lonStr = `${Math.abs(argv.lon).toFixed(2)}°${argv.lon >= 0 ? 'E' : 'W'}`;
    const tzSign = tzOffset >= 0 ? '+' : '-';
    console.log(`\n☀️ Virtual Sundial`);
    console.log(`Location: ${latStr}, ${lonStr}`);
    console.log(`Date: ${dt.toISOString().slice(0,16).replace('T',' ')} (UTC${tzSign}${Math.abs(tzOffset).toFixed(1)})`);
    const solarHours = Math.floor(solarTime);
    const solarMin = Math.round((solarTime - solarHours) * 60);
    console.log(`Solar Time: ${String(solarHours).padStart(2,'0')}:${String(solarMin).padStart(2,'0')} (Equation: ${eot >= 0 ? '+' : ''}${eot.toFixed(1)} min)`);
    console.log(`Solar Altitude: ${alt.toFixed(1)}°`);
    console.log(`Solar Azimuth: ${azi.toFixed(1)}° (${aziDir})`);
    console.log('\n' + '--------------------');
    const sundial = drawSundial(azi);
    if (!argv['no-color']) {
        // Simple colorization: replace '*' with chalk.yellow('*') etc.
        const colored = sundial.replace(/\*/g, chalk.yellow('*')).replace(/X/g, chalk.green('X'));
        console.log(colored);
    } else {
        console.log(sundial);
    }
    console.log();
}

main().catch(console.error);
