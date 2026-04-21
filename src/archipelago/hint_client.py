from archipelago.base_client import ArchipelagoClient
from archipelago.tracker_client import TrackerClient
from utils.colors import get_ansi_color_from_flag
from models.item import Item
import asyncio

class HintClient(ArchipelagoClient) :
    def __init__(self, 
                 player_name: str, 
                 player_game: str,
                 hint : str,
                 tracker_client : TrackerClient,
                 config) :
        super().__init__(config, logger=tracker_client.logger)
        self.game = player_game
        self.tags = set('TextOnly')
        self.slot_name : str = player_name
        self.ap_connection = None
        self.discord_bot_queue = asyncio.Queue(maxsize=2000)
        self.hint_requested = hint
        self.finished_event = asyncio.Event()
        self.client_base = tracker_client
        self.hintpoints = 0
        self.hint_found = False
    
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
                    self.logger.info(f"Processing message HintClient {self.slot_name} :\n{message}")
                    if message["type"] == 'CommandResult' :
                        text = message["data"][0]["text"]
                        self.logger.info(f"Received hint result : {text}")
                        await self.discord_bot_queue.put(message["data"][0]["text"])
                        self.running = False # Running = False to stop workers
                        self.finished_event.set() # Signal that the hint has been processed to stop the client
                    if message["type"] == "Hint" :
                        msg, item = await self.parse_hint(message["data"])
                        self.logger.info(f"Parsed hint : {msg} with item : {item.__str__()})")
                        await self.discord_bot_queue.put((msg, item))
                        self.hint_found = True
            except Exception as e:
                self.logger.error(f"Error processing message (HintClient {self.slot_name}): {e}")
                continue
            
            if self.hint_found and self.message_queue.empty() :
                self.logger.info(f"No more messages to process for hint client {self.slot_name}, stopping client.")
                self.running = False
                self.finished_event.set()
        
    async def parse_hint(self, data : list[dict]) -> tuple[str, Item] :
        item = Item()
        msg_str = "```ansi\n"
        for chunk in data :
            if "type" not in chunk.keys() :
                msg_str += chunk["text"]
            elif chunk["type"] == "player_id" :
                player_slot = int(chunk["text"])
                player = self.client_base.player_db.get_player_by_slot(player_slot)
                if item.player_recieving is None :
                    item.player_recieving = player
                else :
                    item.player_sending = player
                msg_str += f"{player.name_colored}"
            elif chunk["type"] == "item_id" :
                item_id = chunk["text"]
                game = self.client_base.player_db.get_player_by_slot(int(chunk["player"])).player_game
                item_name = self.client_base.datapackage["data"]["games"][game]["id_to_item_name"][item_id]
                color = await get_ansi_color_from_flag(chunk.get("flags", None))
                msg_str += f"\u001b[0;{color}m{item_name}\u001b[0m"
                item.item_id = item_id
                item.item_name = item_name
                item.flag = chunk.get("flags", None)
            elif chunk["type"] == "location_id" :
                location_id = chunk["text"]
                game = self.client_base.player_db.get_player_by_slot(int(chunk["player"])).player_game
                location_name = self.client_base.datapackage["data"]["games"][game]["id_to_location_name"][location_id]
                msg_str += f"{location_name}"
                item.location_id = location_id
                item.location_name = location_name
            elif chunk["type"] == "hint_status" :
                msg_str += chunk["text"]
            else :
                self.logger.warning(f"Unknown chunk type in hint : {chunk['type']}")
        msg_str += "\nRemaining hint points : "+str(self.hintpoints)+"```"
        return msg_str, item