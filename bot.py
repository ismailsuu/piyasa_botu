import os
import requests
import yfinance as yf

# Takip edilecek enstrümanlar ve Yahoo Finance kodları
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
}

# Özel Streamlit panel adresiniz
DASHBOARD_URL = "https://ismail-piyasa.streamlit.app/"


def get_market_summary():
  lines = ["📊 Piyasa Özeti (Canlı)\n"]
  for label, symbol in TICKERS.items():
    try:
      ticker = yf.Ticker(symbol)
      hist = ticker.history(period="2d")
      if not hist.empty:
        last_price = round(float(hist["Close"].iloc[-1]), 2)
        if len(hist) > 1:
          prev_close = float(hist["Close"].iloc[-2])
          change_pct = round(((last_price - prev_close) / prev_close) * 100, 2)
          icon = "🟢" if change_pct >= 0 else "🔴"
          lines.append(f"{icon} {label}: {last_price} (%{change_pct})")
        else:
          lines.append(f"• {label}: {last_price}")
      else:
        lines.append(f"• {label}: Veri yok")
    except Exception:
      lines.append(f"• {label}: Alınamadı")

  # Mesajın altına tıklanabilir panel linki ekleme
  lines.append(f"\n📈 Detaylı Grafikler ve 10 Yıllık Panel:\n{DASHBOARD_URL}")
  return "\n".join(lines)


def send_telegram(message_text):
  bot_token = "8609292057:AAEzjrPio_7af5lZWnwBI4fY6YX-16oB4mE"
  chat_id = "-5347011483"

  url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
  payload = {"chat_id": chat_id, "text": message_text}
  res = requests.post(url, json=payload, timeout=20)
  print("Telegram Yanıtı:", res.status_code, res.text)


if __name__ == "__main__":
  report = get_market_summary()
  send_telegram(report)
