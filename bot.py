import os
import pandas as pd
import requests
import yfinance as yf

# Telegram Ayarları
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

DASHBOARD_URL = "https://ismail-piyasa.streamlit.app/"

# IMF PortWatch Resmi Doğrudan Açık Veri Linki
PORTWATCH_CSV_URL = "https://raw.githubusercontent.com/IMF-PortWatch/PortWatch-data/main/data/daily_chokepoints_data.csv"


def get_portwatch_summary():
  """PortWatch açık CSV verisini doğrudan indirir ve son günün sayılarını çeker."""
  try:
    df = pd.read_csv(PORTWATCH_CSV_URL)
    df.columns = [c.lower() for c in df.columns]

    # Tarihe göre en güncel olanı sırala
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date", ascending=False)

    noktalar = [
        ("suez", "Süveyş Kanalı"),
        ("bab el-mandeb", "Babülmendep Boğazı"),
        ("hormuz", "Hürmüz Boğazı"),
        ("cape of good hope", "Ümit Burnu"),
    ]

    mesaj = ["\n🚢 <b>Boğaz ve Koridor Gemi Trafiği (Son Gün)</b>"]

    for anahtar, etiket in noktalar:
      # İsme göre filtrele
      alt_df = df[df["name"].str.lower().str.contains(anahtar, na=False)]
      if not alt_df.empty:
        son_satir = alt_df.iloc[0]
        toplam = int(
            son_satir.get("n_total", 0)
            or son_satir.get("transit_calls", 0)
            or 0
        )
        konteyner = int(son_satir.get("n_container", 0) or 0)
        tanker = int(son_satir.get("n_tanker", 0) or 0)
        kuru_yuk = int(son_satir.get("n_dry_bulk", 0) or 0)

        mesaj.append(f"\n⚓ <b>{etiket}</b> (Toplam: {toplam})")
        mesaj.append(
            f"  ▫️ Konteyner: {konteyner} | Tanker: {tanker} | Kuru Yük:"
            f" {kuru_yuk}"
        )

    return "\n".join(mesaj)
  except Exception as e:
    print(f"PortWatch CSV Okuma Hatası: {e}")
    # Eğer GitHub raw URL geçici erişilemezse yedek mock veri döner, bot çökmez
    return ""


def get_market_summary():
  lines = ["📊 <b>Piyasa Özeti (Canlı)</b>\n"]
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
  gemi_metni = get_portwatch_summary()
  if gemi_metni:
    lines.append(gemi_metni)

  lines.append(
      f"\n📈 <b>Detaylı Grafikler ve 10 Yıllık Panel:</b>\n{DASHBOARD_URL}"
  )
  return "\n".join(lines)


def send_telegram(message_text):
  url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
  payload = {"chat_id": CHAT_ID, "text": message_text, "parse_mode": "HTML"}
  res = requests.post(url, json=payload, timeout=20)
  print("Telegram Yanıtı:", res.status_code, res.text)


if __name__ == "__main__":
  report = get_market_summary()
  send_telegram(report)
