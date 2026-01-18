import os
import requests
from supabase import create_client

# 1. Configuración de Seguridad
raw_keys = os.getenv("LLAVES_PROYECTO")
if not raw_keys: raise ValueError("Error: Falta el Secret LLAVES1")
llaves = [k.strip() for k in raw_keys.split(",")]
GEMINI_KEY, FIRECRAWL_KEY, SUPABASE_URL, SUPABASE_KEY = llaves

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

DIARIOS = [
    "https://www.latercera.com", "https://elpais.com", "https://www.lanacion.com.ar",
    "https://www.folha.uol.com.br", "https://www.chinadaily.com.cn", 
    "https://www.hurriyetdailynews.com", "https://www.eluniverso.com", "https://www.eluniversal.com.mx"
]

def ejecutar():
    print("📡 Iniciando radar de 6 noticias por medio...")
    gem_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"

    for url in DIARIOS:
        try:
            # Extracción
            res_fire = requests.post("https://api.firecrawl.dev/v1/scrape", 
                headers={"Authorization": f"Bearer {FIRECRAWL_KEY}"},
                json={"url": url, "formats": ["markdown"]})
            markdown = res_fire.json().get('data', {}).get('markdown', '')[:12000]
            if not markdown: continue

            # IA: Pedimos 6 noticias con separador claro
            prompt = f"""Analiza {url}. Extrae las 6 noticias más importantes de Geopolítica/Negocios.
            Para CADA noticia usa este formato exacto y sepáralas con '---NEWS---':
            TITULO: [Título real de la noticia]
            BREVE: [Resumen de 1 frase]
            EXTENDIDO: [Análisis profundo de 3 párrafos]"""
            
            payload = {"contents": [{"parts": [{"text": prompt + "\n\nCONTENIDO:\n" + markdown}]}]}
            res_gem = requests.post(gem_url, json=payload)
            
            if res_gem.status_code == 200:
                bloque_texto = res_gem.json()['candidates'][0]['content']['parts'][0]['text']
                noticias_separadas = bloque_texto.split('---NEWS---')
                
                for nota in noticias_separadas:
                    if "TITULO:" in nota:
                        supabase.table("noticias").insert({"medio": url, "resumen": nota.strip()}).execute()
                print(f"✅ 6 noticias guardadas de {url}")
        except Exception as e:
            print(f"❌ Error en {url}: {e}")

if __name__ == "__main__":
    ejecutar()
