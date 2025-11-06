from __future__ import annotations
from typing import Optional, Tuple, Dict, Any
import re
import requests
import yfinance as yf


def _clean_query(query: str) -> str:
    q = query.strip()
    q = re.sub(r'^https?://', '', q)
    q = q.split('/')[0]
    q = q.replace('www.', '')
    q = re.sub(r'[^\w\.-]+', ' ', q)
    return q.strip()


def search_ticker(query: str) -> Optional[str]:
    """Find the most relevant ticker using Yahoo's public suggestion API, fallback to yfinance search."""
    if not query:
        return None
    q = _clean_query(query)

    # Yahoo finance suggestion API
    try:
        resp = requests.get(
            'https://autoc.finance.yahoo.com/autoc',
            params={'query': q, 'region': 1, 'lang': 'en'}, timeout=6
        )
        if resp.ok:
            j = resp.json()
            results = (j.get('ResultSet') or {}).get('Result') or []
            for item in results:
                sym = item.get('symbol')
                t = (item.get('type') or '').lower()
                if sym and t in ('s', 'equity', 'etf'):  # prefer stocks
                    return sym
            # fallback to first symbol if types missing
            if results:
                sym = results[0].get('symbol')
                if sym:
                    return sym
    except Exception:
        pass

    # Fallback: yfinance search (if available)
    try:
        if hasattr(yf, 'search'):
            res = yf.search(q)
            quotes = (res or {}).get('quotes') or []
            for item in quotes:
                sym = item.get('symbol')
                if sym:
                    return sym
    except Exception:
        pass
    return None


def fetch_financials(ticker: str) -> Optional[Dict[str, Any]]:
    """Fetch key financial fields using yfinance. Returns None on failure."""
    try:
        t = yf.Ticker(ticker)
        out: Dict[str, Any] = {}

        # Try fast_info (dict-like)
        try:
            fi = t.fast_info
            if isinstance(fi, dict):
                out['currency'] = fi.get('currency')
                out['price'] = fi.get('last_price') or fi.get('lastPrice') or fi.get('regularMarketPrice')
                out['market_cap'] = fi.get('market_cap') or fi.get('marketCap')
            else:
                # attribute access fallback
                out['currency'] = getattr(fi, 'currency', None)
                out['price'] = getattr(fi, 'last_price', None)
                out['market_cap'] = getattr(fi, 'market_cap', None)
        except Exception:
            pass

        # Enriched info
        info = {}
        try:
            info = t.get_info() or {}
        except Exception:
            try:
                info = t.info or {}
            except Exception:
                info = {}

        out['currency'] = out.get('currency') or info.get('currency')
        out['price'] = out.get('price') or info.get('currentPrice') or info.get('regularMarketPrice')
        out['market_cap'] = out.get('market_cap') or info.get('marketCap')
        # Attempt to read change percent directly
        out['change_percent'] = info.get('regularMarketChangePercent') or info.get('regularMarketChangePercentRaw')
        out['pe_ratio'] = info.get('trailingPE') or info.get('forwardPE')
        out['revenue'] = info.get('totalRevenue') or info.get('revenue')
        out['employees'] = info.get('fullTimeEmployees') or info.get('employees')

        # Use history to compute price and 24h change when needed
        try:
            hist = t.history(period='2d', interval='1d')
            if hist is not None and not hist.empty:
                closes = hist['Close'].dropna()
                if len(closes) >= 1 and out.get('price') is None:
                    out['price'] = float(closes.iloc[-1])
                if len(closes) >= 2 and out.get('change_percent') is None:
                    prev = float(closes.iloc[-2])
                    last = float(closes.iloc[-1])
                    if prev != 0:
                        out['change_percent'] = ((last - prev) / prev) * 100.0
                        out['change'] = last - prev
        except Exception:
            pass

        # Try to estimate market cap from sharesOutstanding * price if missing
        if out.get('market_cap') is None and out.get('price') is not None and info.get('sharesOutstanding'):
            try:
                out['market_cap'] = int(float(info['sharesOutstanding']) * float(out['price']))
            except Exception:
                pass

        # Ensure at least one key metric exists
        if out.get('price') is None and out.get('market_cap') is None and out.get('revenue') is None:
            return None
        return out
    except Exception:
        return None


def resolve_and_fetch(company_name: Optional[str], company_url: Optional[str]) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Find a ticker for the company and fetch its financials."""
    query = company_name or company_url
    if not query:
        return None, None
    ticker = search_ticker(query)
    if not ticker:
        return None, None
    data = fetch_financials(ticker)
    return ticker, data
