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
    # Token istemeyen, doğrudan IMF PortWatch açık API servisi
    endpoint = "https://portwatch.imf.org/api/v1/chokepoints/daily"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }

    noktalar = [
        ("Süveyş Kanalı", ["suez", "chokepoint1"]),
        ("Babülmendep Boğazı", ["bab_el_mandeb", "chokepoint2"]),
        ("Hürmüz Boğazı", ["hormuz", "chokepoint6", "chokepoint3"]),
        ("Ümit Burnu", ["cape_of_good_hope", "chokepoint8", "chokepoint5"]),
    ]

    mesajlar = ["🚢 <b>IMF PortWatch Deniz Trafiği Raporu</b>\n"]
    bulunan = 0

    try:
        r = requests.get(endpoint, headers=headers, timeout=20)
        if r.status_code == 200:
            data = r.json()
            # Liste formatında veya dict formatında gelebilir
            records = data if isinstance(data, list) else data.get("data", data.get("features", []))

            for etiket, anahtarlar in noktalar:
                satir = None
                for rec in records:
                    item = rec.get("attributes", rec)
                    # ID veya isim eşleşmesi kontrolü
                    item_id = str(item.get("chokepoint") or item.get("portid") or item.get("name") or "").lower()
                    if any(k.lower() in item_id for k in anahtarlar):
                        if (item.get("n_total") or item.get("total") or item.get("transit_calls") or 0) > 0:
                            satir = item
                            break

                if satir:
                    toplam = satir.get("n_total") or satir.get("total") or satir.get("transit_calls") or 0
                    tanker = satir.get("n_tanker") or satir.get("tanker") or satir.get("tanker_calls") or 0
                    konteyner = satir.get("n_container") or satir.get("container") or satir.get("container_calls") or 0
                    kuru = satir.get("n_dry_bulk") or satir.get("dry_bulk") or satir.get("dry_bulk_calls") or 0

                    mesajlar.append(f"⚓ <b>{etiket}</b> (Toplam: {int(toplam)})")
                    mesajlar.append(
                        f"  ▫️ Tanker: {int(tanker)} | Konteyner: {int(konteyner)} | Kuru Yük: {int(kuru)}\n"
                    )
                    bulunan += 1
                else:
                    print(f"{etiket} için eşleşen kayıt bulunamadı.")
        else:
            print("HTTP İstek Hatası:", r.status_code)
    except Exception as e:
        print("Bağlantı hatası:", e)

    if bulunan > 0:
        mesajlar.append(
            "📊 <b>Detaylı Grafikler ve Canlı Panel:</b>\n👉 https://ismail-piyasa.streamlit.app/"
        )
        send_telegram("\n".join(mesajlar))
        print(f"Başarılı: {bulunan} boğaz Telegram'a iletildi.")
    else:
        print("Kritik: Boğaz verisi alınamadı.")


if __name__ == "__main__":
    main()
