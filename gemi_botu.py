import pandas as pd
import requests

BOT_TOKEN = "8609292057:AAEzjrPio_7af5lZWnwBI4fY6YX-16oB4mE"
CHAT_ID = "-5347011483"

# IMF PortWatch Resmi Doğrudan Açık Veri Kaynağı
CSV_URL = "https://raw.githubusercontent.com/IMF-PortWatch/PortWatch-data/main/data/daily_chokepoints_data.csv"


def get_portwatch_stats():
  try:
    # Veri setini doğrudan oku
    df = pd.read_csv(CSV_URL)
    df.columns = [c.lower() for c in df.columns]

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date", ascending=False)

    noktalar = [
        ("suez", "Süveyş Kanalı"),
        ("bab el-mandeb", "Babülmendep Boğazı"),
        ("hormuz", "Hürmüz Boğazı"),
        ("cape of good hope", "Ümit Burnu"),
    ]

    mesaj = ["🚢 <b>IMF PortWatch Deniz Trafiği Raporu</b>\n"]
    bulundu = False

    for anahtar, etiket in noktalar:
      alt_df = df[df["name"].str.lower().str.contains(anahtar, na=False)]
      if not alt_df.empty:
        satir = alt_df.iloc[0]
        toplam = int(
            satir.get("n_total", 0) or satir.get("transit_calls", 0) or 0
        )
        tanker = int(satir.get("n_tanker", 0) or 0)
        konteyner = int(satir.get("n_container", 0) or 0)
        kuru = int(satir.get("n_dry_bulk", 0) or 0)

        mesaj.append(f"⚓ <b>{etiket}</b> (Toplam: {toplam})")
        mesaj.append(
            f"  ▫️ Tanker: {tanker} | Konteyner: {konteyner} | Kuru: {kuru}\n"
        )
        bulundu = True

    return "\n".join(mesaj) if bulundu else ""
  except Exception as e:
    print(f"Hata detayı: {e}")
    return ""


def send_telegram(mesaj_metni):
  url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
  payload = {"chat_id": CHAT_ID, "text": mesaj_metni, "parse_mode": "HTML"}
  res = requests.post(url, json=payload, timeout=20)
  print("Telegram Yanıtı:", res.status_code, res.text)


if __name__ == "__main__":
  rapor = get_portwatch_stats()
  if rapor:
    send_telegram(rapor)
  else:
    print("Veri çekilemedi.")
