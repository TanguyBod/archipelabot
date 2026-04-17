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