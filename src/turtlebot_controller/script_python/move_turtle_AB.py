import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from std_msgs.msg import Bool, String
import time

# File esterni
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

        # --- DEFINIZIONE COORDINATE ---
        
        # Base (Home)
        self.home_x = -2.5
        self.home_y = -2.5
        self.home_theta = 0.0

        # Letto (Paziente)
        self.bed_x = -1.0
        self.bed_y = 3.5
        self.bed_theta = 0.0

        # Divano
        self.sofa_x = -1.5
        self.sofa_y = -3.75
        self.sofa_theta = 0.0

        # Bagno
        self.bath_x = 1.0
        self.bath_y = -0.5
        self.bath_theta = 0.0

        # Cucina
        self.kitchen_x = -0.5
        self.kitchen_y = -1.0
        self.kitchen_theta = 0.0

        self.get_logger().info("Navigazione pronta. In attesa di comandi vocali...")

    def voice_callback(self, msg):
        command = msg.data
        self.get_logger().info(f"Ricevuto comando: {command}")

        # Gestione Destinazioni
        if command == "vieni_letto":
            self.get_logger().info("🚑 Vado al LETTO del paziente...")
            self.send_goal(self.bed_x, self.bed_y, self.bed_theta)
            
        elif command == "torna_base":
            self.get_logger().info("🏠 Torno alla BASE...")
            self.send_goal(self.home_x, self.home_y, self.home_theta)
            
        elif command == "vai_divano":
            self.get_logger().info("🛋️ Vado al DIVANO...")
            self.send_goal(self.sofa_x, self.sofa_y, self.sofa_theta)
            
        elif command == "vai_bagno":
            self.get_logger().info("🚽 Vado in BAGNO...")
            self.send_goal(self.bath_x, self.bath_y, self.bath_theta)
            
        elif command == "vai_cucina":
            self.get_logger().info("🍳 Vado in CUCINA...")
            self.send_goal(self.kitchen_x, self.kitchen_y, self.kitchen_theta)

    def send_goal(self, x, y, theta):
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = float(x)
        goal_msg.pose.pose.position.y = float(y)
        goal_msg.pose.pose.orientation.z = float(theta)
        goal_msg.pose.pose.orientation.w = 1.0 # Orientamento valido di default

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
        # Result unused but kept for structure
        _ = future.result().result
        self.get_logger().info('Destinazione raggiunta!')
        
        msg = Bool()
        msg.data = False
        self.move_status_publisher.publish(msg)

        # Attivazione logica pulsante/interazione (opzionale)
        button(False) 
        
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
