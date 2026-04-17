from archipelago.base_client import ArchipelagoClient
from archipelago.tracker_client import TrackerClient
from utils.colors import get_ansi_color_from_flag
import asyncio

class HintClient(ArchipelagoClient) :
    def __init__(self, 
                 player_name: str, 
                 player_game: str,
                 hint : str,
                 tracker_client : TrackerClient,
                 config) :
        super().__init__(config)
        self.game = player_game
        self.tags = set('TextOnly')
        self.slot_name : str = player_name
        self.ap_connection = None
        self.discord_bot_queue = asyncio.Queue(maxsize=2000)
        self.hint_requested = hint
        self.finished_event = asyncio.Event()
        self.client_base = tracker_client
        self.hintpoints = 0
    
    async def send_hint(self) :
        payload =   {
            "cmd": "Say",
            "text": f"!hint {self.hint_requested}"
        }
        await self.send_message(payload)
        
    async def process_messages(self) :
        while self.running:
            try:
                message = await self.message_queue.get()
                if message["cmd"] == "RoomInfo" :
                    await self.send_connect()
                if message["cmd"] == "Connected" :
                    self.hintpoints = message["hint_points"]
                    await self.send_hint()
                if message["cmd"] == "PrintJSON" :
                    print(f"Processing message HintClient {self.slot_name} :\n{message}")
                    if message["type"] == 'CommandResult' :
                        text = message["data"][0]["text"]
                        print(f"Received hint result : {text}")
                        await self.discord_bot_queue.put(message["data"][0]["text"])
                        self.running = False # Running = False to stop workers
                        self.finished_event.set() # Signal that the hint has been processed to stop the client
                    if message["type"] == "Hint" :
                        msg = await self.parse_hint(message["data"])
                        await self.discord_bot_queue.put(msg)
                        self.running = False # Running = False to stop workers
                        self.finished_event.set() # Signal that the hint has been processed to stop the client
            except Exception as e:
                print(f"Error processing message (HintClient {self.slot_name}): {e}")
                continue
        
    async def parse_hint(self, data : list[dict]) -> str :
        msg_str = "```ansi\n"
        for chunk in data :
            if "type" not in chunk.keys() :
                msg_str += chunk["text"]
            elif chunk["type"] == "player_id" :
                player_slot = int(chunk["text"])
                player = self.client_base.player_db.get_player_by_slot(player_slot)
                msg_str += f"{player.player_name}"
            elif chunk["type"] == "item_id" :
                item_id = chunk["text"]
                game = self.client_base.player_db.get_player_by_slot(int(chunk["player"])).player_game
                item_name = self.client_base.datapackage["data"]["games"][game]["id_to_item_name"][item_id]
                color = await get_ansi_color_from_flag(chunk.get("flags", None))
                msg_str += f"\u001b[0;{color}m{item_name}\u001b[0m"
            elif chunk["type"] == "location_id" :
                location_id = chunk["text"]
                game = self.client_base.player_db.get_player_by_slot(int(chunk["player"])).player_game
                location_name = self.client_base.datapackage["data"]["games"][game]["id_to_location_name"][location_id]
                msg_str += f"{location_name}"
            elif chunk["type"] == "hint_status" :
                msg_str += chunk["text"]
            else :
                print(f"Unknown chunk type in hint : {chunk['type']}")
        msg_str += "\nRemaining hint points : "+str(self.hintpoints)+"```"
        return msg_str