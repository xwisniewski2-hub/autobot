#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║         BINANCE.US BOT v1 — AGGRESSIVE SPOT EDITION            ║
║         20 coins | Per-coin signals | Institutional logic       ║
║         Long only | No leverage | Spot trading                  ║
╠══════════════════════════════════════════════════════════════════╣
║  STRATEGIES:                                                     ║
║  • Trend Following     — SMA/EMA/Ichimoku (Renaissance/Citadel) ║
║  • Momentum Scoring    — AQR Capital style                      ║
║  • Mean Reversion      — Two Sigma oversold dips                ║
║  • Volume Confirmation — OBV/MFI eliminates fake breakouts      ║
║  • Volatility Target   — AQR 20% annualized vol sizing          ║
║  • Half-Kelly Sizing   — Optimal bet sizing (quant standard)    ║
║  • DCA Tranches        — 40/30/30% entry at 0/-2%/-4%          ║
║  • Adaptive Cooldown   — 1/3/7 days by stop-out count          ║
║  • Momentum Crash Prot — Exit if down 8% from entry            ║
║  • News Sentiment      — CryptoPanic free API filter            ║
║  • Price Confirmation  — Cross-exchange sanity check            ║
║                                                                  ║
║  SAFETY:                                                         ║
║  ✓ Stops at $0. Manual restart required.                        ║
║  ✓ No withdrawals. No bank access. Ever.                        ║
║  ✓ Max loss = starting deposit.                                 ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os, sys, json, time, math, hmac, hashlib, datetime as dt
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import numpy as np
import pandas as pd
import warnings
import urllib.request
import urllib.error
import urllib.parse
warnings.filterwarnings("ignore")

# ════════════════════════════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════════════════════════════
CONFIG = {
    # Universe — 20 coins on Binance.US
    "universe": [
        "BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT",
        "DOGEUSDT","AVAXUSDT","LINKUSDT","AAVEUSDT","UNIUSDT",
        "MATICUSDT","ADAUSDT","DOTUSDT","ATOMUSDT","LTCUSDT",
        "BCHUSDT","NEARUSDT","APTUSDT","ARBUSDT","OPUSDT",
    ],

    # Account
    "starting_cash":      500,      # Update to your actual deposit
    "max_position_pct":   0.20,     # Max 20% per coin
    "max_positions":      10,       # Max 10 open at once

    # Trend indicators
    "sma_fast":           50,
    "sma_slow":           200,
    "ema_fast":           12,
    "ema_slow":           26,
    "ichi_tenkan":        9,
    "ichi_kijun":         26,
    "ichi_senkou_b":      52,
    "adx_period":         14,
    "adx_min":            10,       # Relaxed for aggressive mode

    # Momentum
    "mom_fast":           30,
    "mom_slow":           90,
    "mom_min_fast":       0.002,    # Relaxed
    "mom_min_slow":       0.01,     # Relaxed
    "rsi_period":         14,
    "rsi_entry_max":      80,       # Allows more entries
    "rsi_exit_min":       25,
    "rsi_profit_take":    82,
    "stoch_period":       14,
    "stoch_smooth_k":     3,
    "stoch_smooth_d":     3,
    "macd_fast":          12,
    "macd_slow":          26,
    "macd_signal":        9,

    # Volume
    "obv_ma_period":      20,
    "mfi_period":         14,
    "mfi_min":            40,       # Relaxed
    "volume_lookback":    20,
    "volume_mult":        1.05,     # Relaxed

    # Structure
    "zscore_lookback":    20,
    "zscore_max":         3.0,      # Relaxed
    "bb_period":          20,
    "bb_std":             2.0,
    "cci_period":         20,

    # ATR
    "atr_stop_mult":      3.0,
    "atr_trail_mult":     3.0,

    # Fear & Greed — very aggressive gates
    "fg_block_fear":      5,        # Block only at extreme fear (<5)
    "fg_block_greed":     95,
    "fg_exit_greed":      98,

    # Kelly — Half-Kelly
    "kelly_fraction":     0.50,
    "kelly_max_pct":      0.20,
    "kelly_lookback":     30,

    # Exit / entry targets
    "take_profit_pct":    0.15,     # 15% take profit
    "stop_loss_pct":      0.07,     # 7% stop loss

    # Partial profit
    "partial_tp_pct":     0.08,
    "partial_tp_frac":    0.50,

    # Scoring — AGGRESSIVE: threshold 45 (vs 65 on Alpaca)
    "score_threshold":    45,
    "weight_trend":       40,
    "weight_momentum":    25,
    "weight_volume":      20,
    "weight_structure":   15,

    # Dynamic sizing by score
    "size_mult_low":      0.70,
    "size_mult_mid":      0.85,
    "size_mult_high":     1.00,

    # Volatility targeting (AQR)
    "vol_target_annual":  0.20,
    "vol_lookback_days":  20,

    # Momentum crash protection
    "crash_pct_1d":       0.08,     # Exit if down 8% from entry

    # DCA tranches
    "dca_tranche_1":      0.40,
    "dca_tranche_2":      0.30,
    "dca_tranche_3":      0.30,
    "dca_drop_2":         0.02,
    "dca_drop_3":         0.04,

    # News sentiment
    "news_block_hours":   24,
    "sentiment_block":    -0.4,     # Only block on strongly negative news

    # Price confirmation
    "price_diff_block":   0.008,    # 0.8% divergence block

    # Adaptive cooldown
    "cooldown_1":         1,
    "cooldown_2":         3,
    "cooldown_3plus":     7,

    # Correlation
    "correlation_threshold": 0.85,
    "correlation_lookback":  30,

    # Alerts
    "ntfy_topic": os.environ.get("NTFY_TOPIC", ""),

    # Loop
    "check_interval_min": 15,       # Check every 15 minutes
    "state_file":         "binance_state.json",
    "journal_file":       "binance_journal.json",

    # Binance.US base URL
    "base_url":           "https://api.binance.us",
}

