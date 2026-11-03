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
        print("Telegram hatası:", e)


def main():
    endpoint = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }

    # Son işlenmiş 100 kaydı çekip içindeki tüm farklı boğazları tespit ediyoruz
    params = {
        "where": "n_total > 0",
        "outFields": "date,portid,port_name,n_total,n_tanker,n_container,n_dry_bulk",
        "orderByFields": "date DESC",
        "resultRecordCount": 100,
        "f": "json",
    }

    print("--- IMF PortWatch Sorgulanıyor ---")
    try:
        r = requests.get(endpoint, params=params, headers=headers, timeout=20)
        print("HTTP Kodu:", r.status_code)
        if r.status_code != 200:
            print("Sunucu Hatası:", r.text)
            return

        data = r.json()
        if "error" in data:
            print("ArcGIS Hatası:", data["error"])
            return

        features = data.get("features", [])
        print(f"Gelen toplam kayıt sayısı: {len(features)}")

        # Boğazları ID'lerine göre en güncel tekil kayıt olarak gruplayalım
        gorulen_noktalar = {}
        for f in features:
            attr = f.get("attributes", {})
            pid = attr.get("portid")
            if pid and pid not in gorulen_noktalar:
                gorulen_noktalar[pid] = attr

        print("\n--- SUNUCUDA BULUNAN BOĞAZLAR VE ID'LERİ ---")
        for pid, attr in gorulen_noktalar.items():
            print(f"ID: {pid} | İsim: {attr.get('port_name')} | Toplam: {attr.get('n_total')}")

        # Telegram için mesaj oluştur
        tr_adlar = {
            "chokepoint1": "Süveyş Kanalı",
            "chokepoint2": "Babülmendep Boğazı",
            "chokepoint3": "Hürmüz Boğazı",
            "chokepoint6": "Hürmüz Boğazı",
            "chokepoint5": "Ümit Burnu",
            "chokepoint8": "Ümit Burnu",
        }

        mesajlar = ["🚢 <b>IMF PortWatch Deniz Trafiği Raporu</b>\n"]
        eklenen = 0

        for pid, attr in gorulen_noktalar.items():
            etiket = tr_adlar.get(pid, attr.get("port_name", pid))
            toplam = attr.get("n_total") or 0
            tanker = attr.get("n_tanker") or 0
            konteyner = attr.get("n_container") or 0
            kuru = attr.get("n_dry_bulk") or 0

            mesajlar.append(f"⚓ <b>{etiket}</b> (Toplam: {int(toplam)})")
            mesajlar.append(
                f"  ▫️ Tanker: {int(tanker)} | Konteyner: {int(konteyner)} | Kuru Yük: {int(kuru)}\n"
            )
            eklenen += 1

        if eklenen > 0:
            mesajlar.append(
                "📊 <b>Detaylı Grafikler ve Canlı Panel:</b>\n👉 https://ismail-piyasa.streamlit.app/"
            )
            send_telegram("\n".join(mesajlar))
            print(f"{eklenen} adet nokta başarıyla Telegram'a gönderildi.")
        else:
            print("Hiçbir boğaz kaydı ayrıştırılamadı.")

    except Exception as e:
        print("Bağlantı/Çalışma Hatası:", e)


if __name__ == "__main__":
    main()
