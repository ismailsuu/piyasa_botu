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

  # Mesajın altına tıklanabilir panel linki ekleme
  lines.append(f"\n📈 Detaylı Grafikler ve 10 Yıllık Panel:\n{DASHBOARD_URL}")
  return "\n".join(lines)


def send_telegram(message_text):
  url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
  payload = {"chat_id": CHAT_ID, "text": message_text}
  res = requests.post(url, json=payload, timeout=20)
  print("Piyasa Mesajı Yanıtı:", res.status_code, res.text)


def send_portwatch_chart():
  """IMF PortWatch açık veri servisinden Babülmendep ve Süveyş verilerini çeker,

  grafik oluşturup Telegram grubuna fotoğraf olarak gönderir.
  """
  url = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"

  # Güvenlik başlığı (ArcGIS bot filtresine takılmamak için)
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }

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
      res = requests.get(url, params=params, headers=headers, timeout=20)
      data = res.json()

      if "error" in data:
        print(f"ArcGIS API Hatası ({etiket}): {data['error']}")
        continue

      rows = [x["attributes"] for x in data.get("features", [])]
      if rows:
        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"], unit="ms")
        veriler[etiket] = (df.sort_values("date"), renk)
      else:
        print(f"Kayıt bulunamadı: {etiket}")
    except Exception as e:
      print(f"PortWatch bağlantı hatası ({etiket}): {e}")

  if not veriler:
    print(
        "PortWatch verisi çekilemediği için grafik gönderimi iptal edildi."
    )
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
  plt.ylabel("Geçiş Yapan Gemi Sayısı")
  plt.grid(True, linestyle="--", alpha=0.5)
  plt.legend()
  plt.xticks(rotation=25)
  plt.tight_layout()

  # Diske yazmadan belleğe kaydet (RAM)
  buffer = io.BytesIO()
  plt.savefig(buffer, format="png", dpi=130)
  buffer.seek(0)
  plt.close()

  # Telegram'a Fotoğraf Olarak İlet
  photo_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
  caption = (
      "🚢 <b>IMF PortWatch Deniz Trafiği Raporu</b>\n"
      "Babülmendep ve Süveyş Kanalı son 30 günlük gemi geçiş grafiği."
  )

  files = {"photo": ("portwatch.png", buffer, "image/png")}
  data = {"chat_id": CHAT_ID, "caption": caption, "parse_mode": "HTML"}

  res = requests.post(photo_url, data=data, files=files, timeout=25)
  print("PortWatch Telegram Yanıtı:", res.status_code, res.text)


if __name__ == "__main__":
  # 1. Piyasa özeti metnini Telegram'a gönder
  report = get_market_summary()
  send_telegram(report)

  # 2. PortWatch gemi trafiği grafiğini Telegram'a gönder
  send_portwatch_chart()
