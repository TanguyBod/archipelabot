from websockets.asyncio.client import connect
import json
from time import sleep
import uuid
import asyncio
from queue import Queue

# All configuration will be defined in a config.json file.

config = json.load(open("config.json", "r"))

items_received = Queue() # Queue of items received from the server, to be send by the discord bot
json_received = Queue() # Queue of json messages received from the server, to be send by the discord bot

    
class TrackerClient() :
    tags : set[str] = {'TextOnly', 'Tracker', 'DeathLink'}
    version : dict[str, any] = {"major": 0, "minor": 6, "build": 0, "class": "Version"}
    items_handling: int = 0b000 # Does not receive any items
    
    def __init__(self) :
        self.client_url : str = config["ArchipelagoConfig"]["client_url"]
        self.client_port : str = config["ArchipelagoConfig"]["client_port"]
        self.password : str = config["ArchipelagoConfig"]["password"]
        self.password = self.password if self.password else ""
        self.slot_name : str = config["ArchipelagoConfig"]["bot_slot"]
        self.uuid : int = uuid.getnode()
        self.ap_connection = None
        
    async def connect(self) :
        self.ap_connection = await connect(
            f"ws://{self.client_url}:{self.client_port}",
            max_size=None
        )
    
    async def run(self) :
        while True :
            try :
                messages = await self.ap_connection.recv()
                messages = json.loads(messages)
                for message in messages :
                    print(message)
                    if message["cmd"] == "RoomInfo" :
                        # Check DataPackage
                        await self.check_data_package()
                        await self.send_connect()
            except TimeoutError as e :
                pass
            except Exception as e :
                print(f"Error receiving message: {e}")
                break
    
    async def check_data_package(self) -> None :
        print("-- Checking DataPackage.")
        payload = {
            'cmd': 'GetDataPackage'
        }
        await self.send_message(payload)
            
    async def send_connect(self) -> None:
        print("-- Sending `Connect` packet to log in to server.")
        payload = {
            'cmd': 'Connect',
            'game': '',
            'password': self.password,
            'name': self.slot_name,
            'version': self.version,
            'tags': list(self.tags),
            'items_handling': self.items_handling,
            'uuid': self.uuid,
        }
        await self.send_message(payload)
        
    async def send_message(self, message: dict) -> None :
        try :
            await self.ap_connection.send(json.dumps([message]))
        except Exception as e :
            print(f"Error sending message: {e}")
        
client_url = "141.253.103.79"
client_port = "38281"

tracker_client = TrackerClient()
asyncio.run(tracker_client.connect())
asyncio.run(tracker_client.run())