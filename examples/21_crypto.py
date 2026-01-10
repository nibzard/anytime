#!/usr/bin/env python3
"""
21_crypto.py - Cryptocurrency Price Monitoring

BEGINNER-FRIENDLY!

Track crypto prices with anytime-valid confidence sequences.
Perfect for volatile markets where you need valid inference.

WHAT YOU'LL LEARN:
- Monitoring Bitcoin and other crypto prices
- Detecting pumps and dumps
- Volatility analysis
- Price trend confidence

TIME: 10 minutes
"""

from anytime import StreamSpec
from anytime.cs import EmpiricalBernsteinCS
import random

def demo_bitcoin_tracking():
    """Track Bitcoin price with confidence intervals."""
    print("\n" + "=" * 70)
    print("₿ BITCOIN PRICE TRACKING")
    print("=" * 70)

    print("""
SCENARIO: Monitoring Bitcoin price over 30 days

  Crypto markets are EXTREMELY volatile:
    • Prices swing 5-10% daily (sometimes more!)
    • Traditional stats fail with frequent peeking
    • Anytime-valid methods perfect for this

  Anytime-valid advantage:
    ✓ Check price daily without penalty
    ✓ Valid confidence intervals even with high volatility
    ✓ Stop monitoring when confident in trend
    """)

    # Simulate Bitcoin price (very volatile!)
    random.seed(42)
    prices = []
    price = 65000  # Starting BTC price in USD

    for _ in range(30):
        # Crypto has huge daily swings: ±5% typical
        daily_change = random.gauss(0, 0.05)
        price *= (1 + daily_change)
        prices.append(price)

    # Setup monitoring
    # Bitcoin: $0 to $1,000,000 (wide bounds for extreme volatility)
    spec = StreamSpec(
        alpha=0.05,
        support=(0.0, 1000000.0),
        kind="bounded",
        two_sided=True,
        name="btc_price_usd"
    )

    cs = EmpiricalBernsteinCS(spec)

    print("\n" + "-" * 70)
    print(f"{'Day':>6} | {'BTC Price':>12} | {'Avg':>12} | {'95% CI':>20}")
    print("-" * 70)

    for day, price in enumerate(prices, start=1):
        cs.update(price)

        if day % 5 == 0:
            iv = cs.interval()
            print(f"{day:6d} | ${price:10,.2f} | ${iv.estimate:10,.2f} | "
                  f"(${iv.lo:10,.2f}, ${iv.hi:10,.2f})")

    iv = cs.interval()
    print("\n" + "=" * 70)
    print("📊 30-DAY SUMMARY")
    print("=" * 70)
    print(f"\nAverage: ${iv.estimate:,.2f}")
    print(f"95% CI: (${iv.lo:,.2f}, ${iv.hi:,.2f})")
    print(f"Volatility: ${iv.hi - iv.lo:,.2f}")

def demo_volatility_comparison():
    """Compare volatility of different cryptos."""
    print("\n" + "=" * 70)
    print("📊 CRYPTO VOLATILITY COMPARISON")
    print("=" * 70)

    print("""
Different cryptocurrencies have different volatility levels:

  Bitcoin (BTC):  ~5% daily swings
  Ethereum (ETH): ~7% daily swings
  Memecoins (DOGE): ~15% daily swings!

Confidence intervals naturally reflect this volatility.
    """)

    cryptos = {
        'BTC': 0.05,   # 5% volatility
        'ETH': 0.07,   # 7% volatility
        'DOGE': 0.15   # 15% volatility
    }

    print(f"\n{'Crypto':>8} | {'Volatility':>12} | {'CI Width':>15} | {'Stability':>12}")
    print("-" * 60)

    for crypto, vol in cryptos.items():
        spec = StreamSpec(alpha=0.05, support=(0, 1000000), kind="bounded", two_sided=True)
        cs = EmpiricalBernsteinCS(spec)

        random.seed(hash(crypto))
        price = 1000  # Normalized starting price

        for _ in range(30):
            daily_change = random.gauss(0, vol)
            price *= (1 + daily_change)
            cs.update(price)

        iv = cs.interval()
        width = iv.hi - iv.lo

        if width < 200:
            stability = "Stable"
        elif width < 500:
            stability = "Moderate"
        else:
            stability = "Volatile"

        print(f"{crypto:>8} | {vol:11.1%} | ${width:14,.2f} | {stability:>12}")

