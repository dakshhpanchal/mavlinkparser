from pymavlink import mavutil
import time

udp_ip = "127.0.0.1"
udpin = "0.0.0.0"
udp_port = 14550

master = mavutil.mavlink_connection(f"udp:{udp_ip}:{udp_port}")
master.wait_heartbeat()
print("Connected to Pixhawk")

def set_mode(mode):
    mode_id = master.mode_mapping()[mode]
    master.mav.set_mode_send(
        master.target_system,
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
        mode_id
    )

while True:
    set_mode("STABILIZE")
    print("Flight mode changed to STABILIZE")
    time.sleep(5)

    set_mode("GUIDED")
    print("Flight mode changed to GUIDED")
    time.sleep(5)