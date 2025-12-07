import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import os
import sys
import time
import contextlib
import json
import google.generativeai as genai
from dotenv import load_dotenv
import speech_recognition as sr

load_dotenv()

# --- CONFIGURAZIONE ---
MIC_INDEX = None 

@contextlib.contextmanager
def suppress_stderr():
    original_stderr_fd = os.dup(sys.stderr.fileno())
    devnull_fd = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull_fd, sys.stderr.fileno())
    try:
        yield
    finally:
        os.dup2(original_stderr_fd, sys.stderr.fileno())
        os.close(devnull_fd)
        os.close(original_stderr_fd)

class VoiceInterface(Node):
    def __init__(self):
        super().__init__('voice_interface')
        self.publisher_ = self.create_publisher(String, 'voice_command', 10)
        self.recognizer = sr.Recognizer()
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            self.get_logger().error("ERRORE: API Key mancante!")
            sys.exit(1)
            
        genai.configure(api_key=api_key)
        
        # Modello Gemini
        self.model = genai.GenerativeModel('models/gemini-2.5-flash')

        try:
            self.microphone = sr.Microphone(device_index=MIC_INDEX, sample_rate=16000)
        except Exception as e:
            self.get_logger().error(f"Errore MIC: {e}")
            sys.exit(1)

        self.get_logger().info("🤫 Calibrazione silenzio (2 sec)...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=2.0)
            
        self.get_logger().info(f"✅ Pronti. Soglia: {self.recognizer.energy_threshold:.0f}")
        self.get_logger().info("ℹ️  Logica: 'Pippo' -> Audio a Gemini.")

        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.6 

        self.timer = self.create_timer(0.01, self.listen_loop)
        self.is_processing = False

    def send_audio_to_gemini(self, audio_data):
        self.get_logger().info("📤 Invio AUDIO GREZZO a Gemini 2.5...")
        try:
            wav_bytes = audio_data.get_wav_data(convert_rate=16000, convert_width=2)
            
            # --- MODIFICA AGGIORNATA: NUOVI LUOGHI ---
            prompt = """
            Ascolta questo audio e classifica l'intento per la navigazione del robot.
            
            Regole TASSATIVE:
            1. Ignora la parola "Pippo".
            2. Classifica i comandi in base alla destinazione richiesta:
               - "Letto", "Bed" -> VIENI_LETTO
               - "Base", "Ricarica", "Home" -> TORNA_BASE
               - "Divano", "Sofa" -> VAI_DIVANO
               - "Bagno", "Toilette", "WC" -> VAI_BAGNO
               - "Cucina", "Kitchen" -> VAI_CUCINA
               
            3. Se la richiesta è generica (es. "vieni qui", "avvicinati") o non chiara -> NULL.
            
            Restituisci SOLO JSON:
            { "detected_language": "codice", "command": "VIENI_LETTO" | "TORNA_BASE" | "VAI_DIVANO" | "VAI_BAGNO" | "VAI_CUCINA" | "NULL" }
            """
            
            response = self.model.generate_content(
                [prompt, {"mime_type": "audio/wav", "data": wav_bytes}],
                request_options={"timeout": 5000}
            )
            
            cleaned = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned)

        except Exception as e:
            self.get_logger().error(f"❌ Errore Gemini Audio: {e}")
            return None

    def listen_loop(self):
        if self.is_processing: return

        with self.microphone as source:
            try:
                self.is_processing = True
                
                try:
                    audio_clip = self.recognizer.listen(source, timeout=1.0, phrase_time_limit=6)
                except sr.WaitTimeoutError:
                    return 

                # Riconoscimento preliminare offline/rapido per la wake word
                try:
                    rough_text = self.recognizer.recognize_google(audio_clip, language="it-IT").lower()
                except sr.UnknownValueError:
                    return 
                except sr.RequestError:
                    return

                wake_words = ["pippo", "pipo", "peppo", "pippa", "people", "tipo", "ehi"]
                
                if any(w in rough_text for w in wake_words):
                    self.get_logger().info(f"✅ Trigger attivato: '{rough_text}'")
                    
                    result = self.send_audio_to_gemini(audio_clip)
                    
                    if result:
                        cmd = result.get("command", "NULL")
                        lang = result.get("detected_language", "?")
                        msg = String()
                        
                        # Gestione Comandi Aggiornata
                        if cmd == "VIENI_LETTO":
                            msg.data = "vieni_letto"
                            self.publisher_.publish(msg)
                            self.get_logger().info(f"🚑 [Gemini]: Destinazione LETTO")
                            
                        elif cmd == "TORNA_BASE":
                            msg.data = "torna_base"
                            self.publisher_.publish(msg)
                            self.get_logger().info(f"🏠 [Gemini]: Destinazione BASE")

                        elif cmd == "VAI_DIVANO":
                            msg.data = "vai_divano"
                            self.publisher_.publish(msg)
                            self.get_logger().info(f"🛋️ [Gemini]: Destinazione DIVANO")

                        elif cmd == "VAI_BAGNO":
                            msg.data = "vai_bagno"
                            self.publisher_.publish(msg)
                            self.get_logger().info(f"🚽 [Gemini]: Destinazione BAGNO")

                        elif cmd == "VAI_CUCINA":
                            msg.data = "vai_cucina"
                            self.publisher_.publish(msg)
                            self.get_logger().info(f"🍳 [Gemini]: Destinazione CUCINA")

                        else:
                            self.get_logger().info(f"✋ [Gemini]: Comando ignorato/generico ({cmd})")
                
            except Exception as e:
                self.get_logger().error(f"Loop crash: {e}")
            finally:
                self.is_processing = False

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
