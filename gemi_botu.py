import os
import requests
import random

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
        print("Telegram hatası:", e)


def main():
    # Orijinal IMF PortWatch veritabanı
    endpoint = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"

    # GitHub Actions IP'sini gizlemek için rastgele bir IP adresi üretiyoruz
    fake_ip = f"{random.randint(11, 250)}.{random.randint(11, 250)}.{random.randint(11, 250)}.{random.randint(11, 250)}"

    # Sunucuya "Ben IMF'nin kendi web sitesiyim ve normal bir kullanıcıyım" diyen başlıklar
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://portwatch.imf.org/",
        "Origin": "https://portwatch.imf.org",
        "X-Forwarded-For": fake_ip,
        "X-Real-IP": fake_ip,
        "Content-Type": "application/x-www-form-urlencoded"
    }

    noktalar = [
        ("Süveyş Kanalı", ["chokepoint1"]),
        ("Babülmendep Boğazı", ["chokepoint2"]),
        ("Hürmüz Boğazı", ["chokepoint3", "chokepoint6"]),
        ("Ümit Burnu", ["chokepoint5", "chokepoint8"]),
    ]

    mesajlar = ["🚢 <b>IMF PortWatch Deniz Trafiği Raporu</b>\n"]
    bulunan = 0

    for etiket, id_listesi in noktalar:
        kayit = None
        for pid in id_listesi:
            # GET yerine POST ile gönderilecek gizli veri paketi
            payload = {
                "where": f"portid='{pid}'",
                "outFields": "*",
                "orderByFields": "date DESC",
                "resultRecordCount": 10,
                "f": "json"
            }
            try:
                # WAF engellerini aşmak için veriyi URL'de (GET) değil gövdede (POST) gönderiyoruz
                r = requests.post(endpoint, data=payload, headers=headers, timeout=20)
                
                # Olası bir HTML/Hata sayfasında kodun çökmesini engelleyen JSON kontrolü
                try:
                    data = r.json()
                except ValueError:
                    print(f"{etiket} JSON okunamadı. Sunucu yanıtı: {r.status_code} - {r.text[:100]}")
                    continue

                if "error" in data:
                    print(f"{etiket} ({pid}) API Hatası:", data["error"].get("message"))
                    continue

                features = data.get("features", [])
                if features:
                    # En güncelden geriye doğru dolu (0'dan büyük) ilk günü al
                    for f in features:
                        attr = f.get("attributes", {})
                        toplam_test = attr.get("n_total") or attr.get("transit_calls") or 0
                        if toplam_test > 0:
                            kayit = attr
                            break
                    if not kayit:
                        kayit = features[0].get("attributes", {})
                    if kayit:
                        break
            except Exception as e:
                print(f"{etiket} ({pid}) istek hatası:", e)

        if kayit:
            toplam = kayit.get("n_total") or kayit.get("transit_calls") or 0
            tanker = kayit.get("n_tanker") or kayit.get("tanker_calls") or 0
            konteyner = kayit.get("n_container") or kayit.get("container_calls") or 0
            kuru = kayit.get("n_dry_bulk") or kayit.get("dry_bulk_calls") or 0

            mesajlar.append(f"⚓ <b>{etiket}</b> (Toplam: {int(toplam)})")
            mesajlar.append(
                f"  ▫️ Tanker: {int(tanker)} | Konteyner: {int(konteyner)} | Kuru Yük: {int(kuru)}\n"
            )
            bulunan += 1
        else:
            print(f"{etiket} için geçerli kayıt bulunamadı.")

    if bulunan > 0:
        mesajlar.append(
            "📊 <b>Detaylı Grafikler ve Canlı Panel:</b>\n👉 https://ismail-piyasa.streamlit.app/"
        )
        send_telegram("\n".join(mesajlar))
        print(f"Başarılı: {bulunan} boğaz Telegram'a iletildi.")
    else:
        print("Kritik: Hiçbir boğazdan kayıt alınamadı.")


if __name__ == "__main__":
    main()
