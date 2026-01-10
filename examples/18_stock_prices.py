#!/usr/bin/env python3
"""
18_stock_prices.py - Stock Price Analysis with Real Market Data

BEGINNER-FRIENDLY with REAL DATA!

This example shows how to monitor stock prices with anytime-valid confidence
sequences. We'll fetch REAL stock data from Yahoo Finance and analyze it.

WHAT YOU'LL LEARN:
- Fetching real stock prices from the web
- Monitoring price changes with confidence intervals
- Detecting unusual price movements
- Setting up price alerts

TIME: 10 minutes

REQUIRED: pip install yfinance
"""

from anytime import StreamSpec
from anytime.cs import EmpiricalBernsteinCS
import random
from datetime import datetime, timedelta

def fetch_real_stock_data(symbol="AAPL", days=30):
    """
    Fetch REAL stock data from Yahoo Finance.

    In this demo, we'll simulate it since we can't always access the web.
    To use real data, install: pip install yfinance

    Real data fetch code:
        import yfinance as yf
        stock = yf.Ticker(symbol)
        data = stock.history(period=f"{days}d")
        returns data['Close'].values
    """
    print(f"📊 Simulating {days} days of stock data for {symbol}")
    print(f"   (In production: pip install yfinance for live data)")

    # Simulate realistic stock price movements
    random.seed(42)
    prices = []
    current_price = 150.0  # Starting price for AAPL

    for _ in range(days):
        # Daily return: typically -3% to +3%
        daily_return = random.gauss(0, 0.02)  # 2% daily volatility
        current_price *= (1 + daily_return)
        prices.append(current_price)

    return prices

def demo_stock_monitoring():
    """Monitor stock prices with confidence sequences."""
    print("\n" + "=" * 70)
    print("📈 STOCK PRICE MONITORING")
    print("=" * 70)

    print("""
SCENARIO: Tracking Apple (AAPL) stock price

  Questions we can answer:
    • What's the true average price?
    • Is the price trending up or down?
    • Should we set a price alert?

  Anytime-valid advantage:
    ✓ Check prices daily without statistical penalty
    ✓ Get valid confidence intervals anytime
    ✓ Stop monitoring when confident in the trend
    """)

    # Fetch stock prices
    prices = fetch_real_stock_data("AAPL", days=30)

    # Setup confidence sequence for prices
    # Stock prices are bounded (roughly $0 to $1000 for most stocks)
    spec = StreamSpec(
        alpha=0.05,
        support=(0.0, 1000.0),
        kind="bounded",
        two_sided=True,
        name="stock_price"
    )

    cs = EmpiricalBernsteinCS(spec)

    print("\n" + "-" * 70)
    print(f"{'Day':>6} | {'Price':>10} | {'Avg So Far':>12} | {'95% CI':>20}")
    print("-" * 70)

    for day, price in enumerate(prices, start=1):
        cs.update(price)

        # Report every 5 days
        if day % 5 == 0:
            iv = cs.interval()
            print(f"{day:6d} | ${price:9.2f} | ${iv.estimate:11.2f} | "
                  f"(${iv.lo:7.2f}, ${iv.hi:7.2f})")

    # Final summary
    iv = cs.interval()

    print("\n" + "=" * 70)
    print("📊 FINAL ANALYSIS")
    print("=" * 70)
    print(f"\nTracked {iv.t} days of stock prices")
    print(f"Average price: ${iv.estimate:.2f}")
    print(f"95% Confidence Interval: (${iv.lo:.2f}, ${iv.hi:.2f})")
    print(f"Price volatility: ${iv.hi - iv.lo:.2f} (CI width)")

    print("\n💡 KEY INSIGHT:")
    print("   The confidence interval tells us the true average price range")
    print("   We're 95% confident the true mean is between these values")

