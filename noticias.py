import os
import requests
import json
from supabase import create_client

# --- CONFIGURACIÓN DE LLAVES (Seguridad con GitHub Secrets) ---
# El sistema buscará estos nombres en la configuración de tu repositorio
GEMINI_KEY = os.getenv("GEMINI_KEY")
FIRECRAWL_KEY = os.getenv("FIRECRAWL_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Verificación de seguridad básica
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Error: SUPABASE_URL y SUPABASE_KEY no detectados en los Secrets de GitHub.")

# Inicialización del cliente de Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

DIARIOS = [
    "https://www.latercera.com", "https://elpais.com", "https://www.lanacion.com.ar",
    "https://www.eluniverso.com", "https://www.eluniversal.com.mx",
    "https://www.folha.uol.com.br", "https://www.chinadaily.com.cn",
    "https://www.hurriyetdailynews.com"
]

def obtener_modelo_real():
    """Detecta el modelo exacto de Gemini habilitado para tu cuenta"""
    url = f"https://generativelanguage.googleapis.com/v1/models?key={GEMINI_KEY}"
    try:
        res = requests.get(url).json()
        if 'models' in res:
            modelos = [m['name'] for m in res['models'] if 'generateContent' in m['supportedGenerationMethods']]
            for m in modelos:
                if 'gemini-1.5-flash' in m: return m
            return modelos[0]
        return "models/gemini-1.5-flash"
    except:
        return "models/gemini-1.5-flash"

def ejecutar_escaneo():
    modelo_nombre = obtener_modelo_real()
    print(f"🚀 Iniciando escaneo geopolítico con {modelo_nombre}...")

    for url in DIARIOS:
        print(f"📡 Procesando: {url}...")
        try:
            # 1. Extracción de contenido
            res_fire = requests.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers={"Authorization": f"Bearer {FIRECRAWL_KEY}"},
                json={"url": url, "formats": ["markdown"]}
            )
            contenido = res_fire.json().get('data', {}).get('markdown', '')[:8000]

            if not contenido: continue

            # 2. Análisis con IA (Foco Geopolítica)
            gem_url = f"https://generativelanguage.googleapis.com/v1/{modelo_nombre}:generateContent?key={GEMINI_KEY}"
            prompt = f"Analiza el medio: {url}. Resume las 5 noticias más importantes con foco en GEOPOLÍTICA y negocios tangenciales en español."
            
            payload = {"contents": [{"parts": [{"text": prompt + "\n\nTEXTO:\n" + contenido}]}]}
            res_gem = requests.post(gem_url, json=payload)
            datos_gem = res_gem.json()

            if 'candidates' in datos_gem:
                reporte = datos_gem['candidates'][0]['content']['parts'][0]['text']
                # 3. Guardar en Supabase
                supabase.table("noticias").insert({"medio": url, "resumen": reporte, "categoria": "Geopolítica"}).execute()
                print(f"✅ Guardado con éxito.")

        except Exception as e:
            print(f"❌ Error técnico en {url}: {e}")

if __name__ == "__main__":
    ejecutar_escaneo()
