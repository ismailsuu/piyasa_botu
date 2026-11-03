import os
import requests

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram(mesaj):
    if not BOT_TOKEN or not CHAT_ID:
        print("Hata: TELEGRAM_TOKEN veya TELEGRAM_CHAT_ID bulunamadı!")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mesaj,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        res = requests.post(url, json=payload, timeout=15)
        print("Telegram Yanıtı:", res.status_code, res.text)
    except Exception as e:
        print("Telegram gönderim hatası:", e)


def main():
    endpoint = "https://services9.arcgis.com/fqDgCAUbok0cvzq7/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }

    print("--- 1. SERVİS BAĞLANTISI VE TABLO YAPISI KONTROL EDİLİYOR ---")
    # Filtresiz son 5 kaydı çekip gerçek sütun isimlerini görelim
    test_params = {
        "where": "1=1",
        "outFields": "*",
        "orderByFields": "date desc",
        "resultRecordCount": 5,
        "f": "json",
    }

    try:
        r = requests.get(endpoint, params=test_params, headers=headers, timeout=15)
        print("HTTP Kodu:", r.status_code)
        data = r.json()
        
        if "error" in data:
            print("API HATA DÖNDÜRDÜ:", data["error"])
            return

        features = data.get("features", [])
        if not features:
            print("Servisten hiç kayıt dönmedi!")
            return

        print("\nÖrnek Gelen İlk Kaydın Sütunları ve Değerleri:")
        ornek_attr = features[0].get("attributes", {})
        for k, v in ornek_attr.items():
            print(f"  {k}: {v}")

    except Exception as e:
        print("Genel Bağlantı Hatası:", e)
        return

    print("\n--- 2. BOĞAZLAR İÇİN VERİ ÇEKİLİYOR ---")

    # Boğaz adları
    hedefler = {
        "Süveyş Kanalı": ["suez", "chokepoint1"],
        "Babülmendep Boğazı": ["bab_el_mandeb", "mandeb", "chokepoint2"],
        "Hürmüz Boğazı": ["hormuz", "chokepoint6"],
        "Ümit Burnu": ["cape_of_good_hope", "good_hope", "chokepoint8"],
    }

    mesajlar = ["🚢 <b>IMF PortWatch Deniz Trafiği Raporu</b>\n"]
    bulunan = 0

    # Tek tek basit where sorguları atalım (OR kullanmadan)
    for etiket, anahtarlar in hedefler.items():
        kayit = None
        for key in anahtarlar:
            for field in ["chokepoint", "portid", "port_name"]:
                params = {
                    "where": f"LOWER({field}) LIKE '%{key.lower()}%'",
                    "outFields": "*",
                    "orderByFields": "date desc",
                    "resultRecordCount": 1,
                    "f": "json",
                }
                try:
                    res = requests.get(endpoint, params=params, headers=headers, timeout=10)
                    if res.status_code == 200:
                        j = res.json()
                        fts = j.get("features", [])
                        if fts:
                            kayit = fts[0].get("attributes", {})
                            print(f"[BAŞARILI] {etiket} -> Alan: {field}, Değer: {key}")
                            break
                except Exception:
                    pass
            if kayit:
                break

        if kayit:
            toplam = kayit.get("n_total") or kayit.get("transit_calls") or kayit.get("total_calls") or 0
            tanker = kayit.get("n_tanker") or kayit.get("tanker_calls") or kayit.get("tankers") or 0
            konteyner = kayit.get("n_container") or kayit.get("container_calls") or kayit.get("containers") or 0
            kuru = kayit.get("n_dry_bulk") or kayit.get("dry_bulk_calls") or kayit.get("cargo_calls") or 0

            mesajlar.append(f"⚓ <b>{etiket}</b> (Toplam: {int(toplam)})")
            mesajlar.append(
                f"  ▫️ Tanker: {int(tanker)} | Konteyner: {int(konteyner)} | Kuru Yük: {int(kuru)}\n"
            )
            bulunan += 1
        else:
            print(f"[BAŞARISIZ] {etiket} için hiçbir eşleşme bulunamadı.")

    if bulunan > 0:
        mesajlar.append(
            "📊 <b>Detaylı Grafikler ve Canlı Panel:</b>\n👉 https://ismail-piyasa.streamlit.app/"
        )
        send_telegram("\n".join(mesajlar))
        print("Telegram mesajı başarıyla gönderildi.")
    else:
        print("Hiçbir boğaz bulunamadı, Telegram mesajı tetiklenmedi.")


if __name__ == "__main__":
    main()
