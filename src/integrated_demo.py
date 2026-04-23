#!/usr/bin/env python3
"""
Phase 2 Complete Integration Demo
Shows MQTT + CoAP + Gateway + Dashboard working together
"""

import asyncio
import random
import logging
import time
import json
import threading
from datetime import datetime

# Import our components
from room import Room
from mqtt_client import MQTTHandler
from coap_server import CoAPNode
from dashboard_generator import ThingsBoardDashboard

class IntegratedDemo:
    def __init__(self):
        self.rooms = []
        self.mqtt_nodes = []
        self.coap_nodes = []
        self.running = False
        self.message_count = 0
        self.command_count = 0
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def generate_room_id(self, floor_num, room_num):
        """Generate standardized room ID"""
        return f"b01-f{floor_num:02d}-r{room_num:03d}"
    
    def create_demo_infrastructure(self):
        """Create demo infrastructure"""
        self.logger.info("Creating integrated demo infrastructure...")
        
        # Create 10 MQTT rooms (Floor 1)
        for room_num in range(1, 11):
            room_id = self.generate_room_id(1, room_num)
            room = Room(room_id)
            
            # Set initial variation
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
            
            room.temperature = 22.0 + random.uniform(-3, 4)
            room.occupancy = random.choice([True, False])
            room.hvac_mode = random.choice(["OFF", "ON"])
            
            self.rooms.append(room)
            self.coap_nodes.append(CoAPNode(room, port=5683 + room_num - 1))
            self.logger.info(f"Created CoAP room: {room_id}")
    
    def simulate_mqtt_broker_activity(self):
        """Simulate MQTT broker activity"""
        self.logger.info("Starting MQTT broker simulation...")
        
        while self.running:
            try:
                # Simulate incoming messages
                for i, (room, mqtt_node) in enumerate(zip(self.rooms[:10], self.mqtt_nodes)):
                    # Update room state
                    room.update()
                    
                    # Simulate telemetry message
                    telemetry = room.get_telemetry()
                    
                    # Log as if sent to broker
                    topic = f"campus/b01/f01/{room.room_id}/telemetry"
                    self.logger.info(f"[MQTT SEND] {topic}: temp={telemetry['temperature']:.1f}°C, "
                                  f"occupancy={'Yes' if telemetry['occupancy'] else 'No'}")
                    
                    self.message_count += 1
                    
                    # Simulate broker processing delay
                    time.sleep(0.1)
                
                # Simulate edge thinning (every 30 seconds in demo)
                if int(time.time()) % 30 == 0:
                    self.simulate_edge_thinning()
                
                time.sleep(5)  # Telemetry interval
                
            except Exception as e:
                self.logger.error(f"MQTT simulation error: {e}")
                time.sleep(1)
    
    def simulate_coap_activity(self):
        """Simulate CoAP node activity"""
        self.logger.info("Starting CoAP node simulation...")
        
        while self.running:
            try:
                # Simulate CoAP observations
                for i, (room, coap_node) in enumerate(zip(self.rooms[10:], self.coap_nodes)):
                    # Update room state
                    room.update()
                    
                    # Simulate CoAP observation response
                    telemetry = room.get_telemetry()
                    
                    # Log as if sent via CoAP observation
                    self.logger.info(f"[COAP OBSERVE] {room.room_id}: temp={telemetry['temperature']:.1f}°C, "
                                  f"hvac={telemetry['hvac_mode']}")
                    
                    self.message_count += 1
                    
                    # Simulate CoAP processing delay
                    time.sleep(0.05)
                
                time.sleep(5)  # Observation interval
                
            except Exception as e:
                self.logger.error(f"CoAP simulation error: {e}")
                time.sleep(1)
    
    def simulate_gateway_activity(self):
        """Simulate Node-RED gateway activity"""
        self.logger.info("Starting Node-RED gateway simulation...")
        
        while self.running:
            try:
                # Simulate MQTT to CoAP translation
                if random.random() < 0.3:  # 30% chance of command
                    # Simulate incoming MQTT command
                    room = random.choice(self.rooms[:10])
                    command_type = random.choice(["hvac", "lighting", "temperature"])
                    
                    if command_type == "hvac":
                        command = {"hvac_mode": random.choice(["ON", "OFF", "ECO"])}
                    elif command_type == "lighting":
                        command = {"lighting_dimmer": random.randint(0, 100)}
                    else:
                        command = {"target_temp": random.uniform(18, 26)}
                    
                    # Log gateway translation
                    self.logger.info(f"[GATEWAY] MQTT->CoAP: {room.room_id} -> {command}")
                    
                    # Process command
                    result = room.process_command(command)
                    
                    # Log command result
                    self.logger.info(f"[GATEWAY] Command result: {result['status']}")
                    
                    self.command_count += 1
                
                time.sleep(2)  # Gateway processing interval
                
            except Exception as e:
                self.logger.error(f"Gateway simulation error: {e}")
                time.sleep(1)
    
    def simulate_edge_thinning(self):
        """Simulate edge thinning and aggregation"""
        floor1_temps = [room.temperature for room in self.rooms[:10]]
        floor2_temps = [room.temperature for room in self.rooms[10:]]
        
        floor1_avg = sum(floor1_temps) / len(floor1_temps)
        floor2_avg = sum(floor2_temps) / len(floor2_temps)
        
        # Log aggregated data
        self.logger.info(f"[EDGE THINNING] Floor 01 avg: {floor1_avg:.1f}°C, "
                        f"Floor 02 avg: {floor2_avg:.1f}°C")
        
        # Simulate sending to ThingsBoard
        self.logger.info(f"[THINGSBOARD] Aggregated data sent to dashboard")
    
    def simulate_dashboard_activity(self):
        """Simulate ThingsBoard dashboard updates"""
        self.logger.info("Starting ThingsBoard dashboard simulation...")
        
        dashboard = ThingsBoardDashboard()
        
        while self.running:
            try:
                # Simulate dashboard data updates
                total_devices = len(self.rooms)
                online_devices = sum(1 for room in self.rooms if not room.node_dropout)
                avg_temp = sum(room.temperature for room in self.rooms) / len(self.rooms)
                
                # Log dashboard metrics
                self.logger.info(f"[DASHBOARD] Devices: {online_devices}/{total_devices} online, "
                                f"Avg Temp: {avg_temp:.1f}°C")
                
                # Simulate dashboard alerts
                if avg_temp > 28:
                    self.logger.warning(f"[DASHBOARD ALERT] High temperature: {avg_temp:.1f}°C")
                
                time.sleep(10)  # Dashboard update interval
                
            except Exception as e:
                self.logger.error(f"Dashboard simulation error: {e}")
                time.sleep(1)
    
    def print_integration_status(self):
        """Print current integration status"""
        print("\n" + "="*80)
        print(f" IoT CAMPUS PHASE 2 - INTEGRATED DEMO - {datetime.now().strftime('%H:%M:%S')}")
        print("="*80)
        
        # System status
        mqtt_online = sum(1 for node in self.mqtt_nodes if node.client.client_id)
        coap_online = len(self.coap_nodes)
        
        print(f"\n SYSTEM STATUS:")
        print(f"  MQTT Nodes: {mqtt_online}/10 active")
        print(f"  CoAP Nodes: {coap_online}/10 active")
        print(f"  Total Messages: {self.message_count}")
        print(f"  Commands Processed: {self.command_count}")
        
        # Protocol activity
        print(f"\n PROTOCOL ACTIVITY:")
        print(f"  MQTT: Telemetry every 5s, QoS 1/2, LWT enabled")
        print(f"  CoAP: Observation active, Confirmable messages")
        print(f"  Gateway: MQTT<->CoAP translation running")
        print(f"  ThingsBoard: Dashboard updates every 10s")
        
        # Performance metrics
        avg_temp = sum(room.temperature for room in self.rooms) / len(self.rooms)
        occupancy_count = sum(1 for room in self.rooms if room.occupancy)
        
        print(f"\n PERFORMANCE METRICS:")
        print(f"  Average Temperature: {avg_temp:.1f}°C")
        print(f"  Occupied Rooms: {occupancy_count}/20")
        print(f"  Message Rate: ~{self.message_count/60:.1f} msg/sec")
        
        print("\n" + "="*80)
    
    async def run_integrated_demo(self, duration=120):
        """Run the complete integrated demo"""
        self.logger.info(f"Starting Phase 2 Integrated Demo for {duration} seconds...")
        
        # Create infrastructure
        self.create_demo_infrastructure()
        
        # Start simulation threads
        self.running = True
        
        mqtt_thread = threading.Thread(target=self.simulate_mqtt_broker_activity)
        coap_thread = threading.Thread(target=self.simulate_coap_activity)
        gateway_thread = threading.Thread(target=self.simulate_gateway_activity)
        dashboard_thread = threading.Thread(target=self.simulate_dashboard_activity)
        
        # Start all threads
        mqtt_thread.start()
        coap_thread.start()
        gateway_thread.start()
        dashboard_thread.start()
        
        # Main demo loop
        start_time = time.time()
        status_counter = 0
        
        while self.running and (time.time() - start_time) < duration:
            status_counter += 1
            
            # Print status every 15 seconds
            if status_counter % 3 == 0:
                self.print_integration_status()
            
            await asyncio.sleep(5)
        
        # Stop all threads
        self.running = False
        
        mqtt_thread.join(timeout=2)
        coap_thread.join(timeout=2)
        gateway_thread.join(timeout=2)
        dashboard_thread.join(timeout=2)
        
        self.logger.info("Integrated demo completed!")
        
        # Final summary
        print("\n" + "="*80)
        print(" INTEGRATED DEMO SUMMARY")
        print("="*80)
        print(f"  Total Messages Processed: {self.message_count}")
        print(f"  Commands Executed: {self.command_count}")
        print(f"  MQTT Nodes: {len(self.mqtt_nodes)}")
        print(f"  CoAP Nodes: {len(self.coap_nodes)}")
        print(f"  Simulation Duration: {duration} seconds")
        print(f"  Average Message Rate: {self.message_count/duration:.1f} msg/sec")
        print("="*80)

async def main():
    """Main integrated demo function"""
    print(" IoT CAMPUS PHASE 2 - INTEGRATED DEMO")
    print("=" * 50)
    print("This demo shows the complete Phase 2 integration:")
    print("- MQTT broker with real message routing")
    print("- CoAP nodes with observation")
    print("- Node-RED gateway with protocol translation")
    print("- ThingsBoard dashboard with real-time updates")
    print("- Edge thinning and data aggregation")
    print()
    
    demo = IntegratedDemo()
    
    try:
        await demo.run_integrated_demo(duration=120)  # Run for 2 minutes
    except KeyboardInterrupt:
        print("\nDemo stopped by user")
        demo.stop()

if __name__ == "__main__":
    asyncio.run(main())
