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

# Carica le variabili d'ambiente (dal file .env generato dall'altro script)
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
        
        # --- CHECK API KEY (SOLO LETTURA) ---
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            self.get_logger().error("❌ API KEY MANCANTE!")
            self.get_logger().error("Assicurati di aver eseguito lo script di configurazione o di avere il file .env.")
            sys.exit(1)
            
        genai.configure(api_key=api_key)
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
        self.get_logger().info("ℹ️  Comandi: 'Pippo [azione]' o 'Pippo Stop'")

        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.6 

        self.timer = self.create_timer(0.01, self.listen_loop)
        self.is_processing = False

    def send_audio_to_gemini(self, audio_data):
        self.get_logger().info("📤 Analisi comando Gemini...")
        try:
            wav_bytes = audio_data.get_wav_data(convert_rate=16000, convert_width=2)
            
            prompt = """
            Ascolta l'audio e classifica l'intento per il robot.
            
            1. Ignora la parola "Pippo".
            2. Se senti "Stop", "Fermati", "Basta", "Spegni" -> output STOP_NODO.
            3. Altrimenti classifica la destinazione:
               - Letto -> VIENI_LETTO
               - Base/Home -> TORNA_BASE
               - Divano -> VAI_DIVANO
               - Bagno -> VAI_BAGNO
               - Cucina -> VAI_CUCINA
            
            Output JSON TASSATIVO:
            { "command": "VIENI_LETTO" | "TORNA_BASE" | "VAI_DIVANO" | "VAI_BAGNO" | "VAI_CUCINA" | "STOP_NODO" | "NULL" }
            """
            
            response = self.model.generate_content(
                [prompt, {"mime_type": "audio/wav", "data": wav_bytes}],
                request_options={"timeout": 5000}
            )
            
            cleaned = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned)

        except Exception as e:
            self.get_logger().error(f"❌ Errore Gemini: {e}")
            return None

    def listen_loop(self):
        if self.is_processing: return

        with self.microphone as source:
            try:
                self.is_processing = True
                try:
                    audio_clip = self.recognizer.listen(source, timeout=1.0, phrase_time_limit=5)
                except sr.WaitTimeoutError:
                    return 

                try:
                    rough_text = self.recognizer.recognize_google(audio_clip, language="it-IT").lower()
                except:
                    return

                wake_words = ["pippo", "pipo", "peppo", "pippa", "people", "tipo", "ehi"]
                
                if any(w in rough_text for w in wake_words):
                    self.get_logger().info(f"✅ Trigger: '{rough_text}'")
                    
                    result = self.send_audio_to_gemini(audio_clip)
                    
                    if result:
                        cmd = result.get("command", "NULL")
                        msg = String()
                        
                        if cmd == "STOP_NODO":
                            self.get_logger().warn("🛑 COMANDO 'STOP' RICEVUTO. ARRESTO...")
                            raise SystemExit # Esce dal loop e va al blocco try/except del main
                            
                        elif cmd != "NULL":
                            msg.data = cmd.lower()
                            self.publisher_.publish(msg)
                            self.get_logger().info(f"🚀 Comando: {cmd}")
                        else:
                            self.get_logger().info("🤷 Comando non chiaro.")
                
            except SystemExit:
                raise
            except Exception as e:
                self.get_logger().error(f"Loop error: {e}")
            finally:
                self.is_processing = False

def main(args=None):
    rclpy.init(args=args)
    node = VoiceInterface()
    
    try:
        rclpy.spin(node)
    except SystemExit:
        node.get_logger().info("👋 Nodo terminato vocalmente.")
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == "__main__":
    main()
