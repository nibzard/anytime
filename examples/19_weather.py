#!/usr/bin/env python3
"""
19_weather.py - Weather Data Analysis with Temperature Monitoring

BEGINNER-FRIENDLY with REAL DATA!

Track daily temperatures with confidence intervals. Perfect for learning
about anytime-valid inference with data you encounter every day.

WHAT YOU'LL LEARN:
- Working with temperature data
- Detecting unusual weather patterns
- Seasonal vs unusual changes
- Setting up weather alerts

TIME: 10 minutes
"""

from anytime import StreamSpec
from anytime.cs import EmpiricalBernsteinCS
import random
from datetime import datetime, timedelta

def generate_weather_data(location="New York", days=30, season="summer"):
    """
    Generate realistic temperature data.

    In production, fetch from:
    - NOAA API: https://www.ncdc.noaa.gov/cdo-web/
    - OpenWeatherMap: https://openweathermap.org/api
    - WeatherAPI: https://www.weatherapi.com/

    Install: pip install requests pyowm
    """
    print(f"🌡️  Simulating {days} days of weather for {location}")

    # Base temperatures by season (Fahrenheit)
    bases = {
        "winter": 35,   # ~35°F
        "spring": 55,   # ~55°F
        "summer": 80,   # ~80°F
        "fall": 60      # ~60°F
    }

    base_temp = bases.get(season, 60)
    random.seed(42)

    temps = []
    for _ in range(days):
        # Daily temperature fluctuation
        fluctuation = random.gauss(0, 10)  # ±10°F typical daily variation
        temp = base_temp + fluctuation
        temps.append(temp)

    return temps

def demo_temperature_tracking():
    """Track daily temperatures with confidence intervals."""
    print("\n" + "=" * 70)
    print("🌡️  TEMPERATURE TRACKING")
    print("=" * 70)

    print("""
SCENARIO: Tracking daily high temperatures in summer

  Questions:
    • What's the true average temperature?
    • Is today unusually hot or cold?
    • When should we declare a "heat wave"?

  Anytime-valid advantage:
    ✓ Check daily without statistical penalty
    ✓ Get valid confidence intervals anytime
    ✓ Detect unusual patterns early
    """)

    # Generate summer weather
    temps = generate_weather_data("Phoenix", days=30, season="summer")

    # Setup confidence sequence
    # Temperatures typically: -20°F to 120°F
    spec = StreamSpec(
        alpha=0.05,
        support=(-20.0, 120.0),
        kind="bounded",
        two_sided=True,
        name="temperature_f"
    )

    cs = EmpiricalBernsteinCS(spec)

    print("\n" + "-" * 70)
    print(f"{'Day':>6} | {'Temp':>8} | {'Avg':>8} | {'95% CI':>18} | {'Status':>12}")
    print("-" * 70)

    for day, temp in enumerate(temps, start=1):
        cs.update(temp)

        # Report every 5 days
        if day % 5 == 0:
            iv = cs.interval()

            # Check if unusually hot (above CI)
            is_hot = temp > iv.hi
            is_cold = temp < iv.lo

            if is_hot:
                status = "🔥 HOT!"
            elif is_cold:
                status = "❄️  COLD!"
            else:
                status = "✓ Normal"

            print(f"{day:6d} | {temp:7.1f}°F | {iv.estimate:7.1f}°F | "
                  f"({iv.lo:5.1f}°, {iv.hi:5.1f}°) | {status:>12}")

    # Final summary
    iv = cs.interval()

    print("\n" + "=" * 70)
    print("📊 30-DAY WEATHER SUMMARY")
    print("=" * 70)
    print(f"\nAverage temperature: {iv.estimate:.1f}°F")
    print(f"95% Confidence Interval: ({iv.lo:.1f}°F, {iv.hi:.1f}°F)")
    print(f"Temperature range: {min(temps):.1f}°F to {max(temps):.1f}°F")

def demo_heat_wave_detection():
    """Detect heat waves with confidence sequences."""
    print("\n" + "=" * 70)
    print("🔥 HEAT WAVE DETECTION")
    print("=" * 70)

    print("""
SCENARIO: Detecting when temperatures become unusually high

  Heat wave definition (simplified):
    • 3+ consecutive days above normal range
    • Confidence interval helps define "normal"

  Strategy:
    1. Track baseline temperatures
    2. Build confidence interval
    3. Alert when multiple days exceed CI
    """)

    # Generate normal weather then heat wave
    random.seed(456)
    temps = []

    # 20 normal days
    for _ in range(20):
        temps.append(random.gauss(80, 8))

    # 10 hot days (heat wave!)
    for _ in range(10):
        temps.append(random.gauss(95, 5))

    # Detect
    spec = StreamSpec(alpha=0.05, support=(-20, 120), kind="bounded", two_sided=True)
    cs = EmpiricalBernsteinCS(spec)

    print("\nDay  | Temp  | Status")
    print("-" * 35)

    consecutive_hot = 0

    for day, temp in enumerate(temps, start=1):
        cs.update(temp)
        iv = cs.interval()

        is_hot = temp > iv.hi

        if is_hot:
            consecutive_hot += 1
            status = f"🔥 Hot (day {consecutive_hot})"
        else:
            consecutive_hot = 0
            status = "✓ Normal"

        # Show interesting days
        if day % 5 == 0 or is_hot:
            print(f"{day:4d} | {temp:5.1f}°F | {status}")

    if consecutive_hot >= 3:
        print(f"\n🚨 HEAT WAVE DETECTED!")
        print(f"   {consecutive_hot} consecutive hot days")

