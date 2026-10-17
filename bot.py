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
  """IMF PortWatch servisinden Babülmendep ve Süveyş verilerini çeker ve grafiği Telegram'a iletir."""
  # PortWatch açık ArcGIS Katmanı
  url = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"

  # Güvenilir sorgu: LIKE ile isim eşleştirme ve en güncel 50 kayıt
  hedefler = [
      ("Bab el-Mandeb", "Babülmendep", "#d9534f"),
      ("Suez", "Süveyş Kanalı", "#0275d8"),
  ]

  headers = {"User-Agent": "Mozilla/5.0"}
  veriler = {}

  for anahtar_kelime, etiket, renk in hedefler:
    params = {
        "where": f"name LIKE '%{anahtar_kelime}%'",
        "outFields": "*",
        "orderByFields": "date DESC",
        "resultRecordCount": 35,
        "f": "json",
    }
    try:
      res = requests.get(url, params=params, headers=headers, timeout=25)
      data = res.json()

      features = data.get("features", [])
      if not features:
        print(f"Kayıt boş geldi: {etiket}")
        continue

      rows = [f["attributes"] for f in features]
      df = pd.DataFrame(rows)

      # Sütun isimlerini küçük harfe çevirerek uyumluluk sağla
      df.columns = [c.lower() for c in df.columns]

      # Tarih formatlama
      tarih_kolonu = "date" if "date" in df.columns else df.columns[0]
      deger_kolonu = (
          "transit_calls"
          if "transit_calls" in df.columns
          else [c for c in df.columns if "call" in c or "transit" in c][0]
      )

      df["tarih"] = pd.to_datetime(df[tarih_kolonu], unit="ms")
      df = df.sort_values("tarih")
      veriler[etiket] = (df, deger_kolonu, renk)
      print(f"Başarıyla veri çekildi: {etiket} ({len(df)} gün)")
    except Exception as e:
      print(f"Veri çekme hatası ({etiket}): {e}")

  if not veriler:
    print(
        "PortWatch verileri API'den okunamadı, grafik çizimi atlanıyor."
    )
    return

  # Matplotlib ile grafik üretimi
  plt.figure(figsize=(9, 4.5))
  for etiket, (df, deger_kolonu, renk) in veriler.items():
    plt.plot(
        df["tarih"],
        df[deger_kolonu],
        label=etiket,
        color=renk,
        linewidth=2,
        marker="o",
        markersize=4,
    )

  plt.title("IMF PortWatch - Günlük Gemi Geçiş Sayıları (Son 30 Gün)")
  plt.xlabel("Tarih")
  plt.ylabel("Gemi Sayısı")
  plt.grid(True, linestyle="--", alpha=0.5)
  plt.legend()
  plt.xticks(rotation=25)
  plt.tight_layout()

  # RAM üzerinde PNG tamponlama
  buf = io.BytesIO()
  plt.savefig(buf, format="png", dpi=130)
  buf.seek(0)
  plt.close()

  # Telegram'a fotoğraf olarak gönderme
  send_photo_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
  caption = (
      "🚢 <b>IMF PortWatch Deniz Trafiği Raporu</b>\n"
      "Babülmendep ve Süveyş Kanalı son 30 günlük günlük gemi geçiş grafiği."
  )

  files = {"photo": ("portwatch.png", buf, "image/png")}
  data = {"chat_id": CHAT_ID, "caption": caption, "parse_mode": "HTML"}

  telegram_res = requests.post(
      send_photo_url, data=data, files=files, timeout=30
  )
  print(
      "PortWatch Telegram Yanıtı:",
      telegram_res.status_code,
      telegram_res.text,
  )


if __name__ == "__main__":
  report = get_market_summary()
  send_telegram(report)
  send_portwatch_chart()
