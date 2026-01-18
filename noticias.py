import os
import requests
from supabase import create_client

# 1. Configuración de Llaves
raw_keys = os.getenv("LLAVES_PROYECTO")
if not raw_keys: raise ValueError("Falta el Secret LLAVES1")
GEMINI_KEY, FIRECRAWL_KEY, SUPABASE_URL, SUPABASE_KEY = raw_keys.split(",")

supabase = create_client(SUPABASE_URL.strip(), SUPABASE_KEY.strip())

# Lista completa de 8 diarios para máxima cobertura
DIARIOS = [
    "https://www.latercera.com", "https://elpais.com", "https://www.lanacion.com.ar",
    "https://www.folha.uol.com.br", "https://www.chinadaily.com.cn", 
    "https://www.hurriyetdailynews.com", "https://www.eluniverso.com", 
    "https://www.eluniversal.com.mx"
]

def ejecutar():
    print("🌍 Iniciando Escaneo de 6 noticias por diario...")
    gem_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY.strip()}"

    for url in DIARIOS:
        try:
            # Extracción de contenido
            res_fire = requests.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers={"Authorization": f"Bearer {FIRECRAWL_KEY.strip()}"},
                json={"url": url, "formats": ["markdown"]}
            )
            contenido = res_fire.json().get('data', {}).get('markdown', '')[:12000]
            if not contenido: continue

            # Pedimos a la IA 6 noticias estructuradas
            prompt = f"""
            Analiza el contenido de {url}. 
            Selecciona las 6 noticias de GEOPOLÍTICA o NEGOCIOS más importantes.
            Devuelve cada noticia separada por el símbolo '###'.
            Para cada noticia usa estrictamente este formato:
            TITULO: [Título breve y atractivo]
            BREVE: [Resumen de 1 frase]
            EXTENDIDO: [Análisis profundo de 3 párrafos]
            """
            
            payload = {"contents": [{"parts": [{"text": prompt + "\n\nTEXTO:\n" + contenido}]}]}
            res_gem = requests.post(gem_url, json=payload)
            
            if res_gem.status_code == 200:
                texto_completo = res_gem.json()['candidates'][0]['content']['parts'][0]['text']
                # Separamos las 6 noticias
                noticias = texto_completo.split('###')
                
                for nota in noticias:
                    if len(nota.strip()) > 50: # Evitar bloques vacíos
                        supabase.table("noticias").insert({"medio": url, "resumen": nota.strip()}).execute()
                
                print(f"✅ Procesadas 6 noticias de: {url}")

        except Exception as e:
            print(f"❌ Error en {url}: {e}")

if __name__ == "__main__":
    ejecutar()