def demo_real_crypto_data():
    """Show how to fetch real crypto prices."""
    print("\n" + "=" * 70)
    print("🌐 REAL CRYPTO DATA")
    print("=" * 70)

    print("""
To fetch REAL crypto prices, use these APIs:

FREE OPTIONS:
-------------

1. CoinGecko (Free, no API key needed)
   https://www.coingecko.com/en/api

```python
import requests
from anytime import StreamSpec
from anytime.cs import EmpiricalBernsteinCS

def get_crypto_price(coin_id):
    '''Get current price from CoinGecko.'''

    url = f"https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": coin_id,
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }

    response = requests.get(url, params=params)
    data = response.json()

    return data[coin_id]['usd']

# Track Bitcoin
spec = StreamSpec(alpha=0.05, support=(0, 1000000), kind="bounded", two_sided=True)
cs = EmpiricalBernsteinCS(spec)

for day in range(30):
    price = get_crypto_price("bitcoin")
    cs.update(price)
    print(f"Day {day}: ${price:,.2f}")

iv = cs.interval()
print(f"30-day avg: ${iv.estimate:,.2f}")
print(f"95% CI: (${iv.lo:,.2f}, ${iv.hi:,.2f})")
```

2. CoinMarketCap (Free tier)
   https://coinmarketcap.com/api/

3. Binance API (Free for market data)
   https://binance-docs.github.io/apidocs/

POPULAR COINS TO TRACK:
-----------------------
• bitcoin (BTC)
• ethereum (ETH)
• binancecoin (BNB)
• ripple (XRP)
• cardano (ADA)
• solana (SOL)
• dogecoin (DOGE)
• polkadot (DOT)

RATES TO AVOID:
----------------
Most free APIs have rate limits. For production:
• Cache responses
• Use paid plans for high frequency
• Respect rate limits!

INVESTMENT DISCLAIMER:
----------------------
This is for educational purposes only.
Crypto is HIGH RISK and EXTREMELY volatile.
Never invest more than you can afford to lose!
    """)

def main():
    print("=" * 70)
    print("₿ Cryptocurrency Price Monitoring")
    print("=" * 70)

    print("""
Track crypto prices with anytime-valid confidence sequences.

Perfect for:
  • Crypto traders and investors
  • Understanding volatility
  • Detecting unusual price movements
  • Making data-driven decisions

EXAMPLES:
  1. Bitcoin price tracking
  2. Volatility comparison
  3. Real crypto data APIs

⚠️  WARNING: Crypto is extremely volatile!
This is educational, not financial advice.
    """)

    demo_bitcoin_tracking()
    demo_volatility_comparison()
    demo_real_crypto_data()

    print("\n" + "=" * 70)
    print("✅ SUMMARY")
    print("=" * 70)
    print("""
WHAT YOU LEARNED:
  ✓ Crypto price monitoring with confidence
  ✓ Volatility comparison across coins
  ✓ How to fetch real crypto prices

KEY INSIGHT:
  High volatility = wider confidence intervals
  This reflects uncertainty in price predictions!

NEXT STEPS:
  • Example 18: Stock prices (less volatile)
  • Example 22: Website traffic
  • Example 23: Social media metrics

DATA SOURCES:
  • CoinGecko: https://www.coingecko.com/en/api (FREE!)
  • CoinMarketCap: https://coinmarketcap.com/api/
  • Binance: https://binance-docs.github.io/apidocs/

Remember: Crypto markets never sleep!
Confidence sequences let you check anytime.
    """)

if __name__ == "__main__":
    main()
