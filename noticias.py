import os
import requests
from supabase import create_client

# 1. Configuración de Llaves (Separadas por coma en LLAVES1)
raw_keys = os.getenv("LLAVES_PROYECTO")
if not raw_keys: raise ValueError("Falta el Secret LLAVES1")

lista_llaves = raw_keys.split(",")
GEMINI_KEY, FIRECRAWL_KEY, SUPABASE_URL, SUPABASE_KEY = lista_llaves

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

DIARIOS = [
    "https://www.latercera.com", "https://elpais.com", "https://www.lanacion.com.ar",
    "https://www.folha.uol.com.br", "https://www.chinadaily.com.cn", "https://www.hurriyetdailynews.com",
    "https://www.eluniverso.com", "https://www.eluniversal.com.mx"
]

def ejecutar():
    print("🌍 Iniciando Escaneo de Alta Inteligencia...")
    gem_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"

    for url in DIARIOS:
        try:
            # Extracción
            res_fire = requests.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers={"Authorization": f"Bearer {FIRECRAWL_KEY}"},
                json={"url": url, "formats": ["markdown"]}
            )
            contenido = res_fire.json().get('data', {}).get('markdown', '')[:10000]
            if not contenido: continue

            # IA con formato estructurado
            prompt = f"""
            Analiza el contenido de {url}. 
            Selecciona la noticia de GEOPOLÍTICA o NEGOCIOS más importante.
            Devuelve el resultado estrictamente en este formato:
            TITULO: [Título breve]
            BREVE: [Resumen de 1 frase]
            EXTENDIDO: [Análisis profundo de 3 párrafos sobre implicaciones mundiales]
            """
            
            payload = {"contents": [{"parts": [{"text": prompt + "\n\nTEXTO:\n" + contenido}]}]}
            res_gem = requests.post(gem_url, json=payload)
            
            if res_gem.status_code == 200:
                raw_text = res_gem.json()['candidates'][0]['content']['parts'][0]['text']
                # Guardamos el bloque de texto completo; el HTML se encargará de separarlo
                supabase.table("noticias").insert({"medio": url, "resumen": raw_text}).execute()
                print(f"✅ Procesado: {url}")

        except Exception as e:
            print(f"❌ Error en {url}: {e}")

if __name__ == "__main__":
    ejecutar()
