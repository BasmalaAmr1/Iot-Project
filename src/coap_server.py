# coap_server.py
import asyncio
import json
import logging
from aiocoap import Message, Context, resource
from aiocoap.numbers import ContentFormat
import time
import random

class TelemetryResource(resource.Resource):
    """CoAP resource for telemetry data - Enhanced for Phase 2"""
    def __init__(self, room):
        super().__init__()
        self.room = room
        self.observers = set()
        self.last_telemetry = None

    async def render_get(self, request):
        """Handle GET requests for telemetry with confirmable response"""
        self.room.update()
        telemetry = self.room.get_telemetry()
        self.last_telemetry = telemetry
        payload = json.dumps(telemetry).encode('utf-8')
        
        # Return confirmable message if request was confirmable
        if request.is_confirmable:
            return Message(
                payload=payload,
                content_format=ContentFormat.APPLICATION_JSON,
                code=2.05  # Content
            )
        else:
            return Message(
                payload=payload,
                content_format=ContentFormat.APPLICATION_JSON,
                code=2.05  # Content
            )

    def add_observation(self, request, serverobservation):
        """Add observer for telemetry updates - Enhanced for Phase 2"""
        self.observers.add(serverobservation)
        serverobservation.accept()
        logging.info(f"Added observer for {self.room.room_id} telemetry")
        
        # Schedule periodic updates
        asyncio.create_task(self.periodic_update(serverobservation))

    async def periodic_update(self, observation):
        """Send periodic telemetry updates to observers"""
        while True:
            try:
                await asyncio.sleep(5)  # Update interval
                
                self.room.update()
                telemetry = self.room.get_telemetry()
                
                # Only send if values changed significantly
                if self._significant_change(telemetry):
                    payload = json.dumps(telemetry).encode('utf-8')
                    
                    observation.trigger(Message(
                        payload=payload,
                        content_format=ContentFormat.APPLICATION_JSON,
                        code=2.05  # Content
                    ))
                    
                    self.last_telemetry = telemetry
                    logging.debug(f"Sent update for {self.room.room_id}: temp={telemetry['temperature']:.1f}°C")
                
            except Exception as e:
                logging.error(f"Error in periodic update for {self.room.room_id}: {e}")
                break
    
    def _significant_change(self, current_telemetry):
        """Check if telemetry changed significantly"""
        if self.last_telemetry is None:
            return True
            
        # Check temperature change > 0.5°C
        temp_diff = abs(current_telemetry['temperature'] - self.last_telemetry['temperature'])
        if temp_diff > 0.5:
            return True
            
        # Check occupancy change
        if current_telemetry['occupancy'] != self.last_telemetry['occupancy']:
            return True
            
        # Check HVAC mode change
        if current_telemetry['hvac_mode'] != self.last_telemetry['hvac_mode']:
            return True
            
        return False

class ActuatorResource(resource.Resource):
    """CoAP resource for actuator control - Enhanced for Phase 2"""
    def __init__(self, room):
        super().__init__()
        self.room = room

    async def render_put(self, request):
        """Handle PUT requests for actuator control with confirmable response"""
        try:
            command = json.loads(request.payload.decode('utf-8'))
            logging.info(f"[COAP COMMAND] {self.room.room_id}: {command}")
            
            # Process command
            result = self.room.process_command(command)
            
            # Return confirmable response
            response_code = 2.04 if result.get("status") == "success" else 4.00
            
            return Message(
                payload=json.dumps(result).encode('utf-8'),
                content_format=ContentFormat.APPLICATION_JSON,
                code=response_code
            )
            
        except json.JSONDecodeError as e:
            error_response = {
                "status": "error",
                "message": "Invalid JSON format",
                "room_id": self.room.room_id,
                "timestamp": int(time.time())
            }
            return Message(
                payload=json.dumps(error_response).encode('utf-8'),
                code=4.00  # Bad Request
            )
        except Exception as e:
            error_response = {
                "status": "error",
                "message": str(e),
                "room_id": self.room.room_id,
                "timestamp": int(time.time())
            }
            return Message(
                payload=json.dumps(error_response).encode('utf-8'),
                code=5.00  # Internal Server Error
            )
    
    async def render_get(self, request):
        """Handle GET requests for actuator status"""
        try:
            status = self.room.get_actuator_status()
            payload = json.dumps(status).encode('utf-8')
            
            return Message(
                payload=payload,
                content_format=ContentFormat.APPLICATION_JSON,
                code=2.05  # Content
            )
            
        except Exception as e:
            error_response = {
                "status": "error",
                "message": str(e),
                "room_id": self.room.room_id
            }
            return Message(
                payload=json.dumps(error_response).encode('utf-8'),
                code=5.00  # Internal Server Error
            )

class CoAPServer:
    """CoAP Server for individual room"""
    def __init__(self, room, port=5683):
        self.room = room
        self.port = port
        self.context = None
        self.site = None

    async def start(self):
        """Start CoAP server"""
        try:
            # Create CoAP context
            self.context = await Context.create_server_context(self.port)
            
            # Create resource tree
            self.site = resource.Site()
            
            # Add resources
            telemetry_path = f"telemetry"
            actuator_path = f"actuators"
            
            self.site.add_resource([telemetry_path], TelemetryResource(self.room))
            self.site.add_resource([actuator_path], ActuatorResource(self.room))
            
            # Mount site
            self.context.serversite = self.site
            
            logging.info(f"CoAP Server for {self.room.room_id} started on port {self.port}")
            
        except Exception as e:
            logging.error(f"Failed to start CoAP server: {e}")
            raise

    async def stop(self):
        """Stop CoAP server"""
        if self.context:
            await self.context.shutdown()
            logging.info(f"CoAP Server for {self.room.room_id} stopped")

class CoAPNode:
    """Complete CoAP node with room simulation"""
    def __init__(self, room, port=5683):
        self.room = room
        self.server = CoAPServer(room, port)
        self.running = False

    async def start(self):
        """Start CoAP node"""
        self.running = True
        
        # Add startup jitter
        await asyncio.sleep(random.uniform(0, 3))
        
        try:
            await self.server.start()
            logging.info(f"CoAP Node {self.room.room_id} started successfully")
        except Exception as e:
            logging.error(f"Failed to start CoAP Node {self.room.room_id}: {e}")
            raise

    async def stop(self):
        """Stop CoAP node"""
        self.running = False
        await self.server.stop()

async def run_coap_room(room, port_offset=0):
    """Run CoAP room server"""
    node = CoAPNode(room, port=5683 + port_offset)
    
    try:
        await node.start()
        
        # Keep server running
        while node.running:
            await asyncio.sleep(1)
            
    except Exception as e:
        logging.error(f"Error in CoAP room {room.room_id}: {e}")
    finally:
        await node.stop()
