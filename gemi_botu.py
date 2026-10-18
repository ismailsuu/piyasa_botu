import os
import requests

# Mevcut bot ve grup bilgileriniz
BOT_TOKEN = "8609292057:AAEzjrPio_7af5lZWnwBI4fY6YX-16oB4mE"
CHAT_ID = "-5347011483"


def get_portwatch_stats():
  """IMF PortWatch servisinden boğaz verilerini çeker."""
  endpoint = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"

  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      ),
      "Referer": "https://portwatch.imf.org/",
      "Accept": "application/json",
  }

  chokepoints = [
      ("chokepoint1", "Süveyş Kanalı"),
      ("chokepoint2", "Babülmendep Boğazı"),
      ("chokepoint6", "Hürmüz Boğazı"),
  ]

  mesaj = ["🚢 <b>IMF PortWatch Deniz Trafiği Raporu</b>\n"]
  bulundu = False

  for pid, etiket in chokepoints:
    params = {
        "where": f"portid='{pid}'",
        "outFields": "date,n_total,n_tanker,n_container,n_dry_bulk",
        "orderByFields": "date desc",
        "resultRecordCount": 1,
        "returnGeometry": "false",
        "f": "pjson",
    }
    try:
      res = requests.get(endpoint, params=params, headers=headers, timeout=12)
      data = res.json()
      features = data.get("features", [])

      if features:
        attr = features[0]["attributes"]
        toplam = attr.get("n_total") or 0
        tanker = attr.get("n_tanker") or 0
        konteyner = attr.get("n_container") or 0
        kuru = attr.get("n_dry_bulk") or 0

        mesaj.append(f"⚓ <b>{etiket}</b> (Toplam: {int(toplam)})")
        mesaj.append(
            f"  ▫️ Tanker: {int(tanker)} | Konteyner: {int(konteyner)} | Kuru"
            f" Yük: {int(kuru)}\n"
        )
        bulundu = True
      else:
        print(f"Kayıt boş döndü: {etiket}")
    except Exception as e:
      print(f"Hata ({etiket}): {e}")

  return "\n".join(mesaj) if bulundu else ""


def send_telegram(mesaj_metni):
  url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
  payload = {"chat_id": CHAT_ID, "text": mesaj_metni, "parse_mode": "HTML"}
  res = requests.post(url, json=payload, timeout=20)
  print("Gemi Botu Telegram Yanıtı:", res.status_code, res.text)


if __name__ == "__main__":
  rapor = get_portwatch_stats()
  if rapor:
    send_telegram(rapor)
  else:
    print("Veri çekilemediği için Telegram mesajı atılmadı.")
