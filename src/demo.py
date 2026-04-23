#!/usr/bin/env python3
"""
Phase 2 IoT Campus Demo - Standalone Simulation
Demonstrates the complete Phase 2 implementation without external dependencies
"""

import asyncio
import random
import logging
import time
import json
from datetime import datetime

# Import our enhanced components
from room import Room
from mqtt_client import MQTTHandler
from coap_server import CoAPNode

class DemoSimulation:
    def __init__(self):
        self.rooms = []
        self.mqtt_nodes = []
        self.coap_nodes = []
        self.running = False
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def generate_room_id(self, floor_num, room_num):
        """Generate standardized room ID"""
        return f"b01-f{floor_num:02d}-r{room_num:03d}"
    
    def create_demo_rooms(self):
        """Create a subset of rooms for demo (20 total: 10 MQTT + 10 CoAP)"""
        self.logger.info("Creating demo rooms...")
        
        # Create 10 MQTT rooms (Floor 1)
        for room_num in range(1, 11):
            room_id = self.generate_room_id(1, room_num)
            room = Room(room_id)
            
            # Set some initial variation
            room.temperature = 20.0 + random.uniform(-2, 5)
            room.occupancy = random.choice([True, False])
            room.hvac_mode = random.choice(["OFF", "ON", "ECO"])
            
            self.rooms.append(room)
            self.mqtt_nodes.append(MQTTHandler(f"mqtt-{room_id}", room))
            self.logger.info(f"Created MQTT room: {room_id}")
        
        # Create 10 CoAP rooms (Floor 2)
        for room_num in range(1, 11):
            room_id = self.generate_room_id(2, room_num)
            room = Room(room_id)
            
            # Set some initial variation
            room.temperature = 22.0 + random.uniform(-3, 4)
            room.occupancy = random.choice([True, False])
            room.hvac_mode = random.choice(["OFF", "ON"])
            
            self.rooms.append(room)
            self.coap_nodes.append(CoAPNode(room, port=5683 + room_num - 1))
            self.logger.info(f"Created CoAP room: {room_id}")
    
    def simulate_mqtt_telemetry(self):
        """Simulate MQTT telemetry data"""
        telemetry_data = []
        
        for i, (room, mqtt_node) in enumerate(zip(self.rooms[:10], self.mqtt_nodes)):
            # Update room state
            room.update()
            
            # Get telemetry
            telemetry = room.get_telemetry()
            telemetry_data.append({
                "protocol": "MQTT",
                "room_id": room.room_id,
                "temperature": telemetry["temperature"],
                "humidity": telemetry["humidity"],
                "occupancy": telemetry["occupancy"],
                "hvac_mode": telemetry["hvac_mode"],
                "timestamp": telemetry["timestamp"]
            })
        
        return telemetry_data
    
    def simulate_coap_telemetry(self):
        """Simulate CoAP telemetry data"""
        telemetry_data = []
        
        for i, (room, coap_node) in enumerate(zip(self.rooms[10:], self.coap_nodes)):
            # Update room state
            room.update()
            
            # Get telemetry
            telemetry = room.get_telemetry()
            telemetry_data.append({
                "protocol": "CoAP",
                "room_id": room.room_id,
                "temperature": telemetry["temperature"],
                "humidity": telemetry["humidity"],
                "occupancy": telemetry["occupancy"],
                "hvac_mode": telemetry["hvac_mode"],
                "timestamp": telemetry["timestamp"]
            })
        
        return telemetry_data
    
    def simulate_commands(self):
        """Simulate random commands to rooms"""
        commands = []
        
        # Generate random commands
        for _ in range(random.randint(1, 3)):
            room = random.choice(self.rooms)
            command_type = random.choice(["hvac", "lighting", "temperature"])
            
            if command_type == "hvac":
                command = {"hvac_mode": random.choice(["ON", "OFF", "ECO"])}
            elif command_type == "lighting":
                command = {"lighting_dimmer": random.randint(0, 100)}
            else:
                command = {"target_temp": random.uniform(18, 26)}
            
            # Process command
            result = room.process_command(command)
            
            commands.append({
                "room_id": room.room_id,
                "command": command,
                "result": result,
                "timestamp": int(time.time())
            })
        
        return commands
    
    def calculate_floor_averages(self):
        """Calculate average values per floor"""
        floor1_temps = [room.temperature for room in self.rooms[:10]]
        floor2_temps = [room.temperature for room in self.rooms[10:]]
        
        floor1_occupancy = sum(1 for room in self.rooms[:10] if room.occupancy)
        floor2_occupancy = sum(1 for room in self.rooms[10:] if room.occupancy)
        
        return {
            "floor_01": {
                "avg_temperature": sum(floor1_temps) / len(floor1_temps),
                "occupancy_count": floor1_occupancy,
                "total_rooms": 10
            },
            "floor_02": {
                "avg_temperature": sum(floor2_temps) / len(floor2_temps),
                "occupancy_count": floor2_occupancy,
                "total_rooms": 10
            }
        }
    
    def print_dashboard(self, mqtt_data, coap_data, commands, floor_stats):
        """Print a formatted dashboard"""
        print("\n" + "="*80)
        print(f" IoT CAMPUS PHASE 2 DASHBOARD - {datetime.now().strftime('%H:%M:%S')}")
        print("="*80)
        
        # System Overview
        print(f"\n SYSTEM OVERVIEW:")
        print(f"  Total Rooms: {len(self.rooms)} (10 MQTT + 10 CoAP)")
        print(f"  Active MQTT Nodes: {len(self.mqtt_nodes)}")
        print(f"  Active CoAP Nodes: {len(self.coap_nodes)}")
        
        # Floor Statistics
        print(f"\n FLOOR STATISTICS:")
        print(f"  Floor 01: Avg Temp: {floor_stats['floor_01']['avg_temperature']:.1f}°C | "
              f"Occupancy: {floor_stats['floor_01']['occupancy_count']}/10")
        print(f"  Floor 02: Avg Temp: {floor_stats['floor_02']['avg_temperature']:.1f}°C | "
              f"Occupancy: {floor_stats['floor_02']['occupancy_count']}/10")
        
        # Recent Commands
        if commands:
            print(f"\n RECENT COMMANDS:")
            for cmd in commands:
                print(f"  {cmd['room_id']}: {cmd['command']} -> {cmd['result']['status']}")
        
        # Sample Telemetry
        print(f"\n SAMPLE TELEMETRY:")
        print("  MQTT Rooms:")
        for i, data in enumerate(mqtt_data[:3]):
            print(f"    {data['room_id']}: {data['temperature']:.1f}°C, "
                  f"{'Occupied' if data['occupancy'] else 'Vacant'}, HVAC: {data['hvac_mode']}")
        
        print("  CoAP Rooms:")
        for i, data in enumerate(coap_data[:3]):
            print(f"    {data['room_id']}: {data['temperature']:.1f}°C, "
                  f"{'Occupied' if data['occupancy'] else 'Vacant'}, HVAC: {data['hvac_mode']}")
        
        print("\n" + "="*80)
    
    async def run_demo(self, duration=60):
        """Run the demo simulation"""
        self.logger.info(f"Starting Phase 2 Demo for {duration} seconds...")
        self.create_demo_rooms()
        
        self.running = True
        start_time = time.time()
        cycle_count = 0
        
        while self.running and (time.time() - start_time) < duration:
            cycle_count += 1
            
            # Simulate telemetry
            mqtt_data = self.simulate_mqtt_telemetry()
            coap_data = self.simulate_coap_telemetry()
            
            # Simulate commands (every 3 cycles)
            if cycle_count % 3 == 0:
                commands = self.simulate_commands()
            else:
                commands = []
            
            # Calculate statistics
            floor_stats = self.calculate_floor_averages()
            
            # Print dashboard
            self.print_dashboard(mqtt_data, coap_data, commands, floor_stats)
            
            # Wait for next cycle
            await asyncio.sleep(5)
        
        self.logger.info("Demo completed!")
    
    def stop(self):
        """Stop the demo"""
        self.running = False

async def main():
    """Main demo function"""
    print(" IoT CAMPUS PHASE 2 - DEMONSTRATION")
    print("=====================================")
    print("This demo shows the complete Phase 2 implementation:")
    print("- 10 MQTT nodes with telemetry and command processing")
    print("- 10 CoAP nodes with observation support")
    print("- Real-time physics simulation")
    print("- Virtual actuators and command processing")
    print("- Floor-based statistics and edge thinning")
    print()
    
    demo = DemoSimulation()
    
    try:
        await demo.run_demo(duration=120)  # Run for 2 minutes
    except KeyboardInterrupt:
        print("\nDemo stopped by user")
        demo.stop()

if __name__ == "__main__":
    asyncio.run(main())
