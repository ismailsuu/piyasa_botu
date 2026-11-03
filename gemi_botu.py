import requests

# Şifre (Token) istemeyen güncel PortWatch servisi
endpoint = "https://services9.arcgis.com/fqDgCAUbok0cvzq7/arcgis/rest/services/PortWatch_Chokepoints_Daily_Transit_Data/FeatureServer/0/query"
headers = {"User-Agent": "Mozilla/5.0"}

params = {
    "where": "1=1",
    "outFields": "*",
    "orderByFields": "date DESC",
    "resultRecordCount": 30,
    "f": "json"
}

r = requests.get(endpoint, params=params, headers=headers, timeout=20)
print("HTTP Durumu:", r.status_code)
data = r.json()

if "error" in data:
    print("HATA:", data["error"])
else:
    features = data.get("features", [])
    print(f"Gelen Kayıt Sayısı: {len(features)}")
    
    if features:
        print("\n--- ÖRNEK 1 KAYDIN TÜM ALANLARI VE DEĞERLERİ ---")
        for k, v in features[0].get("attributes", {}).items():
            print(f"{k}: {v}")
            
        print("\n--- TABLODAKİ GEÇİT / BOĞAZ DEĞERLERİ ---")
        for f in features:
            attr = f.get("attributes", {})
            # Olası alanları ekrana yazdırıyoruz
            print("Row:", {k: v for k, v in attr.items() if k in ['portid', 'chokepoint', 'name', 'chokepoint_name', 'n_total', 'transit_calls']})
