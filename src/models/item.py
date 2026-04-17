class Item:
    def __init__(
        self,
        item_name=None,
        item_id=None,
        game=None,
        location_name=None,
        location_id=None,
        player_sending=None,
        player_recieving=None,
        flag=None,
    ):
        self.item_name = item_name
        self.item_id = item_id
        self.game = game
        self.location_name = location_name
        self.location_id = location_id
        self.player_sending = player_sending
        self.player_recieving = player_recieving
        self.flag = flag

    def __str__(self):
        return f"Item(name={self.item_name or 'Unknown'}, \
        id={self.item_id or 'Unknown'}, \
        game={self.game or 'Unknown'}, \
        location_name={self.location_name or 'Unknown'}, \
        location_id={self.location_id or 'Unknown'}, \
        player_sending={self.player_sending.player_name if self.player_sending else None}, \
        player_recieving={self.player_recieving.player_name if self.player_recieving else None}, \
        flag={self.flag or 'None'})"