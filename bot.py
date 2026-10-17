import os
import requests
import yfinance as yf

# Telegram Ayarları
BOT_TOKEN = "8609292057:AAEzjrPio_7af5lZWnwBI4fY6YX-16oB4mE"
CHAT_ID = "-5347011483"

# Takip edilecek enstrümanlar ve Yahoo Finance sembolleri
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

DASHBOARD_URL = "https://ismail-piyasa.streamlit.app/"


def get_portwatch_summary():
  """PortWatch'tan en güncel günlük gemi geçiş sayılarını çeker."""
  url = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"
  headers = {"User-Agent": "Mozilla/5.0"}
  targets = [("Suez", "Süveyş Kanalı"), ("Bab el-Mandeb", "Babülmendep")]

  lines = ["\n🚢 Boğaz / Gemi Trafiği (Son Gün)"]
  success = False

  for keyword, label in targets:
    params = {
        "where": f"name LIKE '%{keyword}%'",
        "outFields": "transit_calls",
        "orderByFields": "date DESC",
        "resultRecordCount": 1,
        "f": "json",
    }
    try:
      res = requests.get(url, params=params, headers=headers, timeout=10).json()
      features = res.get("features", [])
      if features:
        calls = int(features[0]["attributes"].get("transit_calls", 0))
        lines.append(f"⚓ {label}: {calls} gemi")
        success = True
      else:
        lines.append(f"⚓ {label}: Veri yok")
    except Exception:
      lines.append(f"⚓ {label}: Alınamadı")

  return "\n".join(lines) if success else ""


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

  # Gemi verilerini ekle
  portwatch_text = get_portwatch_summary()
  if portwatch_text:
    lines.append(portwatch_text)

  # Streamlit bağlantı linki
  lines.append(f"\n📈 Detaylı Grafikler ve 10 Yıllık Panel:\n{DASHBOARD_URL}")
  return "\n".join(lines)


def send_telegram(message_text):
  url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
  payload = {"chat_id": CHAT_ID, "text": message_text}
  res = requests.post(url, json=payload, timeout=20)
  print("Telegram Yanıtı:", res.status_code, res.text)


if __name__ == "__main__":
  report = get_market_summary()
  send_telegram(report)
