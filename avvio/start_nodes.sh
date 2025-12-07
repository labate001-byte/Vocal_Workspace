#!/bin/bash
# ===========================================
# Script per avviare i nodi TurtleBot3
# ===========================================

# 1. Recupera il percorso passato da Avvio.sh (che è il primo argomento $1)
# Se non viene passato nulla, usa la directory corrente
WORKDIR="${1:-$PWD}"

echo "Avvio nodi lavorando nella cartella: $WORKDIR"

# 2. PREP_CMD MODIFICATO:
# Ho RIMOSSO 'colcon build'. Non serve ricompilare qui, lo ha già fatto Avvio.sh.
# Questo elimina l'errore "Duplicate package names".
PREP_CMD="source /opt/ros/humble/setup.bash && cd \"$WORKDIR\" && source install/setup.bash"

# 1️⃣ Nodo distanza
#gnome-terminal --title="Distanza" -- bash -c "$PREP_CMD && echo '✅ Nodo distanza avviato' && ros2 run turtlebot_controller turtle_distance_publisher; exec bash"

# 2️⃣ Nodo CSV
#gnome-terminal --title="CSV Handler" -- bash -c "$PREP_CMD && echo '✅ Nodo CSV avviato' && ros2 run turtlebot_controller turtle_csv_handler; exec bash"

# 3️⃣ Nodo movimento
gnome-terminal --title="Movimento" -- bash -c "$PREP_CMD && echo '✅ Nodo movimento avviato' && ros2 run turtlebot_controller move_turtle_AB; exec bash"

# 4️⃣ Nodo vocale (CON FILTRO SOLO INFO)
# Usiamo grep per mostrare SOLO le righe che contengono "[INFO]"
# 2>&1 reindirizza gli errori nello standard output per poterli filtrare
gnome-terminal --title="Comando Vocale" -- bash -c "$PREP_CMD && \
    echo '⏳ Attendo 3 secondi...' && sleep 3 && \
    echo '🎙️ NODO VOCALE ATTIVO (Mostro solo [INFO])' && \
    ros2 run turtlebot_controller voice_interface 2>&1 | grep --line-buffered '\[INFO\]' \
    || echo 'ERRORE FATALE'; \
    exec bash"

# 5️⃣ (opzionale) Terminale libero
#gnome-terminal --title="Terminale Libero" -- bash -c "$PREP_CMD && echo '🧩 Terminale libero per comandi ROS'; exec bash"

echo "==========================================="
echo "🔥 Tutti i nodi sono stati avviati."
echo "==========================================="
