import os
import google.generativeai as genai
from dotenv import load_dotenv

print("--- TEST DIAGNOSTICO GEMINI 2.5 ---")
load_dotenv() 

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ Chiave non trovata nel .env")
    exit()

genai.configure(api_key=api_key)

try:
    # QUI STA LA CORREZIONE: niente 'self.'
    # Usiamo il modello veloce che hai trovato nella lista
    model = genai.GenerativeModel('models/gemini-2.5-flash')
    
    print("📡 Invio richiesta a Gemini 2.5 Flash...")
    response = model.generate_content("Scrivi solo la parola: FUNZIONA")
    
    print(f"✅ RISPOSTA RICEVUTA: {response.text}")
    print("🎉 Tutto perfetto! Ora puoi aggiornare il robot.")

except Exception as e:
    print(f"❌ ERRORE: {e}")
