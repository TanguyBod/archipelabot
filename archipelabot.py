from websockets.sync.client import connect, ClientConnection
import json
from time import sleep
import uuid

# All configuration will be defined in a config.json file.

config = json.load(open("config.json", "r"))
    
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
        self.ap_connection : ClientConnection = None
        
    def connect(self) :
        self.ap_connection = connect(
            f"ws://{self.client_url}:{self.client_port}",
            max_size=None
        )
    
    def run(self) :
        while True :
            try :
                messages = self.ap_connection.recv(timeout=1)
                messages = json.loads(messages)
                for message in messages :
                    print(message)
                    if message["cmd"] == "RoomInfo" :
                        self.send_connect()
            except TimeoutError as e :
                pass
            except Exception as e :
                print(f"Error receiving message: {e}")
                break
            
    def send_connect(self) -> None:
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
        self.send_message(payload)
        
    def send_message(self, message: dict) -> None :
        try :
            self.ap_connection.send(json.dumps([message]))
        except Exception as e :
            print(f"Error sending message: {e}")
        
client_url = "141.253.103.79"
client_port = "38281"

tracker_client = TrackerClient()
tracker_client.connect()
tracker_client.run()