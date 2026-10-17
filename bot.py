import io
import os
import matplotlib.pyplot as plt
import pandas as pd
import requests
import yfinance as yf

# Telegram Bilgileri
BOT_TOKEN = "8609292057:AAEzjrPio_7af5lZWnwBI4fY6YX-16oB4mE"
CHAT_ID = "-5347011483"

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

  lines.append(f"\n📈 Detaylı Grafikler ve 10 Yıllık Panel:\n{DASHBOARD_URL}")
  return "\n".join(lines)


def send_telegram(message_text):
  url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
  payload = {"chat_id": CHAT_ID, "text": message_text}
  res = requests.post(url, json=payload, timeout=20)
  print("Piyasa Mesajı Yanıtı:", res.status_code, res.text)


def send_portwatch_chart():
  """IMF PortWatch'tan son 30 günlük Babülmendep ve Süveyş verilerini çeker,

  grafik oluşturup Telegram grubuna fotoğraf olarak gönderir.
  """
  url = "https://portwatch.imf.org/api/search/v1/rest/services/collections/Daily_Chokepoints_Data/geoservice/FeatureServer/0/query"

  noktalar = [
      ("Bab el-Mandeb Strait", "Babülmendep", "#d9534f"),
      ("Suez Canal", "Süveyş Kanalı", "#0275d8"),
  ]

  veriler = {}
  for cp_name, etiket, renk in noktalar:
    params = {
        "where": f"name='{cp_name}'",
        "outFields": "date,transit_calls",
        "orderByFields": "date DESC",
        "resultRecordCount": 30,
        "f": "json",
    }
    try:
      r = requests.get(url, params=params, timeout=15).json()
      rows = [x["attributes"] for x in r.get("features", [])]
      if rows:
        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"], unit="ms")
        veriler[etiket] = (df.sort_values("date"), renk)
    except Exception as e:
      print(f"PortWatch {etiket} hatası: {e}")

  if not veriler:
    print("PortWatch verisi alınamadığı için grafik gönderilmedi.")
    return

  # Grafiği Çiz
  plt.figure(figsize=(9, 4.5))
  for etiket, (df, renk) in veriler.items():
    plt.plot(
        df["date"],
        df["transit_calls"],
        label=etiket,
        color=renk,
        linewidth=2,
        marker=".",
    )

  plt.title("IMF PortWatch - Günlük Gemi Geçiş Trendi (Son 30 Gün)")
  plt.xlabel("Tarih")
  plt.ylabel("Gemi Sayısı")
  plt.grid(True, linestyle="--", alpha=0.5)
  plt.legend()
  plt.xticks(rotation=25)
  plt.tight_layout()

  # Diske kaydetmeden doğrudan bellekte (RAM) PNG oluştur
  buffer = io.BytesIO()
  plt.savefig(buffer, format="png", dpi=130)
  buffer.seek(0)
  plt.close()

  # Telegram'a Fotoğraf Olarak İlet
  photo_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
  caption = (
      "🚢 <b>IMF PortWatch Deniz Trafiği Raporu</b>\n"
      "Kritik boğazlardaki son 30 günlük gemi geçiş sayıları."
  )

  files = {"photo": ("portwatch.png", buffer, "image/png")}
  data = {"chat_id": CHAT_ID, "caption": caption, "parse_mode": "HTML"}

  res = requests.post(photo_url, data=data, files=files, timeout=25)
  print("PortWatch Grafik Yanıtı:", res.status_code, res.text)


if __name__ == "__main__":
  # 1. Piyasa özeti metnini gönder
  report = get_market_summary()
  send_telegram(report)

  # 2. PortWatch gemi trafiği grafiğini gönder
  send_portwatch_chart()
