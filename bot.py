import os
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

# Özel Streamlit panel adresiniz
DASHBOARD_URL = "https://ismail-piyasa.streamlit.app/"


def get_portwatch_detailed_summary():
  """PortWatch'tan Süveyş, Babülmendep, Hürmüz ve Ümit Burnu için

  Konteyner, Tanker, Kuru Yük ve Toplam gemi adetlerini çeker.
  """
  url = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"
  headers = {"User-Agent": "Mozilla/5.0"}

  # Takip edilecek kritik boğazlar ve isim filtreleri
  noktalar = [
      ("Suez", "Süveyş Kanalı"),
      ("Bab el-Mandeb", "Babülmendep Boğazı"),
      ("Hormuz", "Hürmüz Boğazı"),
      ("Cape of Good Hope", "Ümit Burnu"),
  ]

  mesaj_satirlari = ["\n🚢 <b>Boğaz ve Koridor Gemi Trafiği (Son Gün)</b>"]
  bulunan_veri_sayisi = 0

  for anahtar, etiket in noktalar:
    params = {
        "where": f"name LIKE '%{anahtar}%'",
        "outFields": "n_total,transit_calls,n_container,n_tanker,n_dry_bulk",
        "orderByFields": "date DESC",
        "resultRecordCount": 1,
        "f": "json",
    }
    try:
      r = requests.get(url, params=params, headers=headers, timeout=12).json()
      features = r.get("features", [])
      if features:
        attr = features[0]["attributes"]
        # Toplam gemi sayısı (n_total veya transit_calls)
        toplam = attr.get("n_total") or attr.get("transit_calls") or 0
        konteyner = attr.get("n_container") or 0
        tanker = attr.get("n_tanker") or 0
        kuru_yuk = attr.get("n_dry_bulk") or 0

        mesaj_satirlari.append(f"\n⚓ <b>{etiket}</b> (Toplam: {int(toplam)})")
        mesaj_satirlari.append(
            f"  ▫️ Konteyner: {int(konteyner)} | Tanker: {int(tanker)} | Kuru"
            f" Yük: {int(kuru_yuk)}"
        )
        bulunan_veri_sayisi += 1
      else:
        mesaj_satirlari.append(f"\n⚓ <b>{etiket}</b>: Veri bulunamadı")
    except Exception as e:
      print(f"Hata ({etiket}): {e}")

  return "\n".join(mesaj_satirlari) if bulunan_veri_sayisi > 0 else ""


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

  # Gemi & Boğaz detay verilerini ekle
  gemi_metni = get_portwatch_detailed_summary()
  if gemi_metni:
    lines.append(gemi_metni)

  # Streamlit Dashboard linkini ekle
  lines.append(
      f"\n📈 <b>Detaylı Grafikler ve 10 Yıllık Panel:</b>\n{DASHBOARD_URL}"
  )
  return "\n".join(lines)


def send_telegram(message_text):
  url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
  payload = {
      "chat_id": CHAT_ID,
      "text": message_text,
      "parse_mode": "HTML",  # Kalın yazı ve liste formatı için HTML modu
  }
  res = requests.post(url, json=payload, timeout=20)
  print("Telegram Yanıtı:", res.status_code, res.text)


if __name__ == "__main__":
  report = get_market_summary()
  send_telegram(report)
