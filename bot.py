import os
import requests
import yfinance as yf

TICKERS = {
    "Bitcoin (BTC)": "BTC-USD",
    "Altın (Ons)": "GC=F",
    "Gümüş (Ons)": "SI=F",
    "Brent Petrol": "BZ=F",
    "Doğalgaz": "NG=F",
    "Pamuk (#2)": "CT=F",
    "USD/TRY": "USDTRY=X",
    "ABD 10Y Tahvil": "^TNX",
    "USD/CNY": "CNY=X",
    "Almanya 10Y": "DE10YT=RR"
}

def get_market_summary():
    lines = ["📊 *Piyasa Özeti (Canlı)*\n"]
    for label, symbol in TICKERS.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")
            if not hist.empty:
                last_price = round(hist['Close'].iloc[-1], 2)
                if len(hist) > 1:
                    prev_close = hist['Close'].iloc[-2]
                    change_pct = round(((last_price - prev_close) / prev_close) * 100, 2)
                    icon = "🟢" if change_pct >= 0 else "🔴"
                    lines.append(f"{icon} *{label}*: `{last_price}` (%{change_pct})")
                else:
                    lines.append(f"• *{label}*: `{last_price}`")
        except Exception:
            lines.append(f"• *{label}*: Veri alınamadı")
    return "\n".join(lines)

def send_telegram(message_text):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message_text,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

if __name__ == "__main__":
    report = get_market_summary()
    send_telegram(report)
