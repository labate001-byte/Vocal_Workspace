import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from std_msgs.msg import Bool, String
import time

# File esterni (Assicurati che esistano nella tua cartella)
from script_python.turtle_estimate_position import publish_initial_pose
from script_python.patient_button_control import button

class GoalNavigation(Node): 
    def __init__(self):
        super().__init__('goal_navigation')

        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.move_status_publisher = self.create_publisher(Bool, '/move_status', 10)

        # Subscriber vocale
        self.voice_subscriber = self.create_subscription(
            String,
            'voice_command', 
            self.voice_callback,
            10
        )

        # Coordinate Base (Home)
        self.home_x = -2.5
        self.home_y = -2.5
        self.home_theta = 0.0

        # Coordinate Letto (Paziente)
        self.bed_x = -1.0
        self.bed_y = 3.5
        self.bed_theta = 0.0

        self.get_logger().info("Navigazione pronta. Comandi: 'vieni a letto' / 'torna alla base'")

    def voice_callback(self, msg):
        command = msg.data
        self.get_logger().info(f"Ricevuto comando: {command}")

        if command == "vieni_letto":
            self.get_logger().info("🚑 Vado al LETTO del paziente...")
            self.send_goal(self.bed_x, self.bed_y, self.bed_theta)
            
        elif command == "torna_base":
            self.get_logger().info("🏠 Torno alla BASE...")
            self.send_goal(self.home_x, self.home_y, self.home_theta)

    def send_goal(self, x, y, theta):
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.orientation.z = theta 

        self.get_logger().info(f'Invio goal: x={x}, y={y}')
        
        self._action_client.wait_for_server()
        self._send_goal_future = self._action_client.send_goal_async(goal_msg)
        self._send_goal_future.add_done_callback(self.goal_response_callback)
        
    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info('Goal rifiutato :(')
            return

        self.get_logger().info('Goal accettato, in movimento...')
        msg = Bool()
        msg.data = True
        self.move_status_publisher.publish(msg)

        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        result = future.result().result
        self.get_logger().info('Destinazione raggiunta!')
        
        msg = Bool()
        msg.data = False
        self.move_status_publisher.publish(msg)

        # Eseguiamo la simulazione pulsante se siamo arrivati (opzionale)
        # Nota: Ho rimosso il ritorno automatico per permettere il controllo vocale completo.
        # Se siamo al letto, attiviamo l'interazione pulsante.
        # Possiamo dedurre dove siamo in base all'ultimo comando, ma per semplicità
        # chiamiamo button() che gestisce la logica interna o è solo una demo.
        button(True) 
        
        self.get_logger().info('In attesa del prossimo comando vocale...')

def main():
    rclpy.init()
    publish_initial_pose()
    time.sleep(2)

    navigator = GoalNavigation()
    
    try:
        rclpy.spin(navigator)
    except KeyboardInterrupt:
        pass
    finally:
        navigator.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
