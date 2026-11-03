import os
import pandas as pd
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
    # Token istemeyen doğrudan açık veri CSV kaynağı
    csv_url = "https://raw.githubusercontent.com/datasets/portwatch-chokepoints/main/daily_chokepoints.csv"
    fallback_url = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query?where=1%3D1&outFields=*&f=json&resultRecordCount=1000"

    print("--- Veri Çekiliyor ---")
    df = None

    # 1. Öncelik: Hızlı ve engelsiz açık CSV
    try:
        df = pd.read_csv(csv_url)
        print("CSV kaynağından veri başarıyla alındı.")
    except Exception as e:
        print("CSV alınamadı, alternatif deneniyor:", e)

    # 2. Alternatif: IMF PortWatch açık API aynası
    if df is None or df.empty:
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(fallback_url, headers=headers, timeout=20)
            data = r.json()
            features = data.get("features", [])
            if features:
                records = [f["attributes"] for f in features]
                df = pd.DataFrame(records)
                print("Alternatif API kaynağından veri alındı.")
        except Exception as e:
            print("Alternatif kaynak hatası:", e)

    if df is None or df.empty:
        print("Veri kaynağına ulaşılamadı.")
        return

    # Sütun isimlerini küçük harfe çekerek standartlaştır
    df.columns = [c.lower() for c in df.columns]

    # Tarihe göre en güncelden eskiye sırala
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date", ascending=False)

    noktalar = [
        ("Süveyş Kanalı", ["chokepoint1", "suez"]),
        ("Babülmendep Boğazı", ["chokepoint2", "bab_el_mandeb", "mandeb"]),
        ("Hürmüz Boğazı", ["chokepoint6", "chokepoint3", "hormuz"]),
        ("Ümit Burnu", ["chokepoint8", "chokepoint5", "cape_of_good_hope"]),
    ]

    mesajlar = ["🚢 <b>IMF PortWatch Deniz Trafiği Raporu</b>\n"]
    bulunan = 0

    id_col = "portid" if "portid" in df.columns else ("chokepoint" if "chokepoint" in df.columns else None)

    for etiket, anahtarlar in noktalar:
        satir = None
        if id_col:
            for k in anahtarlar:
                alt_df = df[df[id_col].astype(str).str.lower() == k.lower()]
                if not alt_df.empty:
                    satir = alt_df.iloc[0]
                    break

        if satir is not None:
            toplam = satir.get("n_total") or satir.get("transit_calls") or 0
            tanker = satir.get("n_tanker") or satir.get("tanker_calls") or 0
            konteyner = satir.get("n_container") or satir.get("container_calls") or 0
            kuru = satir.get("n_dry_bulk") or satir.get("dry_bulk_calls") or 0

            mesajlar.append(f"⚓ <b>{etiket}</b> (Toplam: {int(toplam)})")
            mesajlar.append(
                f"  ▫️ Tanker: {int(tanker)} | Konteyner: {int(konteyner)} | Kuru Yük: {int(kuru)}\n"
            )
            bulunan += 1

    if bulunan > 0:
        mesajlar.append(
            "📊 <b>Detaylı Grafikler ve Canlı Panel:</b>\n👉 https://ismail-piyasa.streamlit.app/"
        )
        send_telegram("\n".join(mesajlar))
        print(f"Başarılı: {bulunan} boğaz Telegram'a gönderildi.")
    else:
        print("Boğazlar filtrelenemedi.")


if __name__ == "__main__":
    main()
