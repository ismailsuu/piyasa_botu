import requests

endpoint = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"
headers = {"User-Agent": "Mozilla/5.0"}

# Sunucudan filtre koymadan en son 50 kaydı istiyoruz
params = {
    "where": "1=1",
    "outFields": "portid,date,n_total",
    "orderByFields": "date DESC",
    "resultRecordCount": 50,
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
    
    # Sunucuda yer alan tüm benzersiz portid değerlerini toplayalım
    bulunan_id_ler = set()
    for f in features:
        pid = f.get("attributes", {}).get("portid")
        if pid:
            bulunan_id_ler.add(pid)
            
    print("\n>>> SUNUCUDAKİ GERÇEK BOĞAZ ID'LERİ <<<")
    for pid in sorted(bulunan_id_ler):
        print(f"BULUNAN ID: {pid}")
