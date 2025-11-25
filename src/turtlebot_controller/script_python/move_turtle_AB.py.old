import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from std_msgs.msg import Bool, String  # <-- Assicurati che 'String' sia importato
import time

# File esterni
from script_python.turtle_estimate_position import publish_initial_pose
from script_python.patient_button_control import button

class GoalNavigation(Node): 
    def __init__(self):
        super().__init__('goal_navigation')

        # Action client per navigazione
        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        # Publisher per stato di avanzamento
        self.move_status_publisher = self.create_publisher(Bool, '/move_status', 10)

        # --- QUESTA È LA PARTE MANCANTE ---
        # Subscriber per comandi vocali
        self.voice_subscriber = self.create_subscription(
            String,
            'voice_command',  # <-- Corretto (SENZA slash)
            self.voice_callback,
            10
        )
        # --- FINE PARTE MANCANTE ---

        # Flag destinazione
        self.at_destination = False
        # Home position
        self.home_x = -2.5
        self.home_y = -2.5
        self.home_theta = 0.0

        self.get_logger().info("Nodo di navigazione pronto (in attesa di comando vocale)...")

    # --- QUESTA È LA FUNZIONE MANCANTE ---
    # Callback comandi vocali
    def voice_callback(self, msg):
        if msg.data == "vieni_qui":
            self.get_logger().info("🚀 Comando vocale ricevuto: muovo il robot verso il paziente")
            # Goal predefinito verso il paziente
            self.send_goal(-1.0, 3.5, 0.0)
    # --- FINE FUNZIONE MANCANTE ---

    # Funzione per inviare goal
    def send_goal(self, x, y, theta):
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.orientation.z = theta  # semplice orientamento

        self.get_logger().info(f'Invio goal: x={x}, y={y}, theta={theta}')
        self._action_client.wait_for_server()
        self._send_goal_future = self._action_client.send_goal_async(goal_msg)
        self._send_goal_future.add_done_callback(self.goal_response_callback)
        
    # Callback risposta del goal
    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info('Goal rifiutato')
            return

        # Pubblica inizio movimento
        self.get_logger().info('Goal accettato')
        msg = Bool()
        msg.data = True
        self.move_status_publisher.publish(msg)

        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    # Callback risultato
    def get_result_callback(self, future):
        result = future.result().result

        if not self.at_destination:
            # Arrivato alla destinazione
            self.get_logger().info('Arrivato alla destinazione!')
            msg = Bool()
            msg.data = False
            self.move_status_publisher.publish(msg)

            self.at_destination = True
            button(self.at_destination)  # Simula interazione con il paziente
            # Torna a casa
            self.get_logger().info('Ritorno alla base...')
            self.send_goal(self.home_x, self.home_y, self.home_theta)
        else:
            # Arrivato a casa
            self.get_logger().info('Arrivato a casa!')
            msg = Bool()
            msg.data = False
            self.move_status_publisher.publish(msg)
            rclpy.shutdown()


def main():
    rclpy.init()
    publish_initial_pose()
    time.sleep(2)

    navigator = GoalNavigation()
    
    # --- CORREZIONE CHIAVE ---
    # Il main deve solo avviare lo spin e restare in attesa.
    # Non deve inviare nessun goal da solo.
    try:
        rclpy.spin(navigator)
    except KeyboardInterrupt:
        pass
    finally:
        navigator.destroy_node()
        rclpy.shutdown()
    # --- FINE CORREZIONE ---

if __name__ == '__main__':
    main()
