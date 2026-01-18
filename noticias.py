import os
import requests
import json
from supabase import create_client

# --- CONFIGURACIÓN DE LLAVES (Segura para GitHub) ---
GEMINI_KEY = os.getenv("GEMINI_KEY")
FIRECRAWL_KEY = os.getenv("FIRECRAWL_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# El resto del código se mantiene exactamente igual...

# Inicialización de clientes
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

DIARIOS = [
    "https://www.latercera.com", "https://elpais.com", "https://www.lanacion.com.ar",
    "https://www.eluniverso.com", "https://www.eluniversal.com.mx",
    "https://www.folha.uol.com.br", "https://www.chinadaily.com.cn",
    "https://www.hurriyetdailynews.com"
]

def obtener_modelo_real():
    """Detecta el modelo exacto habilitado en tu cuenta de Google"""
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
    print(f"🚀 Iniciando motor con {modelo_nombre}...")
    print(f"📦 Conectado a Supabase: {SUPABASE_URL}\n")

    for url in DIARIOS:
        print(f"📡 Escaneando: {url}...")
        try:
            # 1. Extracción con Firecrawl
            res_fire = requests.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers={"Authorization": f"Bearer {FIRECRAWL_KEY}"},
                json={"url": url, "formats": ["markdown"]}
            )
            datos_fire = res_fire.json()
            contenido = datos_fire.get('data', {}).get('markdown', '')[:8000]

            if not contenido:
                print(f"⚠️ Sin contenido en {url}")
                continue

            # 2. Resumen con Gemini (Foco Geopolítica y Negocios)
            gem_url = f"https://generativelanguage.googleapis.com/v1/{modelo_nombre}:generateContent?key={GEMINI_KEY}"
            prompt = f"""
            Analiza el contenido de este diario: {url}.
            TAREA: Resume las 5 noticias más relevantes del momento.
            ENFOQUE: Prioridad absoluta a GEOPOLÍTICA y, de modo tangencial, nuevos negocios.
            IDIOMA: Español. Conciso (máximo 2 frases por noticia).
            CONTENIDO PARA ANALIZAR:
            {contenido}
            """
            
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            res_gem = requests.post(gem_url, json=payload)
            datos_gem = res_gem.json()

            if 'candidates' in datos_gem:
                reporte = datos_gem['candidates'][0]['content']['parts'][0]['text']
                
                # 3. Guardar en la tabla 'noticias' de Supabase
                data_insert = {
                    "medio": url,
                    "resumen": reporte,
                    "categoria": "Geopolítica y Negocios"
                }
                supabase.table("noticias").insert(data_insert).execute()
                
                print(f"✅ Reporte guardado exitosamente para {url}")
                print("-" * 40)
            else:
                print(f"❌ Error de IA en {url}: {json.dumps(datos_gem)}")

        except Exception as e:
            print(f"❌ Error técnico en {url}: {e}")

if __name__ == "__main__":
    ejecutar_escaneo()