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
    # Token istemeyen, halka açık güncel PortWatch transit servisi
    endpoint = "https://services9.arcgis.com/fqDgCAUbok0cvzq7/arcgis/rest/services/PortWatch_Chokepoints_Daily_Transit_Data/FeatureServer/0/query"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }

    # IMF PortWatch tablosunda kayıtlı metin adları ve ID'ler
    noktalar = [
        ("Süveyş Kanalı", ["Suez Canal", "suez", "chokepoint1"]),
        ("Babülmendep Boğazı", ["Bab el-Mandeb", "Bab el-Mandeb Strait", "bab_el_mandeb", "chokepoint2"]),
        ("Hürmüz Boğazı", ["Strait of Hormuz", "Hormuz", "hormuz", "chokepoint6", "chokepoint3"]),
        ("Ümit Burnu", ["Cape of Good Hope", "cape_of_good_hope", "chokepoint8", "chokepoint5"]),
    ]

    mesajlar = ["🚢 <b>IMF PortWatch Deniz Trafiği Raporu</b>\n"]
    bulunan = 0

    for etiket, filtreler in noktalar:
        kayit = None
        for term in filtreler:
            # Hem isim (chokepoint_name/name) hem kod (chokepoint/portid) alanlarında arar
            where_clause = (
                f"(chokepoint_name='{term}' OR name='{term}' OR "
                f"chokepoint='{term}' OR portid='{term}') AND (n_total > 0 OR transit_calls > 0)"
            )
            params = {
                "where": where_clause,
                "outFields": "*",
                "orderByFields": "date DESC",
                "resultRecordCount": 1,
                "f": "json",
            }
            try:
                r = requests.get(endpoint, params=params, headers=headers, timeout=15)
                if r.status_code == 200:
                    data = r.json()
                    features = data.get("features", [])
                    if features:
                        kayit = features[0].get("attributes", {})
                        break
            except Exception:
                pass

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
            print(f"{etiket} için kayıt bulunamadı.")

    if bulunan > 0:
        mesajlar.append(
            "📊 <b>Detaylı Grafikler ve Canlı Panel:</b>\n👉 https://ismail-piyasa.streamlit.app/"
        )
        send_telegram("\n".join(mesajlar))
        print(f"Başarılı: {bulunan} boğaz Telegram'a iletildi.")
    else:
        print("Boğaz verisi çekilemedi.")


if __name__ == "__main__":
    main()
