# room.py
import random
import time
import logging

class Room:
    def __init__(self, room_id):
        self.room_id = room_id
        # Sensors
        self.temperature = 22.0
        self.humidity = 50.0
        self.occupancy = False
        self.light_level = 400
        
        # Actuators
        self.hvac_mode = "OFF"  # ON, OFF, ECO
        self.lighting_dimmer = 50
        self.target_temp = 22.0
        
        # Fault modeling
        self.sensor_drift = 0.0
        self.frozen_sensor = False
        self.telemetry_delay = 0
        self.node_dropout = False
        
        # Physics constants
        self.thermal_leakage_alpha = 0.01
        self.hvac_strength_beta = 0.2
        self.outside_temp = 30.0
        
        # Timing
        self.last_update = int(time.time())
        self.tick_count = 0

    def update(self):
        """Update room state with physics-based simulation"""
        if self.node_dropout:
            return
            
        self.tick_count += 1
        current_time = int(time.time())
        
        # Apply thermal physics (Newton's Law of Cooling)
        leakage = self.thermal_leakage_alpha * (self.outside_temp - self.temperature)
        
        # HVAC impact based on mode
        hvac_power = 0
        if self.hvac_mode == "ON":
            hvac_power = 1.0
        elif self.hvac_mode == "ECO":
            hvac_power = 0.5
            
        hvac_change = self.hvac_strength_beta * hvac_power
        
        # Temperature update
        self.temperature += leakage + hvac_change
        
        # Occupancy effects
        if self.occupancy:
            self.temperature += 0.01  # Body heat
            self.light_level = max(300, self.light_level)  # Minimum light when occupied
        else:
            # Natural light variation
            self.light_level += random.uniform(-50, 50)
            
        # Humidity variation
        self.humidity += random.uniform(-1, 1)
        
        # Apply faults
        self._apply_faults()
        
        # Validate ranges
        self.temperature = max(15.0, min(50.0, self.temperature))
        self.humidity = max(0.0, min(100.0, self.humidity))
        self.light_level = max(0, min(1000, self.light_level))
        
        self.last_update = current_time

    def _apply_faults(self):
        """Apply fault modeling effects"""
        # Sensor drift
        if random.random() < 0.001:  # 0.1% chance per tick
            self.sensor_drift += random.uniform(-0.5, 0.5)
            
        # Frozen sensor
        if random.random() < 0.0005:  # 0.05% chance per tick
            self.frozen_sensor = not self.frozen_sensor
            
        # Node dropout
        if random.random() < 0.0001:  # 0.01% chance per tick
            self.node_dropout = not self.node_dropout

    def get_telemetry(self):
        """Get current telemetry with fault effects applied"""
        if self.frozen_sensor:
            # Return last known values
            return {
                "sensor_id": self.room_id,
                "timestamp": self.last_update,
                "temperature": self.temperature + self.sensor_drift,
                "humidity": self.humidity + self.sensor_drift,
                "occupancy": self.occupancy,
                "light_level": self.light_level,
                "hvac_mode": self.hvac_mode,
                "lighting_dimmer": self.lighting_dimmer,
                "fault_status": {
                    "drift": self.sensor_drift,
                    "frozen": self.frozen_sensor,
                    "dropout": self.node_dropout
                }
            }
        
        return {
            "sensor_id": self.room_id,
            "timestamp": int(time.time()),
            "temperature": self.temperature + self.sensor_drift,
            "humidity": self.humidity + self.sensor_drift,
            "occupancy": self.occupancy,
            "light_level": self.light_level,
            "hvac_mode": self.hvac_mode,
            "lighting_dimmer": self.lighting_dimmer,
            "fault_status": {
                "drift": self.sensor_drift,
                "frozen": self.frozen_sensor,
                "dropout": self.node_dropout
            }
        }

    def process_command(self, command):
        """Process incoming actuator commands - Enhanced for Phase 2"""
        try:
            response = {"status": "success", "room_id": self.room_id, "timestamp": int(time.time())}
            
            # HVAC Control
            if "hvac_mode" in command:
                old_mode = self.hvac_mode
                self.hvac_mode = command["hvac_mode"]
                response["hvac_mode"] = self.hvac_mode
                logging.info(f"{self.room_id}: HVAC changed from {old_mode} to {self.hvac_mode}")
                
            # Lighting Control
            if "lighting_dimmer" in command:
                old_dimmer = self.lighting_dimmer
                self.lighting_dimmer = max(0, min(100, command["lighting_dimmer"]))
                response["lighting_dimmer"] = self.lighting_dimmer
                logging.info(f"{self.room_id}: Lighting changed from {old_dimmer}% to {self.lighting_dimmer}%")
                
            # Target Temperature Control
            if "target_temp" in command:
                old_target = self.target_temp
                self.target_temp = max(15, min(50, command["target_temp"]))
                response["target_temp"] = self.target_temp
                logging.info(f"{self.room_id}: Target temp changed from {old_target}°C to {self.target_temp}°C")
                
            # Occupancy Control (for testing)
            if "occupancy" in command:
                old_occupancy = self.occupancy
                self.occupancy = bool(command["occupancy"])
                response["occupancy"] = self.occupancy
                logging.info(f"{self.room_id}: Occupancy changed from {old_occupancy} to {self.occupancy}")
                
            # Multi-actuator command support
            if "hvac" in command:
                hvac_cmd = command["hvac"].upper()
                if hvac_cmd == "ON":
                    self.hvac_mode = "ON"
                elif hvac_cmd == "OFF":
                    self.hvac_mode = "OFF"
                elif hvac_cmd == "ECO":
                    self.hvac_mode = "ECO"
                response["hvac_mode"] = self.hvac_mode
                
            return response
            
        except Exception as e:
            logging.error(f"Error processing command for {self.room_id}: {e}")
            return {"status": "error", "room_id": self.room_id, "message": str(e), "timestamp": int(time.time())}
    
    def get_actuator_status(self):
        """Get current actuator states - Virtual Actuator Interface"""
        return {
            "room_id": self.room_id,
            "timestamp": int(time.time()),
            "actuators": {
                "hvac": {
                    "mode": self.hvac_mode,
                    "target_temp": self.target_temp,
                    "status": "active" if self.hvac_mode != "OFF" else "inactive"
                },
                "lighting": {
                    "dimmer_level": self.lighting_dimmer,
                    "status": "on" if self.lighting_dimmer > 0 else "off"
                },
                "occupancy": {
                    "detected": self.occupancy,
                    "last_update": self.last_update
                }
            }
        }