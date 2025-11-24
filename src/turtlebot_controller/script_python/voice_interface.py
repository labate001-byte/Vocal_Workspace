import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import os
import sys
import contextlib

# --- Integrazione Gemini ---
import google.generativeai as genai
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()

# --- Blocco per sopprimere l'output di errore ---
@contextlib.contextmanager
def suppress_stderr():
    """Un blocco 'with' per sopprimere stderr (avvisi ALSA/Jack)."""
    original_stderr_fd = os.dup(sys.stderr.fileno())
    devnull_fd = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull_fd, sys.stderr.fileno())
    try:
        yield
    finally:
        os.dup2(original_stderr_fd, sys.stderr.fileno())
        os.close(devnull_fd)
        os.close(original_stderr_fd)
# --- Fine blocco soppressione ---

# Importa la libreria rumorosa *dentro* il blocco di soppressione
with suppress_stderr():
    import speech_recognition as sr

class VoiceInterface(Node):
    def __init__(self):
        super().__init__('voice_interface')
        self.publisher_ = self.create_publisher(String, 'voice_command', 10)
        self.recognizer = sr.Recognizer()
        
        # --- Configurazione Gemini ---
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            self.get_logger().error("ERRORE: Variabile GEMINI_API_KEY non trovata nel file .env!")
        else:
            genai.configure(api_key=api_key)
            # Usiamo 'gemini-1.5-flash' perché è più veloce (minore latenza)
            self.model = genai.GenerativeModel('models/gemini-2.0-flash-lite')
            self.get_logger().info("Gemini AI configurato correttamente.")

        # Inizializza il microfono *dentro* il blocco di soppressione
        with suppress_stderr():
            self.microphone = sr.Microphone()
        
        self.get_logger().info("Nodo vocale pronto, in ascolto...")
        self.timer = self.create_timer(1.0, self.listen_loop)

    def ask_gemini(self, user_text):
        """Chiede a Gemini di interpretare l'intento dell'utente."""
        try:
            # Prompt engineering: istruiamo il modello a comportarsi come un classificatore
            prompt = f"""
            Sei il cervello di un robot mobile. Analizza il comando vocale dell'utente.
            
            Comando utente: "{user_text}"
            
            Regole:
            1. Se l'utente vuole che tu ti avvicini, che vada da lui, o lo raggiunga (es: "vieni qui", "avvicinati", "raggiungimi", "ehi vieni qua"), rispondi SOLO con la stringa: VIENI_QUI
            2. Se il comando non riguarda il movimento verso l'utente, rispondi SOLO con: NULL
            
            Rispondi solo con la parola chiave, niente altro.
            """
            
            response = self.model.generate_content(prompt)
            clean_response = response.text.strip().upper()
            return clean_response
        except Exception as e:
            self.get_logger().error(f"Errore chiamata Gemini: {e}")
            return "NULL"

    def listen_loop(self):
        with self.microphone as source:
            try:
                self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
                
                # Timeout breve per non bloccare il loop troppo a lungo
                with suppress_stderr():
                    audio = self.recognizer.listen(source, timeout=3)
                
                # Riconoscimento Speech-to-Text (Google base)
                text = self.recognizer.recognize_google(audio, language="it-IT")
                self.get_logger().info(f"Utente ha detto: {text}")
                
                # --- Analisi Semantica con Gemini ---
                intent = self.ask_gemini(text)
                
                if intent == "VIENI_QUI":
                    msg = String()
                    msg.data = "vieni_qui"
                    self.publisher_.publish(msg)
                    self.get_logger().info(f"✅ Gemini ha approvato il comando: {intent}")
                else:
                    self.get_logger().info(f"Gemini ha ignorato: {intent}")
            
            except sr.WaitTimeoutError:
                pass 
            except sr.UnknownValueError:
                pass 
            except sr.RequestError as e:
                self.get_logger().error(f"Errore servizio Speech Google: {e}")
            except Exception as e:
                self.get_logger().error(f"Errore generico: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = VoiceInterface()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