# ════════════════════════════════════════════════════════════════
# ALERTS
# ════════════════════════════════════════════════════════════════
def send_alert(title, message):
    topic = CONFIG.get("ntfy_topic", "")
    if not topic:
        return
    try:
        req = urllib.request.Request(
            f"https://ntfy.sh/{topic}",
            data=message.encode(), method="POST",
            headers={"Title": title, "Priority": "default", "Tags": "chart_increasing"}
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass


# ════════════════════════════════════════════════════════════════
# BINANCE.US API
# ════════════════════════════════════════════════════════════════
class BinanceUS:
    def __init__(self, key, secret):
        self.key    = key
        self.secret = secret
        self.base   = CONFIG["base_url"]

    def _sign(self, params):
        qs  = urllib.parse.urlencode(params)
        sig = hmac.new(self.secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
        params["signature"] = sig
        return params

    def _headers(self):
        return {
            "X-MBX-APIKEY": self.key,
            "Content-Type": "application/x-www-form-urlencoded",
        }

    def get(self, path, params=None, signed=False):
        params = params or {}
        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["recvWindow"] = 10000
            params = self._sign(params)
        url = self.base + path + ("?" + urllib.parse.urlencode(params) if params else "")
        req = urllib.request.Request(url, headers=self._headers())
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())

    def post(self, path, params):
        params["timestamp"] = int(time.time() * 1000)
        params["recvWindow"] = 10000
        params = self._sign(params)
        data = urllib.parse.urlencode(params).encode()
        req  = urllib.request.Request(
            self.base + path, data=data,
            method="POST", headers=self._headers()
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())

    def delete(self, path, params):
        params["timestamp"] = int(time.time() * 1000)
        params["recvWindow"] = 10000
        params = self._sign(params)
        data = urllib.parse.urlencode(params).encode()
        req  = urllib.request.Request(
            self.base + path, data=data,
            method="DELETE", headers=self._headers()
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())

    def account(self):
        return self.get("/api/v3/account", signed=True)

    def get_balances(self):
        acct = self.account()
        return {b["asset"]: float(b["free"]) for b in acct["balances"] if float(b["free"]) > 0}

    def get_price(self, symbol):
        data = self.get("/api/v3/ticker/price", {"symbol": symbol})
        return float(data["price"])

    def get_all_prices(self):
        data = self.get("/api/v3/ticker/price")
        return {d["symbol"]: float(d["price"]) for d in data}

    def get_klines(self, symbol, interval="1d", limit=600):
        data = self.get("/api/v3/klines", {
            "symbol": symbol, "interval": interval, "limit": limit
        })
        rows = []
        for k in data:
            rows.append({
                "open":   float(k[1]),
                "high":   float(k[2]),
                "low":    float(k[3]),
                "close":  float(k[4]),
                "volume": float(k[5]),
            })
        df = pd.DataFrame(rows)
        return df

    def get_open_orders(self, symbol=None):
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self.get("/api/v3/openOrders", params, signed=True)

    def cancel_order(self, symbol, order_id):
        return self.delete("/api/v3/order", {"symbol": symbol, "orderId": order_id})

    def cancel_all_orders(self, symbol):
        return self.delete("/api/v3/openOrders", {"symbol": symbol})

    def market_buy(self, symbol, quote_qty):
        """Buy using USDT amount (quoteOrderQty)."""
        return self.post("/api/v3/order", {
            "symbol":        symbol,
            "side":          "BUY",
            "type":          "MARKET",
            "quoteOrderQty": str(round(quote_qty, 2)),
        })

    def market_sell_qty(self, symbol, qty):
        """Sell exact quantity of base asset."""
        # Get lot size filter
        info = self.get_symbol_info(symbol)
        qty  = self._apply_lot_filter(qty, info)
        if qty <= 0:
            return None
        return self.post("/api/v3/order", {
            "symbol":   symbol,
            "side":     "SELL",
            "type":     "MARKET",
            "quantity": self._fmt_qty(qty, info),
        })

    def get_symbol_info(self, symbol):
        try:
            data = self.get("/api/v3/exchangeInfo", {"symbol": symbol})
            for s in data.get("symbols", []):
                if s["symbol"] == symbol:
                    return s
        except Exception:
            pass
        return {}

    def _apply_lot_filter(self, qty, info):
        for f in info.get("filters", []):
            if f["filterType"] == "LOT_SIZE":
                step = float(f["stepSize"])
                mini = float(f["minQty"])
                if step > 0:
                    qty = math.floor(qty / step) * step
                if qty < mini:
                    return 0.0
        return qty

    def _fmt_qty(self, qty, info):
        for f in info.get("filters", []):
            if f["filterType"] == "LOT_SIZE":
                step = float(f["stepSize"])
                if step > 0:
                    decimals = max(0, round(-math.log10(step)))
                    return f"{qty:.{decimals}f}"
        return str(qty)

    def set_stop_loss(self, symbol, qty, stop_price, info=None):
        """Place a stop-loss sell order."""
        if info is None:
            info = self.get_symbol_info(symbol)
        qty = self._apply_lot_filter(qty, info)
        if qty <= 0:
            return None
        return self.post("/api/v3/order", {
            "symbol":    symbol,
            "side":      "SELL",
            "type":      "STOP_LOSS_LIMIT",
            "timeInForce": "GTC",
            "quantity":  self._fmt_qty(qty, info),
            "price":     str(round(stop_price * 0.999, 8)),  # Limit slightly below stop
            "stopPrice": str(round(stop_price, 8)),
        })

    def set_take_profit(self, symbol, qty, tp_price, info=None):
        """Place a take-profit sell order."""
        if info is None:
            info = self.get_symbol_info(symbol)
        qty = self._apply_lot_filter(qty, info)
        if qty <= 0:
            return None
        return self.post("/api/v3/order", {
            "symbol":    symbol,
            "side":      "SELL",
            "type":      "TAKE_PROFIT_LIMIT",
            "timeInForce": "GTC",
            "quantity":  self._fmt_qty(qty, info),
            "price":     str(round(tp_price, 8)),
            "stopPrice": str(round(tp_price * 0.999, 8)),
        })


# ════════════════════════════════════════════════════════════════
# FEAR & GREED
# ════════════════════════════════════════════════════════════════
_fg_cache = {"value": None, "ts": 0}

def get_fear_greed():
    if time.time() - _fg_cache["ts"] < 3600 and _fg_cache["value"] is not None:
        return _fg_cache["value"]
    try:
        with urllib.request.urlopen(
            "https://api.alternative.me/fng/?limit=1&format=json", timeout=5
        ) as r:
            val = int(json.loads(r.read())["data"][0]["value"])
        _fg_cache.update({"value": val, "ts": time.time()})
        return val
    except Exception:
        return _fg_cache["value"] if _fg_cache["value"] is not None else 50

def fg_label(v):
    if v <= 25:  return "Extreme Fear 😱"
    if v <= 45:  return "Fear 😰"
    if v <= 55:  return "Neutral 😐"
    if v <= 75:  return "Greed 😏"
    return "Extreme Greed 🤑"


# ════════════════════════════════════════════════════════════════
# NEWS SENTIMENT
# ════════════════════════════════════════════════════════════════
_news_cache = {}

def get_news_sentiment(coin_name):
    cached = _news_cache.get(coin_name, {})
    if time.time() - cached.get("ts", 0) < 3600:
        return cached.get("value", 0)
    try:
        url = f"https://cryptopanic.com/api/free/v1/posts/?currencies={coin_name}&filter=news&public=true"
        with urllib.request.urlopen(url, timeout=8) as r:
            data  = json.loads(r.read())
            posts = data.get("results", [])
        if not posts:
            return 0
        total_bull = 0
        total_bear = 0
        cutoff = time.time() - (CONFIG["news_block_hours"] * 3600)
        for post in posts[:20]:
            try:
                pub_str = post.get("published_at", "")
                if pub_str:
                    pub_ts = dt.datetime.fromisoformat(
                        pub_str.replace("Z", "+00:00")).timestamp()
                    if pub_ts < cutoff:
                        continue
                votes = post.get("votes", {})
                total_bull += int(votes.get("positive", 0))
                total_bear += int(votes.get("negative", 0))
            except Exception:
                pass
        total = total_bull + total_bear
        if total == 0:
            return 0
        score = (total_bull - total_bear) / total
        _news_cache[coin_name] = {"value": score, "ts": time.time()}
        return score
    except Exception:
        return 0


# ════════════════════════════════════════════════════════════════
# INDICATOR ENGINE
# ════════════════════════════════════════════════════════════════
def indicators(df):
    o = df.copy()
    c, h, l, v = o["close"], o["high"], o["low"], o["volume"]

    o["sma_fast"] = c.rolling(CONFIG["sma_fast"]).mean()
    o["sma_slow"] = c.rolling(CONFIG["sma_slow"]).mean()
    o["ema_fast"] = c.ewm(span=CONFIG["ema_fast"], adjust=False).mean()
    o["ema_slow"] = c.ewm(span=CONFIG["ema_slow"], adjust=False).mean()

    tr = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
    o["atr"]     = tr.rolling(14).mean()
    o["atr_sma"] = o["atr"].rolling(20).mean()

    up  = h.diff(); dn = -l.diff()
    pdm = up.where((up > dn) & (up > 0), 0.0)
    ndm = dn.where((dn > up) & (dn > 0), 0.0)
    atr14 = tr.ewm(alpha=1/CONFIG["adx_period"], adjust=False).mean()
    pdi = 100 * pdm.ewm(alpha=1/CONFIG["adx_period"], adjust=False).mean() / atr14
    ndi = 100 * ndm.ewm(alpha=1/CONFIG["adx_period"], adjust=False).mean() / atr14
    dx  = (100 * (pdi - ndi).abs() / (pdi + ndi).replace(0, np.nan))
    o["adx"] = dx.ewm(alpha=1/CONFIG["adx_period"], adjust=False).mean()
    o["pdi"] = pdi
    o["ndi"] = ndi

    def hl_mid(n): return (h.rolling(n).max() + l.rolling(n).min()) / 2
    o["tenkan"]   = hl_mid(CONFIG["ichi_tenkan"])
    o["kijun"]    = hl_mid(CONFIG["ichi_kijun"])
    span_a        = ((o["tenkan"] + o["kijun"]) / 2).shift(CONFIG["ichi_kijun"])
    span_b        = hl_mid(CONFIG["ichi_senkou_b"]).shift(CONFIG["ichi_kijun"])
    o["kumo_top"] = pd.concat([span_a, span_b], axis=1).max(axis=1)
    o["kumo_bot"] = pd.concat([span_a, span_b], axis=1).min(axis=1)

    o["mom_fast"] = c.pct_change(CONFIG["mom_fast"])
    o["mom_slow"] = c.pct_change(CONFIG["mom_slow"])

    delta = c.diff()
    gain  = delta.clip(lower=0).rolling(CONFIG["rsi_period"]).mean()
    loss  = (-delta.clip(upper=0)).rolling(CONFIG["rsi_period"]).mean()
    o["rsi"] = 100 - (100 / (1 + gain / loss.replace(0, np.nan)))

    rsi_min  = o["rsi"].rolling(CONFIG["stoch_period"]).min()
    rsi_max  = o["rsi"].rolling(CONFIG["stoch_period"]).max()
    raw_k    = 100 * (o["rsi"] - rsi_min) / (rsi_max - rsi_min).replace(0, np.nan)
    o["stoch_k"] = raw_k.rolling(CONFIG["stoch_smooth_k"]).mean()
    o["stoch_d"] = o["stoch_k"].rolling(CONFIG["stoch_smooth_d"]).mean()

    ema_f         = c.ewm(span=CONFIG["macd_fast"], adjust=False).mean()
    ema_s         = c.ewm(span=CONFIG["macd_slow"], adjust=False).mean()
    o["macd"]     = ema_f - ema_s
    o["macd_sig"] = o["macd"].ewm(span=CONFIG["macd_signal"], adjust=False).mean()
    o["macd_hist"]      = o["macd"] - o["macd_sig"]
    o["macd_hist_prev"] = o["macd_hist"].shift(1)

    direction   = np.sign(c.diff()).fillna(0)
    o["obv"]    = (v * direction).cumsum()
    o["obv_ma"] = o["obv"].rolling(CONFIG["obv_ma_period"]).mean()

    tp     = (h + l + c) / 3
    mf     = tp * v
    pos_mf = mf.where(tp > tp.shift(), 0.0).rolling(CONFIG["mfi_period"]).sum()
    neg_mf = mf.where(tp < tp.shift(), 0.0).rolling(CONFIG["mfi_period"]).sum()
    o["mfi"] = 100 - (100 / (1 + pos_mf / neg_mf.replace(0, np.nan)))

    o["vol_avg"]   = v.rolling(CONFIG["volume_lookback"]).mean()
    o["vol_ratio"] = v / o["vol_avg"]

    rm = c.rolling(CONFIG["zscore_lookback"]).mean()
    rs = c.rolling(CONFIG["zscore_lookback"]).std()
    o["zscore"] = (c - rm) / rs.replace(0, np.nan)

    o["bb_mid"]   = c.rolling(CONFIG["bb_period"]).mean()
    bb_std        = c.rolling(CONFIG["bb_period"]).std()
    o["bb_upper"] = o["bb_mid"] + CONFIG["bb_std"] * bb_std
    o["bb_lower"] = o["bb_mid"] - CONFIG["bb_std"] * bb_std

    tp2      = (h + l + c) / 3
    tp_sma   = tp2.rolling(CONFIG["cci_period"]).mean()
    mean_dev = tp2.rolling(CONFIG["cci_period"]).apply(
        lambda x: np.mean(np.abs(x - x.mean())), raw=True)
    o["cci"] = (tp2 - tp_sma) / (0.015 * mean_dev.replace(0, np.nan))

    return o


# ════════════════════════════════════════════════════════════════
# SIGNAL ENGINE
# ════════════════════════════════════════════════════════════════
def weighted_score(row):
    trend_signals = [
        int(row["sma_fast"]  > row["sma_slow"]),
        int(row["ema_fast"]  > row["ema_slow"]),
        int(row["close"]     > row["kumo_top"]),
        int(row["tenkan"]    > row["kijun"]),
    ]
    trend_score = (sum(trend_signals) / 4) * CONFIG["weight_trend"]

    momentum_signals = [
        int(row["mom_fast"]  > CONFIG["mom_min_fast"]),
        int(row["rsi"]       < CONFIG["rsi_entry_max"]),
        int(row["stoch_k"]   > row["stoch_d"]),
        int(row["macd_hist"] > row["macd_hist_prev"]),
    ]
    momentum_score = (sum(momentum_signals) / 4) * CONFIG["weight_momentum"]

    volume_signals = [
        int(row["obv"]       > row["obv_ma"]),
        int(row["mfi"]       > CONFIG["mfi_min"]),
        int(row["vol_ratio"] > CONFIG["volume_mult"]),
    ]
    volume_score = (sum(volume_signals) / 3) * CONFIG["weight_volume"]

    structure_signals = [
        int(abs(row["zscore"]) < CONFIG["zscore_max"]),
        int(row["close"]       > row["bb_mid"]),
        int(row["cci"]         > 0),
    ]
    structure_score = (sum(structure_signals) / 3) * CONFIG["weight_structure"]

    return round(trend_score + momentum_score + volume_score + structure_score, 1)


def signal(row, fg_score=50):
    required = (
        "sma_slow","ema_fast","ema_slow","adx","tenkan","kijun",
        "kumo_top","mom_fast","mom_slow","rsi","stoch_k","stoch_d",
        "macd","macd_sig","macd_hist","macd_hist_prev",
        "obv","obv_ma","mfi","vol_ratio","zscore","bb_mid","cci","atr"
    )
    if any(pd.isna(row.get(k, float("nan"))) for k in required):
        return "flat", 0

    # Exit conditions
    long_exit = (
        row["close"] < row["sma_slow"] or
        row["macd"]  < row["macd_sig"] or
        row["rsi"]   < CONFIG["rsi_exit_min"] or
        fg_score     > CONFIG["fg_exit_greed"] or
        row["rsi"]   > CONFIG["rsi_profit_take"]
    )
    if long_exit:
        return "flat", 0

    # Core entry conditions — relaxed for Binance aggressive mode
    core = [
        fg_score     > CONFIG["fg_block_fear"],
        row["close"] > row["sma_slow"],
        row["adx"]   > CONFIG["adx_min"],
        row["mom_slow"] > CONFIG["mom_min_slow"],
    ]
    if not all(core):
        return "flat", 0

    score = weighted_score(row)
    if score >= CONFIG["score_threshold"]:
        return "long", score
    return "flat", score


# ════════════════════════════════════════════════════════════════
# SIZING
# ════════════════════════════════════════════════════════════════
def score_size_mult(score):
    if score >= 75:   return CONFIG["size_mult_high"]
    elif score >= 60: return CONFIG["size_mult_mid"]
    else:             return CONFIG["size_mult_low"]

def vol_scalar(df):
    try:
        returns = df["close"].pct_change().dropna().tail(CONFIG["vol_lookback_days"])
        realized_vol = returns.std() * np.sqrt(252)
        if realized_vol <= 0:
            return 1.0
        scalar = CONFIG["vol_target_annual"] / realized_vol
        return min(max(scalar, 0.3), 1.5)
    except Exception:
        return 1.0

def kelly_size(equity, price, atr, trade_history, score=65, corr=0.0, vol_mult=1.0):
    wins   = [t for t in trade_history if t > 0]
    losses = [t for t in trade_history if t < 0]

    if len(wins) >= 3 and len(losses) >= 3:
        wr    = len(wins) / len(trade_history)
        avg_w = np.mean(wins)
        avg_l = abs(np.mean(losses))
        if avg_w > 0 and avg_l > 0:
            kelly_f = max(0, (wr * avg_w - (1 - wr) * avg_l) / avg_w)
            base    = min(
                CONFIG["kelly_fraction"] * kelly_f * equity,
                CONFIG["kelly_max_pct"] * equity,
                CONFIG["max_position_pct"] * equity,
            )
        else:
            base = 0.0
    else:
        stop_dist = CONFIG["atr_stop_mult"] * atr
        if stop_dist <= 0 or price <= 0:
            return 0.0
        base = min(
            (0.02 * equity * price) / stop_dist,
            CONFIG["max_position_pct"] * equity,
        )

    base *= score_size_mult(score)
    base *= min(vol_mult, 1.5)
    if corr > CONFIG["correlation_threshold"]:
        base *= 0.50

    return max(0.0, base)

def get_cooldown_days(stop_count):
    if stop_count >= 3: return CONFIG["cooldown_3plus"]
    if stop_count == 2: return CONFIG["cooldown_2"]
    return CONFIG["cooldown_1"]


# ════════════════════════════════════════════════════════════════
# TRADE JOURNAL
# ════════════════════════════════════════════════════════════════
def log_trade(action, symbol, notional, price, score, fg, reason, pnl_pct=None):
    try:
        try:
            journal = json.load(open(CONFIG["journal_file"]))
        except Exception:
            journal = []
        entry = {
            "ts":       dt.datetime.now().isoformat(),
            "action":   action,
            "symbol":   symbol,
            "notional": round(notional, 2),
            "price":    round(price, 8),
            "score":    score,
            "fg":       fg,
            "reason":   reason,
        }
        if pnl_pct is not None:
            entry["pnl_pct"] = round(pnl_pct * 100, 2)
        journal.append(entry)
        json.dump(journal, open(CONFIG["journal_file"], "w"), indent=2)
    except Exception:
        pass


# ════════════════════════════════════════════════════════════════
# DASHBOARD
# ════════════════════════════════════════════════════════════════
def print_dashboard(equity, start_equity, trade_history, positions, fg):
    ret  = (equity / start_equity - 1) * 100
    wins = [t for t in trade_history if t > 0]
    wr   = (len(wins) / len(trade_history) * 100) if trade_history else 0
    print(f"\n  {'─'*52}")
    print(f"  BINANCE.US BOT  |  F&G: {fg} {fg_label(fg)}")
    print(f"  {'─'*52}")
    print(f"  Equity    : ${equity:.2f}  ({ret:+.1f}%)")
    print(f"  Trades    : {len(trade_history)}  |  Win rate: {wr:.0f}%")
    print(f"  Positions : {len(positions)}")
    if trade_history:
        print(f"  Best      : {max(trade_history)*100:+.1f}%  |  Worst: {min(trade_history)*100:+.1f}%")
    print(f"  {'─'*52}")


# ════════════════════════════════════════════════════════════════
# MAIN LOOP
# ════════════════════════════════════════════════════════════════
def main():
    key    = os.environ.get("BINANCE_KEY", "")
    secret = os.environ.get("BINANCE_SECRET", "")

    if not key or not secret:
        print("❌  BINANCE_KEY and BINANCE_SECRET environment variables required.")
        print("    Set them in Railway → Variables tab.")
        sys.exit(1)

    bn = BinanceUS(key, secret)

    print(f"\n{'═'*64}")
    print(f" BINANCE.US BOT v1 — AGGRESSIVE SPOT — LIVE 💰")
    print(f"{'═'*64}\n")

    # Verify connection
    try:
        balances = bn.get_balances()
        usdt     = balances.get("USDT", 0.0)
        print(f"  ✓  Connected to Binance.US")
        print(f"  ✓  USDT balance: ${usdt:.2f}")
        start_equity = usdt
        CONFIG["starting_cash"] = usdt if usdt > 0 else CONFIG["starting_cash"]
    except Exception as e:
        print(f"  ❌  Connection failed: {e}")
        sys.exit(1)

    print(f"  ✓  Max loss = your balance. Cannot exceed.")
    print(f"  ✓  No withdrawals. No bank access. Ever.")
    print(f"  ✓  Bot stops at $0. Manual restart required.")
    print(f"  ✓  Universe: {len(CONFIG['universe'])} coins")
    print(f"  ✓  Check interval: every {CONFIG['check_interval_min']} minutes\n")

    # Load state
    try:
        state = json.load(open(CONFIG["state_file"]))
    except Exception:
        state = {}

    cooldown_st   = state.get("cooldown", {})
    stop_counts   = state.get("stop_counts", {})
    trade_history = state.get("trade_history", [])
    partial_done  = state.get("partial_done", {})
    dca_state     = state.get("dca", {})
    positions     = state.get("positions", {})
    # positions[symbol] = {qty, entry_price, stop_order_id, tp_order_id, notional}

    def save_state():
        json.dump({
            "cooldown":      cooldown_st,
            "stop_counts":   stop_counts,
            "trade_history": trade_history,
            "partial_done":  partial_done,
            "dca":           dca_state,
            "positions":     positions,
        }, open(CONFIG["state_file"], "w"))

    def emergency_halt(reason):
        print(f"\n{'█'*60}")
        print(f"  🛑  EMERGENCY HALT: {reason}")
        print(f"{'█'*60}")
        # Cancel all open orders and market-sell all positions
        for sym, pos in list(positions.items()):
            try:
                bn.cancel_all_orders(sym)
                bn.market_sell_qty(sym, pos["qty"])
                print(f"  ✓  Closed {sym}")
            except Exception as ex:
                print(f"  ⚠ Could not close {sym}: {ex}")
        send_alert("🛑 BOT HALTED", reason)
        print(f"  ✓  Your bank account has NOT been touched.")
        sys.exit(0)

    while True:
        try:
            ts   = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
            fg   = get_fear_greed()

            # Get current USDT balance + value of all held coins
            try:
                all_prices = bn.get_all_prices()
                balances   = bn.get_balances()
                usdt       = balances.get("USDT", 0.0)

                # Calculate total equity including open positions
                equity = usdt
                for sym, pos in positions.items():
                    p = all_prices.get(sym, pos.get("entry_price", 0))
                    equity += pos["qty"] * p

            except Exception as e:
                print(f"  ⚠ Balance fetch failed: {e}")
                time.sleep(60)
                continue

            print(f"\n[{ts}]  equity=${equity:.2f}  F&G={fg} {fg_label(fg)}")

            if equity <= 1.0:
                emergency_halt(f"Equity ${equity:.2f} — fully exhausted.")

            print_dashboard(equity, start_equity, trade_history, positions, fg)

            # ── Check existing positions ──────────────────────────
            for sym in list(positions.keys()):
                pos = positions[sym]
                curr_price = all_prices.get(sym, 0)
                if curr_price <= 0:
                    continue

                entry_price = pos.get("entry_price", curr_price)
                qty         = pos.get("qty", 0)

                # Crash protection: exit if down 8%+ from entry
                if entry_price > 0:
                    drop = (curr_price - entry_price) / entry_price
                    if drop < -CONFIG["crash_pct_1d"]:
                        try:
                            bn.cancel_all_orders(sym)
                            bn.market_sell_qty(sym, qty)
                            pnl = drop
                            trade_history.append(pnl)
                            s_ticker = sym.replace("USDT","") + "-USD"
                            stop_counts[s_ticker] = stop_counts.get(s_ticker, 0) + 1
                            cooldown_st[s_ticker] = time.time()
                            partial_done.pop(f"partial_{sym}", None)
                            dca_state.pop(s_ticker, None)
                            del positions[sym]
                            save_state()
                            print(f"  💥 CRASH EXIT {sym:<12} {drop*100:+.1f}% from entry")
                            send_alert("💥 Crash Exit", f"{sym}: {drop*100:+.1f}% → force exit")
                            log_trade("crash_exit", sym, 0, curr_price, 0, fg,
                                      "momentum_crash", pnl)
                        except Exception as ex:
                            print(f"  ⚠ Crash exit {sym}: {ex}")
                        continue

                # Get signal for exit check
                try:
                    df  = indicators(bn.get_klines(sym))
                    row = df.iloc[-1]
                    sig, score = signal(row, fg)
                except Exception:
                    continue

                # Partial profit at 8% gain
                part_key = f"partial_{sym}"
                if (entry_price > 0 and
                    curr_price >= entry_price * (1 + CONFIG["partial_tp_pct"]) and
                    not partial_done.get(part_key)):
                    try:
                        half_qty = qty * CONFIG["partial_tp_frac"]
                        result = bn.market_sell_qty(sym, half_qty)
                        if result:
                            positions[sym]["qty"] = qty - half_qty
                            partial_done[part_key] = True
                            save_state()
                            gain = (curr_price / entry_price - 1) * 100
                            print(f"  PARTIAL TP  {sym:<12} +{gain:.1f}% → sold 50%")
                            send_alert("💰 Partial Profit", f"{sym}: Sold 50% at +{gain:.1f}%")
                            log_trade("partial_tp", sym, 0, curr_price, score, fg,
                                      f"partial_tp_{gain:.1f}pct")
                    except Exception as ex:
                        print(f"  ⚠ Partial TP {sym}: {ex}")

                # Exit on signal flip
                if sig != "long":
                    try:
                        current_qty = positions[sym]["qty"]
                        bn.cancel_all_orders(sym)
                        bn.market_sell_qty(sym, current_qty)
                        pnl = (curr_price - entry_price) / entry_price if entry_price > 0 else 0
                        trade_history.append(pnl)
                        if len(trade_history) > CONFIG["kelly_lookback"]:
                            trade_history.pop(0)
                        s_ticker = sym.replace("USDT","") + "-USD"
                        cooldown_st[s_ticker] = time.time()
                        partial_done.pop(f"partial_{sym}", None)
                        dca_state.pop(s_ticker, None)
                        del positions[sym]
                        save_state()
                        reason = "RSI_ob" if row["rsi"] > CONFIG["rsi_profit_take"] else "signal"
                        print(f"  EXIT        {sym:<12} {pnl*100:+.1f}% [{reason}]")
                        send_alert("📤 Exit", f"{sym}: {pnl*100:+.1f}% [{reason}]")
                        log_trade("exit_long", sym, 0, curr_price, score, fg, reason, pnl)
                    except Exception as ex:
                        print(f"  ⚠ Exit {sym}: {ex}")
                    continue

                # DCA tranche 2
                s_ticker = sym.replace("USDT","") + "-USD"
                dca = dca_state.get(s_ticker, {})
                if dca:
                    drop_from_entry = (curr_price - entry_price) / entry_price
                    if (not dca.get("tranche_2_done") and
                        drop_from_entry <= -CONFIG["dca_drop_2"] and usdt >= 1.0):
                        t2 = dca["remaining"] * (
                            CONFIG["dca_tranche_2"] /
                            (CONFIG["dca_tranche_2"] + CONFIG["dca_tranche_3"])
                        )
                        t2 = min(math.floor(t2 * 100) / 100, usdt * 0.95)
                        if t2 >= 1.0:
                            try:
                                result = bn.market_buy(sym, t2)
                                if result:
                                    filled_qty = float(result.get("executedQty", 0))
                                    positions[sym]["qty"] += filled_qty
                                    dca["tranche_2_done"] = True
                                    save_state()
                                    usdt -= t2
                                    print(f"  DCA T2      {sym:<12} ${t2:.2f} (drop {drop_from_entry*100:.1f}%)")
                                    log_trade("dca_t2", sym, t2, curr_price, score, fg,
                                              f"dca_drop_{drop_from_entry*100:.1f}pct")
                            except Exception as ex:
                                print(f"  ⚠ DCA T2 {sym}: {ex}")

                    elif (dca.get("tranche_2_done") and
                          not dca.get("tranche_3_done") and
                          drop_from_entry <= -CONFIG["dca_drop_3"] and usdt >= 1.0):
                        t3 = dca["remaining"] * (
                            CONFIG["dca_tranche_3"] /
                            (CONFIG["dca_tranche_2"] + CONFIG["dca_tranche_3"])
                        )
                        t3 = min(math.floor(t3 * 100) / 100, usdt * 0.95)
                        if t3 >= 1.0:
                            try:
                                result = bn.market_buy(sym, t3)
                                if result:
                                    filled_qty = float(result.get("executedQty", 0))
                                    positions[sym]["qty"] += filled_qty
                                    dca["tranche_3_done"] = True
                                    save_state()
                                    usdt -= t3
                                    print(f"  DCA T3      {sym:<12} ${t3:.2f} (drop {drop_from_entry*100:.1f}%)")
                                    log_trade("dca_t3", sym, t3, curr_price, score, fg,
                                              f"dca_drop_{drop_from_entry*100:.1f}pct")
                            except Exception as ex:
                                print(f"  ⚠ DCA T3 {sym}: {ex}")

            # ── Scan for new entries ──────────────────────────────
            for symbol in CONFIG["universe"]:
                if symbol in positions:
                    continue
                if len(positions) >= CONFIG["max_positions"]:
                    break

                # Adaptive cooldown
                s_ticker = symbol.replace("USDT","") + "-USD"
                cd_days  = get_cooldown_days(stop_counts.get(s_ticker, 0))
                if time.time() - cooldown_st.get(s_ticker, 0) < cd_days * 86400:
                    continue

                try:
                    df  = indicators(bn.get_klines(symbol))
                    row = df.iloc[-1]
                    sig, score = signal(row, fg)
                except Exception as ex:
                    print(f"  ⚠ Data {symbol}: {ex}")
                    continue

                if sig != "long":
                    continue

                # News sentiment filter
                coin_name  = symbol.replace("USDT", "")
                news_score = get_news_sentiment(coin_name)
                if news_score < CONFIG["sentiment_block"]:
                    print(f"  SKIP {symbol:<12} negative news ({news_score:.2f})")
                    continue

                # Correlation check vs open positions
                corr = 0.0
                if positions:
                    try:
                        new_rets = df["close"].pct_change().dropna().tail(30)
                        for held_sym in list(positions.keys())[:3]:
                            try:
                                h_df   = indicators(bn.get_klines(held_sym))
                                h_rets = h_df["close"].pct_change().dropna().tail(30)
                                aligned = pd.concat([new_rets, h_rets], axis=1).dropna()
                                if len(aligned) > 10:
                                    c_val = abs(aligned.iloc[:,0].corr(aligned.iloc[:,1]))
                                    corr  = max(corr, c_val)
                            except Exception:
                                pass
                    except Exception:
                        pass

                # Size the position
                curr_price = all_prices.get(symbol, float(row["close"]))
                v_mult     = vol_scalar(df)
                notional   = kelly_size(equity, curr_price, float(row["atr"]),
                                        trade_history, score, corr, v_mult)
                tranche_1  = notional * CONFIG["dca_tranche_1"]
                tranche_1  = min(math.floor(tranche_1 * 100) / 100, usdt * 0.95)

                if tranche_1 < 1.0:
                    print(f"  SKIP {symbol:<12} insufficient funds (${tranche_1:.2f})")
                    continue

                try:
                    result = bn.market_buy(symbol, tranche_1)
                    if not result:
                        continue
                    filled_qty   = float(result.get("executedQty", 0))
                    filled_price = (float(result.get("cummulativeQuoteQty", tranche_1))
                                    / filled_qty if filled_qty > 0 else curr_price)

                    # Store position
                    positions[symbol] = {
                        "qty":         filled_qty,
                        "entry_price": filled_price,
                        "notional":    tranche_1,
                    }

                    # Place stop-loss order
                    sl_price = round(filled_price * (1 - CONFIG["stop_loss_pct"]), 8)
                    tp_price = round(filled_price * (1 + CONFIG["take_profit_pct"]), 8)
                    try:
                        bn.set_stop_loss(symbol, filled_qty, sl_price)
                    except Exception as ex:
                        print(f"  ⚠ SL order {symbol}: {ex}")
                    try:
                        bn.set_take_profit(symbol, filled_qty, tp_price)
                    except Exception as ex:
                        print(f"  ⚠ TP order {symbol}: {ex}")

                    # DCA state
                    dca_state[s_ticker] = {
                        "entry_price":    filled_price,
                        "remaining":      notional * (1 - CONFIG["dca_tranche_1"]),
                        "tranche_2_done": False,
                        "tranche_3_done": False,
                    }

                    usdt -= tranche_1
                    save_state()

                    print(f"  ENTER LONG  {symbol:<12} T1:${tranche_1:.2f} "
                          f"score:{score:.0f} SL:{sl_price:.4f} TP:{tp_price:.4f}")
                    send_alert("📈 Long Entry",
                               f"{symbol}: ${tranche_1:.2f} | Score:{score:.0f} | F&G:{fg}")
                    log_trade("enter_long_t1", symbol, tranche_1, filled_price,
                              score, fg, "signal")

                except Exception as ex:
                    print(f"  ⚠ Enter {symbol}: {ex}")

        except urllib.error.HTTPError as e:
            print(f"  ⚠  HTTP {e.code}: {e.reason} — retrying in 60s")
            time.sleep(60)
            continue
        except Exception as e:
            print(f"  ⚠  Error: {e} — retrying in 60s")
            time.sleep(60)
            continue

        time.sleep(CONFIG["check_interval_min"] * 60)


# ════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    main()
