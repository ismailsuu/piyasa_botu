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
  # PortWatch açık REST FeatureServer sorgusu
  endpoint = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"

  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
      ),
      "Accept": "application/json",
  }

  noktalar = [
      ("Suez", "Süveyş Kanalı"),
      ("Bab el-Mandeb", "Babülmendep Boğazı"),
      ("Hormuz", "Hürmüz Boğazı"),
      ("Cape of Good Hope", "Ümit Burnu"),
  ]

  mesajlar = ["🚢 <b>IMF PortWatch Deniz Trafiği Raporu</b>\n"]
  bulunan = 0

  for anahtar, etiket in noktalar:
    params = {
        "where": f"name LIKE '%{anahtar}%'",
        "outFields": "n_total,transit_calls,n_container,n_tanker,n_dry_bulk",
        "orderByFields": "date desc",
        "resultRecordCount": 1,
        "f": "json",
    }
    try:
      r = requests.get(endpoint, params=params, headers=headers, timeout=12)
      if r.status_code == 200:
        data = r.json()
        features = data.get("features", [])
        if features:
          attr = features[0]["attributes"]
          toplam = int(
              attr.get("n_total") or attr.get("transit_calls") or 0
          )
          tanker = int(attr.get("n_tanker") or 0)
          konteyner = int(attr.get("n_container") or 0)
          kuru = int(attr.get("n_dry_bulk") or 0)

          mesajlar.append(f"⚓ <b>{etiket}</b> (Toplam: {toplam})")
          mesajlar.append(
              f"  ▫️ Tanker: {tanker} | Konteyner: {konteyner} | Kuru: {kuru}\n"
          )
          bulunan += 1
    except Exception as e:
      print(f"{etiket} çekilemedi: {e}")

  if bulunan > 0:
    send_telegram("\n".join(mesajlar))
  else:
    send_telegram("⚠️ PortWatch verisine şu an ulaşılamadı.")


if __name__ == "__main__":
  main()
