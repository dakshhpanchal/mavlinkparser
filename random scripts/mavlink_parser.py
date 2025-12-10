#!/usr/bin/env python3
"""
MAVLink Custom Message Sender via Telemetry RF
Base Station → Telemetry Radio → Pixhawk
"""

import struct
import xml.etree.ElementTree as ET
import random
import time
import serial
import binascii
import argparse
from pathlib import Path

class MAVLinkSender:
    def __init__(self, system_id=100, component_id=190):
        self.system_id = system_id
        self.component_id = component_id
        self.sequence = 0
        
    def load_xml(self, xml_file):
        """Load message definitions from XML file"""
        if not Path(xml_file).exists():
            print(f"Error: XML file '{xml_file}' not found!")
            return {}
        
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        messages = {}
        print(f"Loading messages from: {xml_file}")
        
        for msg_elem in root.findall('message'):
            msg_id = int(msg_elem.get('id'))
            msg_name = msg_elem.get('name')
            
            fields = []
            for field_elem in msg_elem.findall('field'):
                field_name = field_elem.get('name')
                field_type = field_elem.get('type')
                fields.append((field_name, field_type))
            
            messages[msg_id] = {
                'name': msg_name,
                'fields': fields
            }
            print(f"  ID {msg_id}: {msg_name} ({len(fields)} fields)")
        
        return messages
    
    def generate_data(self, fields):
        """Generate random test data"""
        data = {}
        for field_name, field_type in fields:
            if 'timestamp' in field_name.lower() or 'time' in field_name.lower():
                if 'uint64' in field_type:
                    data[field_name] = int(time.time() * 1000)
                elif 'uint32' in field_type:
                    data[field_name] = int(time.time())
            
            elif 'temperature' in field_name.lower():
                if 'float' in field_type:
                    data[field_name] = round(random.uniform(20, 30), 2)
                else:
                    data[field_name] = random.randint(200, 300)
            
            elif 'pressure' in field_name.lower():
                if 'float' in field_type:
                    data[field_name] = round(random.uniform(1000, 1020), 2)
                else:
                    data[field_name] = random.randint(100000, 102000)
            
            elif 'humidity' in field_name.lower():
                if 'float' in field_type:
                    data[field_name] = round(random.uniform(40, 60), 2)
                else:
                    data[field_name] = random.randint(40, 60)
            
            else:
                # Default values
                if 'uint8' in field_type:
                    data[field_name] = random.randint(0, 255)
                elif 'int8' in field_type:
                    data[field_name] = random.randint(-128, 127)
                elif 'uint16' in field_type:
                    data[field_name] = random.randint(0, 65535)
                elif 'int16' in field_type:
                    data[field_name] = random.randint(-32768, 32767)
                elif 'uint32' in field_type:
                    data[field_name] = random.randint(0, 1000000)
                elif 'int32' in field_type:
                    data[field_name] = random.randint(-1000000, 1000000)
                elif 'uint64' in field_type:
                    data[field_name] = int(time.time() * 1000)
                elif 'int64' in field_type:
                    data[field_name] = int(time.time() * 1000)
                elif 'float' in field_type:
                    data[field_name] = round(random.uniform(0, 100), 4)
                elif 'double' in field_type:
                    data[field_name] = round(random.uniform(0, 100), 8)
                elif 'char' in field_type:
                    data[field_name] = 'A'
        
        return data
    
    def calculate_crc(self, data, crc_extra=0):
        """Calculate MAVLink CRC-16/MCRF4XX with proper crc_extra"""
        crc = 0xFFFF
        
        # Process crc_extra FIRST (important!)
        crc ^= (crc_extra << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc = crc << 1
            crc &= 0xFFFF
        
        # Process data bytes
        for byte in data:
            crc ^= (byte << 8)
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc = crc << 1
                crc &= 0xFFFF
        
        return crc
    
    def create_mavlink_packet(self, message_id, msg_info, data):
        """Create a proper MAVLink 2 packet with correct CRC"""
        fields = msg_info['fields']
        
        # Pack payload
        payload_bytes = b''
        format_str = '<'
        values = []
        
        for field_name, field_type in fields:
            value = data.get(field_name, 0)
            
            # Map MAVLink types to struct format characters
            if 'uint8' in field_type:
                format_str += 'B'
                values.append(value)
            elif 'int8' in field_type:
                format_str += 'b'
                values.append(value)
            elif 'uint16' in field_type:
                format_str += 'H'
                values.append(value)
            elif 'int16' in field_type:
                format_str += 'h'
                values.append(value)
            elif 'uint32' in field_type:
                format_str += 'I'
                values.append(value)
            elif 'int32' in field_type:
                format_str += 'i'
                values.append(value)
            elif 'uint64' in field_type:
                format_str += 'Q'
                values.append(value)
            elif 'int64' in field_type:
                format_str += 'q'
                values.append(value)
            elif 'float' in field_type:
                format_str += 'f'
                values.append(value)
            elif 'double' in field_type:
                format_str += 'd'
                values.append(value)
            elif 'char' in field_type:
                format_str += 'c'
                values.append(bytes(str(value)[0], 'ascii'))
        
        if values:
            try:
                payload_bytes = struct.pack(format_str, *values)
            except struct.error as e:
                print(f"Error packing data: {e}")
                return None
        
        # MAVLink 2 header (10 bytes)
        payload_len = len(payload_bytes)
        incompat_flags = 0x00
        compat_flags = 0x00
        seq = self.sequence
        self.sequence = (self.sequence + 1) & 0xFF
        
        # Build header (10 bytes total)
        header = struct.pack('<BBBBBBB',
                           payload_len,
                           incompat_flags,
                           compat_flags,
                           seq,
                           self.system_id,
                           self.component_id,
                           message_id & 0xFF)  # LSB of message ID
        
        header += struct.pack('<H', (message_id >> 8) & 0xFFFF)  # Middle and MSB
        header += b'\x00'  # Padding byte
        
        # Calculate PROPER MAVLink CRC
        # For custom messages (ID >= 50000), we need a crc_extra
        # Use a simple derivation for custom messages
        if message_id < 50000:
            # Standard messages have predefined crc_extras
            crc_extra = self.get_standard_crc_extra(message_id)
        else:
            # For custom messages, derive from message ID
            crc_extra = (message_id & 0xFF) ^ ((message_id >> 8) & 0xFF)
        
        crc_data = header[1:] + payload_bytes  # Everything except STX
        crc = self.calculate_crc(crc_data, crc_extra)
        
        # Build complete packet
        packet = b'\xFD' + header + payload_bytes + struct.pack('<H', crc)
        
        return packet
    
    def get_standard_crc_extra(self, message_id):
        """Get CRC extra for standard MAVLink messages"""
        # Common MAVLink message CRC extras
        crc_extras = {
            0: 50,    # HEARTBEAT
            1: 124,   # SYS_STATUS
            30: 39,   # ATTITUDE
            33: 104,  # GLOBAL_POSITION_INT
            74: 142,  # VFR_HUD
            253: 83,  # STATUSTEXT
            251: 170, # NAMED_VALUE_FLOAT
        }
        return crc_extras.get(message_id, 0)
    
    def send_packet(self, serial_port, packet, verbose=False):
        """Send packet via serial port"""
        try:
            serial_port.write(packet)
            if verbose:
                hex_str = binascii.hexlify(packet).decode('ascii')
                print(f"Sent: {hex_str}")
            return True
        except Exception as e:
            print(f"Error sending packet: {e}")
            return False
    
    def run(self, xml_file, serial_port, message_id=None, rate_hz=1, duration=60):
        """Main function: send MAVLink packets via telemetry"""
        
        # Load messages from XML
        messages = self.load_xml(xml_file)
        if not messages:
            print("No messages loaded. Exiting.")
            return
        
        # If no specific message ID, use first one
        if message_id is None:
            message_id = list(messages.keys())[0]
        
        if message_id not in messages:
            print(f"Error: Message ID {message_id} not found in XML!")
            return
        
        msg_info = messages[message_id]
        
        print("\n" + "="*60)
        print("MAVLink Custom Message Sender")
        print("="*60)
        print(f"Message: {msg_info['name']} (ID: {message_id})")
        print(f"Serial Port: {serial_port.port}")
        print(f"Baud Rate: {serial_port.baudrate}")
        print(f"Sending at: {rate_hz} Hz for {duration} seconds")
        print("="*60 + "\n")
        
        packet_count = 0
        start_time = time.time()
        interval = 1.0 / rate_hz
        
        try:
            while time.time() - start_time < duration:
                # Generate test data
                data = self.generate_data(msg_info['fields'])
                
                # Create MAVLink packet
                packet = self.create_mavlink_packet(message_id, msg_info, data)
                
                if packet:
                    # Send packet
                    if self.send_packet(serial_port, packet, verbose=False):
                        packet_count += 1
                        
                        # Display progress every 10 packets
                        if packet_count % 10 == 0:
                            elapsed = time.time() - start_time
                            print(f"[{elapsed:.1f}s] Sent {packet_count} packets")
                            print(f"  Last data: {data}")
                
                # Wait for next interval
                next_time = start_time + (packet_count * interval)
                sleep_time = next_time - time.time()
                if sleep_time > 0:
                    time.sleep(sleep_time)
        
        except KeyboardInterrupt:
            print("\nStopped by user")
        
        finally:
            elapsed = time.time() - start_time
            print(f"\n" + "="*60)
            print(f"Summary:")
            print(f"  Total packets sent: {packet_count}")
            print(f"  Total time: {elapsed:.1f} seconds")
            print(f"  Average rate: {packet_count/elapsed:.1f} Hz")
            print("="*60)

def main():
    parser = argparse.ArgumentParser(
        description='Send MAVLink custom messages via Telemetry RF to Pixhawk',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  %(prog)s custom_messages.xml --port COM3 --baud 57600
  %(prog)s custom_messages.xml --id 50000 --rate 5 --duration 30
  %(prog)s custom_messages.xml --port /dev/ttyUSB0 --baud 115200 --system 200
        
Common telemetry radio baud rates: 57600, 115200, 921600
        """
    )
    
    parser.add_argument('xml_file', help='XML file with message definitions')
    parser.add_argument('--port', default='/dev/ttyUSB0', 
                       help='Serial port (default: /dev/ttyUSB0)')
    parser.add_argument('--baud', type=int, default=57600,
                       help='Baud rate (default: 57600)')
    parser.add_argument('--id', type=int, 
                       help='Message ID to send (default: first in XML)')
    parser.add_argument('--rate', type=float, default=1.0,
                       help='Send rate in Hz (default: 1)')
    parser.add_argument('--duration', type=int, default=60,
                       help='Duration in seconds (default: 60)')
    parser.add_argument('--system', type=int, default=100,
                       help='System ID (default: 100)')
    parser.add_argument('--component', type=int, default=190,
                       help='Component ID (default: 190)')
    
    args = parser.parse_args()
    
    # Check if XML exists
    if not Path(args.xml_file).exists():
        print(f"Error: XML file '{args.xml_file}' not found!")
        return
    
    # Open serial port
    try:
        ser = serial.Serial(
            port=args.port,
            baudrate=args.baud,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1
        )
        print(f"Connected to {args.port} at {args.baud} baud")
    except Exception as e:
        print(f"Failed to open serial port {args.port}: {e}")
        print("\nCommon issues:")
        print("1. Check if telemetry radio is connected")
        print("2. Check COM port name (Windows: COM3, Linux: /dev/ttyUSB0)")
        print("3. Check if another program is using the port (Mission Planner, QGC)")
        print("4. Check baud rate matches telemetry radio settings")
        return
    
    # Create sender and run
    sender = MAVLinkSender(args.system, args.component)
    
    try:
        sender.run(args.xml_file, ser, args.id, args.rate, args.duration)
    finally:
        ser.close()
        print(f"Closed serial port {args.port}")

if __name__ == "__main__":
    # First install required package if needed
    print("Note: This script requires pyserial")
    print("Install with: pip install pyserial")
    print("-" * 50)
    
    main()