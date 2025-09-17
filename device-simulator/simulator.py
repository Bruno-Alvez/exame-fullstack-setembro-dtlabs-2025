import asyncio
import aiohttp
import random
import time
import json
import os
import structlog
from datetime import datetime, timedelta
from typing import Dict, List, Any
from faker import Faker
from decouple import config

logger = structlog.get_logger()
fake = Faker()

class DeviceSimulator:
    def __init__(self):
        self.api_base_url = config('API_BASE_URL', default='http://localhost:8000')
        self.device_count = config('DEVICE_COUNT', default=10, cast=int)
        self.failure_rate = config('FAILURE_RATE', default=0.05, cast=float)
        self.scenario = config('SCENARIO', default='mixed')
        self.geographic_spread = config('GEOGRAPHIC_SPREAD', default=True, cast=bool)
        self.profiles = self._parse_profiles(config('PROFILES', default='server:3,iot:4,router:3'))
        
        self.devices = []
        self.session = None
        
    def _parse_profiles(self, profiles_str: str) -> Dict[str, int]:
        profiles = {}
        for profile in profiles_str.split(','):
            name, count = profile.strip().split(':')
            profiles[name] = int(count)
        return profiles
    
    async def create_session(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'Content-Type': 'application/json'}
        )
    
    async def close_session(self):
        if self.session:
            await self.session.close()
    
    async def register_devices(self):
        for profile_name, count in self.profiles.items():
            for i in range(count):
                device_data = self._generate_device_data(profile_name, i)
                
                try:
                    async with self.session.post(
                        f"{self.api_base_url}/api/v1/devices/",
                        json=device_data
                    ) as response:
                        if response.status == 201:
                            device = await response.json()
                            self.devices.append(device)
                            logger.info(
                                "Device registered",
                                device_id=device['id'],
                                name=device['name'],
                                profile=profile_name
                            )
                        else:
                            logger.error(
                                "Failed to register device",
                                status=response.status,
                                profile=profile_name
                            )
                except Exception as e:
                    logger.error("Error registering device", error=str(e), profile=profile_name)
    
    def _generate_device_data(self, profile: str, index: int) -> Dict[str, Any]:
        locations = [
            "São Paulo, BR", "Rio de Janeiro, BR", "Belo Horizonte, BR",
            "Brasília, BR", "Salvador, BR", "Fortaleza, BR",
            "Manaus, BR", "Curitiba, BR", "Recife, BR", "Porto Alegre, BR"
        ]
        
        return {
            "name": f"{profile.title()}-{index+1:03d}",
            "location": random.choice(locations),
            "serial_number": f"{random.randint(100000000000, 999999999999)}",
            "description": f"Simulated {profile} device for testing"
        }
    
    def _generate_heartbeat_data(self, device: Dict[str, Any]) -> Dict[str, Any]:
        profile = device['name'].split('-')[0].lower()
        
        if profile == 'server':
            return self._generate_server_metrics()
        elif profile == 'iot':
            return self._generate_iot_metrics()
        elif profile == 'router':
            return self._generate_router_metrics()
        else:
            return self._generate_mixed_metrics()
    
    def _generate_server_metrics(self) -> Dict[str, Any]:
        base_cpu = random.uniform(20, 60)
        base_ram = random.uniform(30, 70)
        
        if random.random() < self.failure_rate:
            base_cpu = random.uniform(80, 95)
            base_ram = random.uniform(85, 95)
        
        return {
            "cpu_usage": round(base_cpu + random.uniform(-5, 5), 2),
            "ram_usage": round(base_ram + random.uniform(-5, 5), 2),
            "temperature": round(random.uniform(35, 55), 2),
            "free_disk_space": round(random.uniform(20, 80), 2),
            "dns_latency": round(random.uniform(10, 50), 2),
            "connectivity": random.random() > 0.02,
            "boot_timestamp": datetime.utcnow() - timedelta(
                hours=random.randint(1, 168)
            ).isoformat()
        }
    
    def _generate_iot_metrics(self) -> Dict[str, Any]:
        base_cpu = random.uniform(5, 30)
        base_ram = random.uniform(10, 40)
        
        if random.random() < self.failure_rate * 2:
            base_cpu = random.uniform(70, 90)
            base_ram = random.uniform(60, 85)
        
        return {
            "cpu_usage": round(base_cpu + random.uniform(-3, 3), 2),
            "ram_usage": round(base_ram + random.uniform(-3, 3), 2),
            "temperature": round(random.uniform(25, 45), 2),
            "free_disk_space": round(random.uniform(40, 90), 2),
            "dns_latency": round(random.uniform(20, 100), 2),
            "connectivity": random.random() > 0.05,
            "boot_timestamp": datetime.utcnow() - timedelta(
                hours=random.randint(1, 720)
            ).isoformat()
        }
    
    def _generate_router_metrics(self) -> Dict[str, Any]:
        base_cpu = random.uniform(10, 40)
        base_ram = random.uniform(20, 50)
        
        if random.random() < self.failure_rate:
            base_cpu = random.uniform(60, 80)
            base_ram = random.uniform(70, 90)
        
        return {
            "cpu_usage": round(base_cpu + random.uniform(-4, 4), 2),
            "ram_usage": round(base_ram + random.uniform(-4, 4), 2),
            "temperature": round(random.uniform(30, 50), 2),
            "free_disk_space": round(random.uniform(30, 70), 2),
            "dns_latency": round(random.uniform(5, 30), 2),
            "connectivity": random.random() > 0.01,
            "boot_timestamp": datetime.utcnow() - timedelta(
                hours=random.randint(1, 240)
            ).isoformat()
        }
    
    def _generate_mixed_metrics(self) -> Dict[str, Any]:
        return random.choice([
            self._generate_server_metrics(),
            self._generate_iot_metrics(),
            self._generate_router_metrics()
        ])
    
    async def send_heartbeat(self, device: Dict[str, Any]):
        heartbeat_data = self._generate_heartbeat_data(device)
        
        try:
            async with self.session.post(
                f"{self.api_base_url}/api/v1/heartbeats/{device['id']}",
                json=heartbeat_data
            ) as response:
                if response.status == 201:
                    logger.debug(
                        "Heartbeat sent",
                        device_id=device['id'],
                        health_score=heartbeat_data.get('health_score', 'N/A')
                    )
                else:
                    logger.warning(
                        "Heartbeat failed",
                        device_id=device['id'],
                        status=response.status
                    )
        except Exception as e:
            logger.error("Error sending heartbeat", device_id=device['id'], error=str(e))
    
    async def simulate_heartbeats(self):
        while True:
            for device in self.devices:
                await self.send_heartbeat(device)
                await asyncio.sleep(0.1)
            
            await asyncio.sleep(60)
    
    async def run(self):
        logger.info("Starting DeviceWatch Simulator", 
                   device_count=self.device_count,
                   scenario=self.scenario)
        
        await self.create_session()
        
        try:
            await self.register_devices()
            logger.info("All devices registered", count=len(self.devices))
            
            await self.simulate_heartbeats()
        except KeyboardInterrupt:
            logger.info("Simulator stopped by user")
        except Exception as e:
            logger.error("Simulator error", error=str(e))
        finally:
            await self.close_session()

async def main():
    simulator = DeviceSimulator()
    await simulator.run()

if __name__ == "__main__":
    asyncio.run(main())
