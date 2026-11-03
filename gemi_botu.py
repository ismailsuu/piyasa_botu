import os
import io
import requests
import pandas as pd

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
    # IMF PortWatch resmi açık veri CSV indirme bağlantısı
    csv_url = "https://portwatch.imf.org/datasets/daily-transit-data.csv"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("--- IMF PortWatch Verisi İndiriliyor ---")
    df = None
    try:
        r = requests.get(csv_url, headers=headers, timeout=30)
        if r.status_code == 200:
            df = pd.read_csv(io.StringIO(r.text))
            print("CSV başarıyla yüklendi. Satır sayısı:", len(df))
        else:
            print("CSV indirme HTTP hatası:", r.status_code)
    except Exception as e:
        print("İndirme hatası:", e)

    if df is None or df.empty:
        print("Veri alınamadığı için işlem durduruldu.")
        return

    # Sütun isimlerini küçük harfe dönüştür
    df.columns = [c.lower() for c in df.columns]

    # Tarihe göre sırala
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date", ascending=False)

    # İlgili kimlik veya metin eşleştirmeleri
    noktalar = [
        ("Süveyş Kanalı", ["chokepoint1", "suez"]),
        ("Babülmendep Boğazı", ["chokepoint2", "bab_el_mandeb", "mandeb"]),
        ("Hürmüz Boğazı", ["chokepoint6", "chokepoint3", "hormuz"]),
        ("Ümit Burnu", ["chokepoint8", "chokepoint5", "cape_of_good_hope"]),
    ]

    id_col = None
    for col in ["portid", "chokepoint", "name", "chokepoint_name"]:
        if col in df.columns:
            id_col = col
            break

    if not id_col:
        print("ID sütunu bulunamadı. Tablodaki sütunlar:", list(df.columns))
        return

    mesajlar = ["🚢 <b>IMF PortWatch Deniz Trafiği Raporu</b>\n"]
    bulunan = 0

    for etiket, anahtarlar in noktalar:
        satir = None
        for key in anahtarlar:
            filtre = df[df[id_col].astype(str).str.lower().str.contains(key.lower(), na=False)]
            # Boş olmayan (n_total > 0) ilk geçerli günü bul
            filtre = filtre[filtre.get("n_total", 0) > 0]
            if not filtre.empty:
                satir = filtre.iloc[0]
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
        else:
            print(f"{etiket} için veri satırı bulunamadı.")

    if bulunan > 0:
        mesajlar.append(
            "📊 <b>Detaylı Grafikler ve Canlı Panel:</b>\n👉 https://ismail-piyasa.streamlit.app/"
        )
        send_telegram("\n".join(mesajlar))
        print(f"Başarılı: {bulunan} boğaz Telegram'a iletildi.")
    else:
        print("Boğazlar ayrıştırılamadı.")


if __name__ == "__main__":
    main()
