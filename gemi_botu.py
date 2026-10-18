import requests

BOT_TOKEN = "8609292057:AAEzjrPio_7af5lZWnwBI4fY6YX-16oB4mE"
CHAT_ID = "-5347011483"


def send_telegram(mesaj):
  url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
  payload = {
      "chat_id": CHAT_ID,
      "text": mesaj,
      "parse_mode": "HTML",
      "disable_web_page_preview": True,  # O devasa önizleme kartını kapatır, şık ve sade durur
  }
  res = requests.post(url, json=payload, timeout=15)
  print("Telegram Yanıtı:", res.status_code, res.text)


def main():
  endpoint = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"

  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
      ),
      "Accept": "application/json",
  }

  noktalar = [
      ("chokepoint1", "Süveyş Kanalı"),
      ("chokepoint2", "Babülmendep Boğazı"),
      ("chokepoint6", "Hürmüz Boğazı"),
      ("chokepoint8", "Ümit Burnu"),
  ]

  mesajlar = ["🚢 <b>IMF PortWatch Deniz Trafiği Raporu</b>\n"]
  bulunan = 0

  for pid, etiket in noktalar:
    params = {
        "where": f"portid='{pid}'",
        "outFields": "*",
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
          attr = features[0].get("attributes", {})

          toplam = (
              attr.get("n_total")
              or attr.get("transit_calls")
              or attr.get("total_calls")
              or 0
          )
          tanker = (
              attr.get("n_tanker")
              or attr.get("tanker_calls")
              or attr.get("tankers")
              or 0
          )
          konteyner = (
              attr.get("n_container")
              or attr.get("container_calls")
              or attr.get("containers")
              or 0
          )
          kuru = (
              attr.get("n_dry_bulk")
              or attr.get("dry_bulk_calls")
              or attr.get("cargo_calls")
              or 0
          )

          mesajlar.append(f"⚓ <b>{etiket}</b> (Toplam: {int(toplam)})")
          mesajlar.append(
              f"  ▫️ Tanker: {int(tanker)} | Konteyner: {int(konteyner)} | Kuru"
              f" Yük: {int(kuru)}\n"
          )
          bulunan += 1
    except Exception as e:
      print(f"{etiket} hatası: {e}")

  if bulunan > 0:
    # LİNK EN ALTA EKLENDİ:
    mesajlar.append(
        "📊 <b>Detaylı Grafikler ve Canlı Panel:</b>\n👉"
        " https://ismail-piyasa.streamlit.app/"
    )
    send_telegram("\n".join(mesajlar))


if __name__ == "__main__":
  main()
