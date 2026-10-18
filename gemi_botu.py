import io
import matplotlib.pyplot as plt
import numpy as np
import requests

BOT_TOKEN = "8609292057:AAEzjrPio_7af5lZWnwBI4fY6YX-16oB4mE"
CHAT_ID = "-5347011483"


def create_traffic_chart(stats_data):
  """Boğazlara göre yük türlerini şık bir çubuk grafik haline getirir."""
  bogazlar = [item["etiket"] for item in stats_data]
  tanker = [item["tanker"] for item in stats_data]
  konteyner = [item["konteyner"] for item in stats_data]
  kuru = [item["kuru"] for item in stats_data]

  # Koyu modern tema
  plt.style.use("dark_background")
  fig, ax = plt.subplots(figsize=(9, 5), dpi=150)

  y = np.arange(len(bogazlar))
  h = 0.25

  # Çubuklar
  ax.barh(y - h, tanker, height=h, label="Tanker", color="#e74c3c")
  ax.barh(y, konteyner, height=h, label="Konteyner", color="#3498db")
  ax.barh(y + h, kuru, height=h, label="Kuru Yük", color="#f1c40f")

  ax.set_yticks(y)
  ax.set_yticklabels(bogazlar, fontsize=11, fontweight="bold")
  ax.invert_yaxis()  # Üstten aşağı sırala
  ax.set_xlabel("Günlük Gemi Sayısı", fontsize=10)
  ax.set_title("Kritik Boğazlar Gemi Geçiş Dağılımı", fontsize=13, pad=15)
  ax.legend(loc="lower right", framealpha=0.8)
  ax.grid(axis="x", linestyle="--", alpha=0.3)

  # Değer etiketlerini çubukların ucuna yaz
  for i in range(len(bogazlar)):
    if tanker[i] > 0:
      ax.text(
          tanker[i] + 1,
          i - h,
          str(tanker[i]),
          va="center",
          fontsize=9,
          color="#e74c3c",
      )
    if konteyner[i] > 0:
      ax.text(
          konteyner[i] + 1,
          i,
          str(konteyner[i]),
          va="center",
          fontsize=9,
          color="#3498db",
      )
    if kuru[i] > 0:
      ax.text(
          kuru[i] + 1,
          i + h,
          str(kuru[i]),
          va="center",
          fontsize=9,
          color="#f1c40f",
      )

  plt.tight_layout()

  buf = io.BytesIO()
  plt.savefig(buf, format="png", bbox_inches="tight")
  buf.seek(0)
  plt.close()
  return buf


def send_telegram_photo(photo_buf, caption):
  url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
  files = {"photo": ("chart.png", photo_buf, "image/png")}
  data = {"chat_id": CHAT_ID, "caption": caption, "parse_mode": "HTML"}
  res = requests.post(url, data=data, files=files, timeout=20)
  print("Telegram Yanıtı:", res.status_code)


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
      ("chokepoint2", "Babülmendep"),
      ("chokepoint6", "Hürmüz Boğazı"),
      ("chokepoint8", "Ümit Burnu"),
  ]

  mesaj_satirlari = ["🚢 <b>IMF PortWatch Deniz Trafiği Raporu</b>\n"]
  stats = []

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

          mesaj_satirlari.append(f"⚓ <b>{etiket}</b> (Toplam: {int(toplam)})")
          mesaj_satirlari.append(
              f"  ▫️ Tanker: {int(tanker)} | Konteyner: {int(konteyner)} | Kuru"
              f" Yük: {int(kuru)}\n"
          )

          stats.append({
              "etiket": etiket,
              "toplam": int(toplam),
              "tanker": int(tanker),
              "konteyner": int(konteyner),
              "kuru": int(kuru),
          })
    except Exception as e:
      print(f"{etiket} hatası: {e}")

  if stats:
    caption_text = "\n".join(mesaj_satirlari)
    chart_buffer = create_traffic_chart(stats)
    send_telegram_photo(chart_buffer, caption_text)


if __name__ == "__main__":
  main()
