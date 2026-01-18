import os
import requests
from supabase import create_client

# 1. Obtener el secreto único y separarlo
raw_keys = os.getenv("LLAVES_PROYECTO")

if not raw_keys:
    raise ValueError("Error: No se detectó el secret LLAVES1 en GitHub.")

# Separamos por la coma
try:
    lista_llaves = raw_keys.split(",")
    GEMINI_KEY = lista_llaves[0]
    FIRECRAWL_KEY = lista_llaves[1]
    SUPABASE_URL = lista_llaves[2]
    SUPABASE_KEY = lista_llaves[3]
except IndexError:
    raise ValueError("Error: El formato de LLAVES1 es incorrecto. Debe ser: GEMINI,FIRE,URL,KEY")

# 2. Conectar a Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

DIARIOS = [
    "https://www.latercera.com", "https://elpais.com", "https://www.lanacion.com.ar",
    "https://www.folha.uol.com.br", "https://www.chinadaily.com.cn", "https://www.hurriyetdailynews.com"
]

def ejecutar():
    print("🚀 Iniciando escaneo geopolítico...")
    # Usamos la ruta v1 que es la más estable
    gem_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"

    for url in DIARIOS:
        print(f"📡 Procesando: {url}")
        try:
            # Extracción
            res_fire = requests.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers={"Authorization": f"Bearer {FIRECRAWL_KEY}"},
                json={"url": url, "formats": ["markdown"]}
            )
            contenido = res_fire.json().get('data', {}).get('markdown', '')[:8000]

            if not contenido: continue

            # IA
            prompt = f"Analiza este contenido de {url} y resume las 5 noticias más importantes de GEOPOLÍTICA y negocios en español."
            payload = {"contents": [{"parts": [{"text": prompt + "\n\nCONTENIDO:\n" + contenido}]}]}
            res_gem = requests.post(gem_url, json=payload)
            
            if res_gem.status_code == 200:
                reporte = res_gem.json()['candidates'][0]['content']['parts'][0]['text']
                # Guardar
                supabase.table("noticias").insert({"medio": url, "resumen": reporte}).execute()
                print("✅ Guardado.")
            else:
                print(f"❌ Error Gemini: {res_gem.text}")

        except Exception as e:
            print(f"❌ Error en {url}: {e}")

if __name__ == "__main__":
    ejecutar()
