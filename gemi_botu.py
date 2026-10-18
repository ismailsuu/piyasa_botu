import traceback
import pandas as pd
import requests

BOT_TOKEN = "8609292057:AAEzjrPio_7af5lZWnwBI4fY6YX-16oB4mE"
CHAT_ID = "-5347011483"


def send_telegram(mesaj):
  url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
  res = requests.post(
      url,
      json={"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "HTML"},
      timeout=15,
  )
  print("Telegram Yanıtı:", res.status_code, res.text)


def main():
  # IMF PortWatch resmi CSV açık veri yolu
  url = "https://raw.githubusercontent.com/IMF-PortWatch/PortWatch-data/main/data/daily_chokepoints_data.csv"

  try:
    print("CSV indiriliyor...")
    # Timeout ve user-agent ekleyerek istek atıyoruz
    res = requests.get(
        url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20
    )
    if res.status_code != 200:
      send_telegram(
          f"⚠️ PortWatch İndirme Hatası! HTTP Kodu: {res.status_code}"
      )
      return

    import io

    df = pd.read_csv(io.StringIO(res.text))
    df.columns = [c.lower() for c in df.columns]

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date", ascending=False)

    noktalar = [
        ("suez", "Süveyş Kanalı"),
        ("bab el-mandeb", "Babülmendep Boğazı"),
        ("hormuz", "Hürmüz Boğazı"),
        ("cape of good hope", "Ümit Burnu"),
    ]

    mesajlar = ["🚢 <b>IMF PortWatch Deniz Trafiği Raporu</b>\n"]
    bulunan = 0

    for anahtar, etiket in noktalar:
      alt_df = df[df["name"].str.lower().str.contains(anahtar, na=False)]
      if not alt_df.empty:
        satir = alt_df.iloc[0]
        toplam = int(
            satir.get("n_total", 0)
            or satir.get("transit_calls", 0)
            or 0
        )
        tanker = int(satir.get("n_tanker", 0) or 0)
        konteyner = int(satir.get("n_container", 0) or 0)
        kuru = int(satir.get("n_dry_bulk", 0) or 0)

        mesajlar.append(f"⚓ <b>{etiket}</b> (Toplam: {toplam})")
        mesajlar.append(
            f"  ▫️ Tanker: {tanker} | Konteyner: {konteyner} | Kuru: {kuru}\n"
        )
        bulunan += 1

    if bulunan > 0:
      send_telegram("\n".join(mesajlar))
    else:
      send_telegram(
          "⚠️ PortWatch tablosu indi ancak eşleşen boğaz ismi bulunamadı!"
      )

  except Exception as e:
    hata_metni = traceback.format_exc()
    print("HATA DETAYI:\n", hata_metni)
    send_telegram(
        f"❌ <b>gemi_botu.py Çalışırken Hata Aldı:</b>\n<code>{str(e)[:500]}</code>"
    )


if __name__ == "__main__":
  main()
