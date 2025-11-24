import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Chiave non trovata nel .env")
    exit()

genai.configure(api_key=api_key)

print("🔍 Cerco i modelli disponibili per la tua chiave...")

try:
    count = 0
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"✅ Trovato: {m.name}")
            count += 1
    
    if count == 0:
        print("⚠️ Nessun modello trovato. Potrebbe essere un problema di regione o permessi.")
        
except Exception as e:
    print(f"❌ Errore critico: {e}")
