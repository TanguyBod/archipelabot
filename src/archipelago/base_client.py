import asyncio
from abc import ABC, abstractmethod
import uuid
import json
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosedOK

class ArchipelagoClient(ABC) :
    version : dict[str, any] = {"major": 0, "minor": 6, "build": 0, "class": "Version"}
    items_handling: int = 0b000 # Does not receive any items
    
    def __init__(self, config: dict[str, any]) :
        self.client_url : str = config["ArchipelagoConfig"]["client_url"]
        self.client_port : str = config["ArchipelagoConfig"]["client_port"]
        self.password : str = config["ArchipelagoConfig"]["password"]
        self.password = self.password if self.password else ""
        self.uuid : int = uuid.getnode()
        self.ap_connection = None
        self.message_queue = asyncio.Queue(maxsize=2000)
        self.slot_name : str = ""
        self.tags : set[str] = set()
        self.running = True
        self.nb_workers = 4
        self.workers_started = False
        self.game = ''
        self.worker_tasks = []
    
    async def connect(self) :
        self.ap_connection = await connect(
            f"ws://{self.client_url}:{self.client_port}",
            max_size=None
        )
        
    async def send_message(self, message: dict) -> None :
        try :
            await self.ap_connection.send(json.dumps([message]))
        except Exception as e :
            print(f"Error sending message: {e}")
    
    async def send_connect(self) -> None:
        print("-- Sending `Connect` packet to log in to server.")
        payload = {
            'cmd': 'Connect',
            'game': self.game,
            'password': self.password,
            'name': self.slot_name,
            'version': ArchipelagoClient.version,
            'tags': list(self.tags),
            'items_handling': ArchipelagoClient.items_handling,
            'uuid': self.uuid,
        }
        await self.send_message(payload)
        
    async def run(self):
        while self.running:
            try:
                await self.connect()
                if not self.workers_started:
                    for _ in range(self.nb_workers):
                        task = asyncio.create_task(self.process_messages())
                        self.worker_tasks.append(task)
                    self.workers_started = True

                while self.running:
                    raw = await self.ap_connection.recv()
                    messages = json.loads(raw)
                    for message in messages:
                        await self.message_queue.put(message)
            except ConnectionClosedOK:
                print("Connection closed gracefully.")
                break
            except Exception as e:
                print(f"Connection error: {e}")
                await asyncio.sleep(5)
                
    async def stop(self) :
        self.running = False
        for task in getattr(self, "worker_tasks", []):
            task.cancel()
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        if self.ap_connection:
            await self.ap_connection.close()
    
    @abstractmethod
    async def process_messages(self) :
        pass