#!/bin/bash

# ===========================================
# Script Universale per TurtleBot3 su ROS2 Humble
# Posizione: cartella 'avvio' dentro la root del workspace
# ===========================================

# 1. Ottiene la directory dove si trova QUESTO script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 2. Calcola la root del workspace (padre di 'avvio')
WORKSPACE_PATH="$(dirname "$SCRIPT_DIR")"

set -e  # Interrompe l’esecuzione in caso di errore

echo "==========================================="
echo "📂 Script avviato da: $SCRIPT_DIR"
echo "📂 Root Workspace rilevata in: $WORKSPACE_PATH"
echo "🔧 Preparazione dell'ambiente ROS2 Humble..."
echo "==========================================="

# --- GESTIONE API KEY GEMINI (NUOVO BLOCCO) ---
TARGET_ENV_DIR="$WORKSPACE_PATH/src/turtlebot_controller/script_python"
ENV_FILE="$TARGET_ENV_DIR/.env"

echo
echo "🔑 Controllo Configurazione API Key..."

# Verifica se il file .env esiste
if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  File .env non trovato in: $TARGET_ENV_DIR"
    echo "ℹ️  Il sistema vocale richiede una Google Gemini API Key."
    echo ""
    
    # Richiesta input utente
    read -p ">> Incolla qui la tua API Key e premi INVIO: " USER_KEY

    # Verifica input non vuoto
    if [ -z "$USER_KEY" ]; then
        echo "❌ Errore: Nessuna chiave inserita. Impossibile proseguire."
        exit 1
    fi

    # Creazione cartella se non esiste (sicurezza)
    mkdir -p "$TARGET_ENV_DIR"

    # Scrittura del file .env
    echo "GEMINI_API_KEY=$USER_KEY" > "$ENV_FILE"
    echo "✅ Chiave salvata con successo in: $ENV_FILE"
    echo "   (Non ti verrà più richiesta ai prossimi avvii)"
else
    echo "✅ File .env trovato. Configurazione presente."
fi
echo "==========================================="

# Source ROS2
if [ -f /opt/ros/humble/setup.bash ]; then
    source /opt/ros/humble/setup.bash
    echo "✅ ROS2 Humble caricato."
else
    echo "❌ Errore: /opt/ros/humble/setup.bash non trovato!"
    exit 1
fi

# Variabili TurtleBot3
export TURTLEBOT3_MODEL=waffle
export GAZEBO_MODEL_PATH=$GAZEBO_MODEL_PATH:/opt/ros/humble/share/turtlebot3_gazebo/models
export LIBGL_ALWAYS_SOFTWARE=0 
echo "✅ Variabili d'ambiente impostate."

if [ -f /usr/share/gazebo/setup.bash ]; then
    source /usr/share/gazebo/setup.bash
fi

echo
echo "==========================================="
echo "📦 Controllo Dipendenze (Rosdep) e Build..."
echo "==========================================="

cd "$WORKSPACE_PATH"

# Controlla se rosdep è stato inizializzato
if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then
    echo "⚠️  Rosdep non inizializzato. Eseguo 'sudo rosdep init' (inserisci psw)..."
    sudo rosdep init
    echo "🔄 Aggiornamento database rosdep..."
    rosdep update
else
    echo "✅ Rosdep già inizializzato."
fi

# Installazione dipendenze
if [ -d "src" ]; then
    echo "🔍 Installazione dipendenze mancanti..."
    rosdep install --from-paths src --ignore-src -r -y
else
    echo "❌ Errore: Cartella 'src' non trovata!"
    exit 1
fi

# Build
echo "🏗️  Eseguendo colcon build..."
colcon build --symlink-install

# Source del nuovo ambiente
if [ -f "install/setup.bash" ]; then
    source install/setup.bash
    echo "✅ Workspace buildato e caricato."
else
    echo "❌ Errore: setup.bash mancante."
    exit 1
fi

echo
echo "==========================================="
echo "🚀 Avvio della simulazione TurtleBot..."
echo "==========================================="

# Avvio simulazione
ros2 launch turtlebot_controller tb3_santanna_launch.py > logs_simulazione.txt 2>&1 &
SIM_PID=$!
echo "✅ Simulazione avviata (PID: $SIM_PID)."

sleep 8 

# Torna in 'avvio' per lanciare start_nodes
cd "$SCRIPT_DIR"

if [ -f "start_nodes.sh" ]; then
    echo "🧠 Trovato start_nodes.sh."
    chmod +x start_nodes.sh
    
    echo "⏳ Attendo 10 secondi per permettere al sistema di stabilizzarsi..."
    sleep 20
    
    echo "🚀 Avvio ora start_nodes.sh..."
    # Passiamo il WORKSPACE_PATH come argomento
    ./start_nodes.sh "$WORKSPACE_PATH"
else
    echo "⚠️  start_nodes.sh non trovato."
fi
