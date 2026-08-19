# sundial.rb
require 'optparse'
require 'date'
require 'time'

DEG = Math::PI / 180.0
RAD = 180.0 / Math::PI

def solar_declination(day_of_year)
  23.44 * DEG * Math.sin((284 + day_of_year) * 360 * DEG / 365)
end

def equation_of_time(day_of_year)
  b = (360.0 / 365) * (day_of_year - 81)
  b_rad = b * DEG
  9.87 * Math.sin(2 * b_rad) - 7.53 * Math.cos(b_rad) - 1.5 * Math.sin(b_rad)
end

def solar_hour_angle(solar_time)
  (solar_time - 12) * 15 * DEG
end

def solar_altitude(lat, dec, ha)
  Math.asin(Math.sin(lat) * Math.sin(dec) + Math.cos(lat) * Math.cos(dec) * Math.cos(ha))
end

def compute_solar_position(lat_deg, lon_deg, dt, tz_offset)
  lat_rad = lat_deg * DEG
  day_of_year = dt.yday
  dec_rad = solar_declination(day_of_year)
  eot = equation_of_time(day_of_year)

  hour_utc = dt.hour + dt.min / 60.0 + dt.sec / 3600.0
  local_mean_time = hour_utc + tz_offset
  solar_time = local_mean_time + (4 * lon_deg) / 60.0 + eot / 60.0
  ha_rad = solar_hour_angle(solar_time)
  alt_rad = solar_altitude(lat_rad, dec_rad, ha_rad)
  alt_deg = alt_rad * RAD

  azi_rad = Math.atan2(-Math.sin(ha_rad) * Math.cos(dec_rad),
                       Math.sin(dec_rad) * Math.cos(lat_rad) -
                       Math.cos(dec_rad) * Math.sin(lat_rad) * Math.cos(ha_rad))
  azi_deg = (azi_rad * RAD + 360) % 360

  {
    altitude: alt_deg,
    azimuth: azi_deg,
    solar_time: solar_time,
    eot: eot,
    declination: dec_rad * RAD,
    hour_angle: ha_rad * RAD
  }
end

def draw_sundial(azimuth_deg)
  size = 13
  half = size / 2
  grid = Array.new(size) { Array.new(size, ' ') }
  (0...size).each do |r|
    (0...size).each do |c|
      dx = c - half
      dy = r - half
      dist = Math.hypot(dx, dy)
      if (dist - half).abs < 0.5
        grid[r][c] = '·'
      end
    end
  end
  grid[half][half] = '●'
  angle_rad = azimuth_deg * DEG
  end_r = half - 1
  dx = (end_r * Math.sin(angle_rad)).round
  dy = (-end_r * Math.cos(angle_rad)).round
  x2 = half + dx
  y2 = half + dy
  x2 = [[x2, 0].max, size-1].min
  y2 = [[y2, 0].max, size-1].min
  x0, y0 = half, half
  steps = [ (x2-x0).abs, (y2-y0).abs ].max
  if steps > 0
    (1..steps).each do |i|
      x = (x0 + (x2 - x0) * i / steps.to_f).round
      y = (y0 + (y2 - y0) * i / steps.to_f).round
      if x >= 0 && x < size && y >= 0 && y < size
        if grid[y][x] == ' ' || grid[y][x] == '·'
          grid[y][x] = '*'
        end
      end
    end
    if y2 >= 0 && y2 < size && x2 >= 0 && x2 < size
      grid[y2][x2] = 'X'
    end
  end
  grid.map(&:join).join("\n")
end

options = {}
OptionParser.new do |opts|
  opts.banner = "Usage: ruby sundial.rb -lat LAT -lon LON [options]"
  opts.on('-lat LAT', Float, 'Latitude in degrees (positive North)') { |v| options[:lat] = v }
  opts.on('-lon LON', Float, 'Longitude in degrees (positive East)') { |v| options[:lon] = v }
  opts.on('-d DATE', 'Date YYYY-MM-DD') { |v| options[:date] = v }
  opts.on('-t TIME', 'Time HH:MM') { |v| options[:time] = v }
  opts.on('-tz OFFSET', Float, 'Timezone offset in hours') { |v| options[:tz] = v }
  opts.on('--no-color', 'Disable color output') { options[:no_color] = true }
end.parse!

unless options[:lat] && options[:lon]
  warn "Error: -lat and -lon required"
  exit 1
end

now = Time.now
if options[:date]
  dt = Date.parse(options[:date]).to_time
  if options[:time]
    h, m = options[:time].split(':').map(&:to_i)
    dt = Time.new(dt.year, dt.month, dt.day, h, m, 0, dt.utc_offset)
  else
    dt = Time.new(dt.year, dt.month, dt.day, now.hour, now.min, 0, dt.utc_offset)
  end
else
  if options[:time]
    h, m = options[:time].split(':').map(&:to_i)
    dt = Time.new(now.year, now.month, now.day, h, m, 0, now.utc_offset)
  else
    dt = now
  end
end

tz_offset = options[:tz] || -(now.utc_offset / 3600.0)

pos = compute_solar_position(options[:lat], options[:lon], dt, tz_offset)
alt = pos[:altitude]
azi = pos[:azimuth]
solar_time = pos[:solar_time]
eot = pos[:eot]

dir_names = %w[N NE E SE S SW W NW]
idx = (azi / 45).round % 8
azi_dir = dir_names[idx]

lat_str = "#{options[:lat].abs.round(2)}°#{options[:lat] >= 0 ? 'N' : 'S'}"
lon_str = "#{options[:lon].abs.round(2)}°#{options[:lon] >= 0 ? 'E' : 'W'}"
tz_sign = tz_offset >= 0 ? '+' : '-'

puts "\n☀️ Virtual Sundial"
puts "Location: #{lat_str}, #{lon_str}"
puts "Date: #{dt.strftime('%Y-%m-%d %H:%M')} (UTC#{tz_sign}#{tz_offset.abs.round(1)})"
solar_hours = solar_time.to_i
solar_min = ((solar_time - solar_hours) * 60).round
puts "Solar Time: #{solar_hours.to_s.rjust(2,'0')}:#{solar_min.to_s.rjust(2,'0')} (Equation: #{eot >= 0 ? '+' : ''}#{eot.round(1)} min)"
puts "Solar Altitude: #{alt.round(1)}°"
puts "Solar Azimuth: #{azi.round(1)}° (#{azi_dir})"
puts "\n" + "-"*20
sundial = draw_sundial(azi)
if options[:no_color]
  puts sundial
else
  # color: replace * with yellow, X with green
  puts sundial.gsub('*', "\e[33m*\e[0m").gsub('X', "\e[32mX\e[0m")
end
puts