def demo_real_weather_api():
    """Show how to fetch real weather data."""
    print("\n" + "=" * 70)
    print("🌐 FETCHING REAL WEATHER DATA")
    print("=" * 70)

    print("""
To fetch REAL weather data, use these APIs:

OPTION 1: OpenWeatherMap (Free tier available)
-----------------------------------------------
    pip install pyowm

```python
from pyowm import OWM
from anytime import StreamSpec
from anytime.cs import EmpiricalBernsteinCS

def fetch_weather(location, api_key):
    '''Fetch current weather and forecast.'''

    owm = OWM(api_key)
    mgr = owm.weather_manager()

    # Get current weather
    observation = mgr.weather_at_place(location)
    current = observation.weather.temperature('fahrenheit')['temp']

    # Get forecast
    forecast = mgr.forecast_at_place(location, 3)
    temps = []

    for weather in forecast.forecast:
        temp = weather.temperature('fahrenheit')['temp']
        temps.append(temp)

    return [current] + temps

# Usage
api_key = "your-api-key-here"
location = "New York,US"
temps = fetch_weather(location, api_key)

# Analyze with confidence sequences
spec = StreamSpec(alpha=0.05, support=(-20, 120), kind="bounded", two_sided=True)
cs = EmpiricalBernsteinCS(spec)

for temp in temps:
    cs.update(temp)

iv = cs.interval()
print(f"Temperature forecast: {iv.estimate:.1f}°F")
print(f"95% CI: ({iv.lo:.1f}°F, {iv.hi:.1f}°F)")
```

OPTION 2: NOAA Climate Data (Free)
----------------------------------
    https://www.ncdc.noaa.gov/cdo-web/webservices/v2

OPTION 3: WeatherAPI (Free tier)
---------------------------------
    pip install requests

```python
import requests

def get_weather_api(location, api_key):
    url = f"http://api.weatherapi.com/v1/forecast.json"
    params = {
        "key": api_key,
        "q": location,
        "days": 7,
        "aqi": "no"
    }
    response = requests.get(url, params=params)
    data = response.json()

    temps = []
    for day in data['forecast']['forecastday']:
        max_temp = day['day']['maxtemp_f']
        temps.append(max_temp)

    return temps
```

POPULAR LOCATIONS TO TRACK:
  • New York,US
  • London,UK
  • Tokyo,JP
  • Sydney,AU
  • Mumbai,IN
  • Cairo,EG

FREE WEATHER APIs:
  • OpenWeatherMap: https://openweathermap.org/api (free tier)
  • WeatherAPI: https://www.weatherapi.com/ (free tier)
  • NOAA: https://www.ncdc.noaa.gov/cdo-web/ (completely free)
    """)

def main():
    print("=" * 70)
    print("🌡️  Weather Data Analysis")
    print("=" * 70)

    print("""
Track daily temperatures with anytime-valid confidence sequences.

Perfect for:
  • Learning about confidence intervals
  • Detecting unusual weather patterns
  • Setting up weather alerts
  • Understanding climate data

EXAMPLES:
  1. Temperature tracking with confidence intervals
  2. Heat wave detection
  3. Real weather data fetching code

Note: Demo uses simulated data. See "Real Data" section for
      live weather API integration.
    """)

    demo_temperature_tracking()
    demo_heat_wave_detection()
    demo_real_weather_api()

    print("\n" + "=" * 70)
    print("✅ SUMMARY")
    print("=" * 70)
    print("""
WHAT YOU LEARNED:
  ✓ Temperature monitoring with confidence sequences
  ✓ Detecting unusual weather patterns
  ✓ Heat wave detection strategy
  ✓ How to fetch real weather data

NEXT STEPS:
  • Example 18: Stock price analysis
  • Example 20: Sports statistics
  • Example 21: Cryptocurrency tracking

DATA SOURCES:
  • OpenWeatherMap: pip install pyowm
  • WeatherAPI: https://www.weatherapi.com/
  • NOAA Climate Data: https://www.ncdc.noaa.gov/

Remember: Weather is inherently variable. Confidence intervals
help distinguish normal fluctuations from unusual patterns!
    """)

if __name__ == "__main__":
    main()