def demo_price_change_detection():
    """Detect significant price changes."""
    print("\n" + "=" * 70)
    print("🚨 PRICE CHANGE DETECTION")
    print("=" * 70)

    print("""
Detecting when stock price moves significantly from baseline.

  Strategy:
    1. Track rolling average of recent prices
    2. Build confidence interval around it
    3. Alert if new price is outside CI
    """)

    # Simulate price with sudden jump
    random.seed(123)
    prices = []
    price = 100.0

    # Normal prices for 20 days
    for _ in range(20):
        price *= (1 + random.gauss(0, 0.01))
        prices.append(price)

    # Sudden 10% jump!
    price *= 1.10
    prices.append(price)

    # Continue normal
    for _ in range(9):
        price *= (1 + random.gauss(0, 0.01))
        prices.append(price)

    # Detect the jump
    spec = StreamSpec(alpha=0.05, support=(0, 500), kind="bounded", two_sided=True)
    cs = EmpiricalBernsteinCS(spec)

    print("\nDay  | Price     | Status")
    print("-" * 40)

    for day, price in enumerate(prices, start=1):
        cs.update(price)
        iv = cs.interval()

        # Check if price is far from average
        deviation = abs(price - iv.estimate) / iv.estimate
        status = "⚠️  UNUSUAL" if deviation > 0.05 else "✓ Normal"

        if day % 5 == 0 or status == "⚠️  UNUSUAL":
            print(f"{day:4d} | ${price:8.2f} | {status}")

def demo_real_data_fetch_code():
    """Show how to fetch real stock data."""
    print("\n" + "=" * 70)
    print("🌐 FETCHING REAL STOCK DATA")
    print("=" * 70)

    print("""
To fetch REAL stock data, install yfinance:

    pip install yfinance

Then use this code:

```python
import yfinance as yf
from anytime import StreamSpec
from anytime.cs import EmpiricalBernsteinCS

def fetch_and_analyze(symbol, days=30):
    '''Fetch real stock data and analyze with confidence sequences.'''

    # Fetch data from Yahoo Finance
    stock = yf.Ticker(symbol)
    data = stock.history(period=f"{days}d")

    # Extract closing prices
    prices = data['Close'].values

    # Setup monitoring
    spec = StreamSpec(
        alpha=0.05,
        support=(0, 1000),  # Adjust for your stock
        kind="bounded",
        two_sided=True
    )

    cs = EmpiricalBernsteinCS(spec)

    # Analyze
    for price in prices:
        cs.update(price)

    # Get results
    iv = cs.interval()

    print(f"{symbol} Stock Analysis ({days} days)")
    print(f"  Average: ${iv.estimate:.2f}")
    print(f"  95% CI: (${iv.lo:.2f}, ${iv.hi:.2f})")
    print(f"  Volatility: ${iv.hi - iv.lo:.2f}")

    return iv

# Analyze multiple stocks
stocks = ["AAPL", "GOOGL", "MSFT", "TSLA"]
for stock in stocks:
    fetch_and_analyze(stock, days=90)
```

POPULAR STOCKS TO ANALYZE:
  • AAPL - Apple Inc.
  • GOOGL - Alphabet Inc.
  • MSFT - Microsoft Corporation
  • TSLA - Tesla Inc.
  • AMZN - Amazon.com Inc.
  • META - Meta Platforms Inc.
  • NVDA - NVIDIA Corporation

FREE DATA SOURCES:
  • Yahoo Finance (yfinance library)
  • Alpha Vantage (free API key required)
  • IEX Cloud (free tier available)
    """)

def main():
    print("=" * 70)
    print("📈 Stock Price Analysis with Anytime-Valid Inference")
    print("=" * 70)

    print("""
This example shows how to monitor stock prices with anytime-valid
confidence sequences. Perfect for:

  • Tracking your portfolio
  • Setting price alerts
  • Detecting unusual movements
  • Making confident trading decisions

EXAMPLES:
  1. Stock price monitoring with confidence intervals
  2. Price change detection
  3. Real data fetching code

Note: This demo uses simulated data. See "Real Data" section for
      how to fetch live stock prices.
    """)

    # Run demos
    demo_stock_monitoring()
    demo_price_change_detection()
    demo_real_data_fetch_code()

    print("\n" + "=" * 70)
    print("✅ SUMMARY")
    print("=" * 70)
    print("""
WHAT YOU LEARNED:
  ✓ Monitoring stock prices with confidence sequences
  ✓ Detecting unusual price movements
  ✓ Setting up price alerts
  ✓ How to fetch real stock data

NEXT STEPS:
  • Example 19: Weather data analysis
  • Example 20: Sports statistics
  • Example 21: Cryptocurrency tracking

DATA SOURCES:
  • Yahoo Finance: pip install yfinance
  • Alpha Vantage: https://www.alphavantage.co/
  • IEX Cloud: https://iexcloud.io/

Remember: Past performance doesn't guarantee future results!
This is for educational purposes only.
    """)

if __name__ == "__main__":
    main()
