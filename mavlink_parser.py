#!/usr/bin/env python3

import struct
import xml.etree.ElementTree as ET
import random
import time
import binascii
from pathlib import Path

class SimpleMAVLinkGenerator:
    def __init__(self, system_id=100, component_id=190):
        self.system_id = system_id
        self.component_id = component_id
        self.sequence = 0
        
    def load_xml(self, xml_file):
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
    
    '''this function will be replaced with actual data received by the sensors'''
    def generate_data(self, fields):
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
            
            elif 'latitude' in field_name.lower():
                if 'int32' in field_type:
                    data[field_name] = 376500000 + random.randint(-10000, 10000)
            
            elif 'longitude' in field_name.lower():
                if 'int32' in field_type:
                    data[field_name] = -1224300000 + random.randint(-10000, 10000)
            
            elif 'altitude' in field_name.lower():
                if 'int32' in field_type:
                    data[field_name] = random.randint(0, 50000)
            
            elif 'quality' in field_name.lower() or 'percent' in field_name.lower():
                if 'uint8' in field_type:
                    data[field_name] = random.randint(0, 100)
                elif 'float' in field_type:
                    data[field_name] = round(random.uniform(0, 100), 2)
            
            elif 'status' in field_name.lower() or 'flag' in field_name.lower():
                if 'uint8' in field_type:
                    data[field_name] = random.randint(0, 3)
            
            elif 'id' in field_name.lower():
                if 'uint8' in field_type or 'uint16' in field_type:
                    data[field_name] = random.randint(1, 255)
            
            elif 'count' in field_name.lower():
                if 'uint8' in field_type:
                    data[field_name] = random.randint(1, 20)
                elif 'uint16' in field_type:
                    data[field_name] = random.randint(1, 100)
            
            elif 'voltage' in field_name.lower():
                if 'float' in field_type:
                    data[field_name] = round(random.uniform(4.8, 5.2), 2)
            
            elif 'current' in field_name.lower():
                if 'float' in field_type:
                    data[field_name] = round(random.uniform(0.5, 2.0), 2)
            
            else:
                #default values
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
    
    def create_mavlink_packet(self, message_id, msg_info, data):
        """Create a MAVLink 2 packet from data"""
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
        
        # Simple CRC calculation (for demonstration)
        # In real use, you'd use proper MAVLink CRC
        crc = 0xFFFF
        for byte in header[1:] + payload_bytes:
            crc ^= byte << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc = crc << 1
                crc &= 0xFFFF
        
        # Build complete packet
        packet = b'\xFD' + header + payload_bytes + struct.pack('<H', crc)
        
        return packet
    
    def generate_from_xml(self, xml_file, message_id=None, count=1):
        """Main function: generate MAVLink from XML"""
        
        # Load messages from XML
        messages = self.load_xml(xml_file)
        if not messages:
            return
        
        # If no specific message ID, use first one
        if message_id is None:
            message_id = list(messages.keys())[0]
        
        if message_id not in messages:
            print(f"Error: Message ID {message_id} not found in XML!")
            return
        
        msg_info = messages[message_id]
        print(f"\nGenerating {count} packet(s) for: {msg_info['name']} (ID: {message_id})")
        print("-" * 60)
        
        for i in range(count):
            print(f"\nPacket {i+1}:")
            
            # Generate test data
            data = self.generate_data(msg_info['fields'])
            
            # Display data
            print("  Field values:")
            for field_name, field_type in msg_info['fields']:
                value = data.get(field_name, "N/A")
                print(f"    {field_name:20s} = {value:15} ({field_type})")
            
            # Create MAVLink packet
            packet = self.create_mavlink_packet(message_id, msg_info, data)
            
            if packet:
                # Convert to hex
                hex_str = binascii.hexlify(packet).decode('ascii')
                
                print(f"\n  MAVLink 2 packet ({len(packet)} bytes):")
                bytes_list = [hex_str[i:i+2] for i in range(0, len(hex_str), 2)]
                
                print(f"    STX:     {bytes_list[0]}")
                
                # Header (10 bytes)
                if len(bytes_list) > 10:
                    header_bytes = bytes_list[1:11]
                    print(f"    Header:  {' '.join(header_bytes[:8])}")
                    if len(header_bytes) > 8:
                        print(f"            {' '.join(header_bytes[8:])}")
                
                # Payload
                payload_len = packet[1]  # Second byte is payload length
                if len(bytes_list) > 11:
                    payload_start = 11
                    payload_end = payload_start + payload_len
                    payload_bytes = bytes_list[payload_start:payload_end]
                    
                    if payload_bytes:
                        print(f"    Payload: {' '.join(payload_bytes[:min(8, len(payload_bytes))])}")
                        if len(payload_bytes) > 8:
                            for i in range(8, len(payload_bytes), 8):
                                chunk = payload_bytes[i:i+8]
                                print(f"            {' '.join(chunk)}")
                
                # CRC
                if len(bytes_list) >= 2:
                    crc_bytes = bytes_list[-2:]
                    print(f"    CRC:     {' '.join(crc_bytes)}")
                
                print(f"\n  Raw hex: {hex_str}")
                
                print(f"\n  C array: {{0x{', 0x'.join(bytes_list)}}}")
            
            print("-" * 40)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate MAVLink 2 packets from XML')
    parser.add_argument('xml_file', help='XML file with message definitions')
    parser.add_argument('--id', type=int, help='Message ID to generate (default: first in XML)')
    parser.add_argument('--count', type=int, default=1, help='Number of packets to generate')
    parser.add_argument('--system', type=int, default=100, help='System ID (default: 100)')
    parser.add_argument('--component', type=int, default=190, help='Component ID (default: 190)')
    
    args = parser.parse_args()
    
    generator = SimpleMAVLinkGenerator(args.system, args.component)
    generator.generate_from_xml(args.xml_file, args.id, args.count)

if __name__ == "__main__":
    main()