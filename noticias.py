import os
import requests
from supabase import create_client

# 1. Cargar LLAVES1 desde GitHub Secrets
raw_keys = os.getenv("LLAVES_PROYECTO")
if not raw_keys:
    raise ValueError("Error: No se encontró LLAVES1 en los Secrets.")

try:
    # Separamos las 4 llaves por la coma
    lista = raw_keys.split(",")
    GEMINI_KEY = lista[0].strip()
    FIRECRAWL_KEY = lista[1].strip()
    SUPABASE_URL = lista[2].strip()
    SUPABASE_KEY = lista[3].strip()
except:
    raise ValueError("Error: El formato de LLAVES1 debe ser: GEMINI,FIRE,URL,ANON")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

DIARIOS = [
    "https://www.latercera.com", "https://elpais.com", "https://www.folha.uol.com.br", 
    "https://www.chinadaily.com.cn", "https://www.hurriyetdailynews.com", "https://www.eluniversal.com.mx"
]

def ejecutar():
    print("🚀 Iniciando Radar Geopolítico...")
    gem_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"

    for url in DIARIOS:
        try:
            # Extracción limpia
            res_fire = requests.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers={"Authorization": f"Bearer {FIRECRAWL_KEY}"},
                json={"url": url, "formats": ["markdown"]}
            )
            markdown = res_fire.json().get('data', {}).get('markdown', '')[:10000]
            if not markdown: continue

            # IA con instrucciones de formato estricto
            prompt = f"""Analiza {url}. Selecciona la noticia más relevante de Geopolítica/Negocios.
            Responde ÚNICAMENTE en este formato:
            TITULO: [Título]
            BREVE: [Resumen de una línea]
            EXTENDIDO: [Análisis profundo de 2 o 3 párrafos]"""
            
            payload = {"contents": [{"parts": [{"text": prompt + "\n\nCONTENIDO:\n" + markdown}]}]}
            res_gem = requests.post(gem_url, json=payload)
            
            if res_gem.status_code == 200:
                texto_ia = res_gem.json()['candidates'][0]['content']['parts'][0]['text']
                # Guardamos en Supabase
                supabase.table("noticias").insert({"medio": url, "resumen": texto_ia}).execute()
                print(f"✅ {url} analizado.")

        except Exception as e:
            print(f"❌ Error en {url}: {e}")

if __name__ == "__main__":
    ejecutar()
