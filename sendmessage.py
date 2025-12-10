from pymavlink import mavutil
import custom_dialect.mavlink as mav
import time

master = mavutil.mavlink_connection("udp:127.0.0.1:14550")
master.wait_heartbeat()

while True:
    sensor = mav.MAVLink_sensor_data_message(
        timestamp=int(time.time()*1e6),
        temperature=25.2,
        pressure=1012.5,
        humidity=53.2,
        sensor_id=1,
        battery_voltage=11.7
    )

    gps = mav.MAVLink_gps_data_message(
        time=int(time.time()*1e6),
        latitude=int(28.6139 * 1e7),
        longitude=int(77.2090 * 1e7),
        altitude=int(230000),
        satellites=9,
        fix_type=3
    )

    master.mav.send(sensor)
    master.mav.send(gps)

    print("Sent custom messages")
    time.sleep(1)