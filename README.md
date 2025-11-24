TurtleBot3 Workspace con Comandi Vocali

Questo è un fork del workspace TurtleBot3 arricchito con un sistema di controllo vocale e script di installazione automatica per ROS2 Humble.

🚀 Installazione e Avvio Rapido

Non serve configurare manualmente il workspace. Lo script installa le dipendenze, compila il codice e avvia la simulazione automaticamente.

1. Clona la repository
```
git clone https://github.com/labate001-byte/Vocal_Workspace.git
cd Vocal_Workspace
```

2. Installa le dipendeze dell'api Gemini
```
pip install google-generativeai python-dotenv
```
3. Iserisci la chiave api
```
nano /src/turtlebot_controller/script_python/.env
```
4. Avvia tutto

Esegui semplicemente lo script universale:

```
bash avvio/Avvio.sh
```


Lo script farà tutto da solo:

✅ Controllerà e installerà le dipendenze (rosdep).

🏗️ Compilerà il workspace (colcon build).

🐢 Avvierà Gazebo e Rviz.

🎙️ Avvierà i nodi di controllo (incluso il comando vocale).

🎙️ Comandi Vocali Disponibili

Una volta avviato il nodo vocale (terminale "Comando Vocale"), puoi dire:

"Vieni qui" o altri comandi di uguale significato: Gemini deciderà se il comando è valido in base al contesto

🛠️ Requisiti

Ubuntu 22.04

Seguire la guida originale di Tetano02

