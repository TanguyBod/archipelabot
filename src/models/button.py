import discord
from models.item import Item

class Button(discord.ui.View):
    def __init__(self, item: Item = None, tracker_client = None):
        super().__init__(timeout=600)
        self.active = False 
        self.item = item
        self.tracker_client = tracker_client

    @discord.ui.button(label="Add to todolist", style=discord.ButtonStyle.primary)
    async def toggle(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.active:
            self.active = True
            button.label = "Remove from todolist"
            button.style = discord.ButtonStyle.danger

            # Add the item to the player's todolist
            print("Looking for player sending the item : "+self.item.player_sending.player_name)
            player_sending = self.tracker_client.player_db.get_player_by_name(self.item.player_sending.player_name)
            print(f"Adding item {self.item.item_name} to todolist of player {player_sending.player_name}")
            player_sending.todolist.append(self.item)
            await interaction.response.send_message(
                f"Added {self.item.item_name} to todolist!", ephemeral=True
            )

        else:
            self.active = False
            button.label = "Add to todolist"
            button.style = discord.ButtonStyle.primary

            # Remove the item from the player's todolist
            player_sending = self.tracker_client.player_db.get_player_by_name(self.item.player_sending.player_name)
            print(f"Removing item {self.item.item_name} from todolist of player {player_sending.player_name}")
            if self.item in player_sending.todolist:
                player_sending.todolist.remove(self.item)
            else :
                print(f"Warning: tried to remove item {self.item.item_name} from todolist but it was not found.")
            await interaction.response.send_message(
                f"Removed {self.item.item_name} from todolist!", ephemeral=True
            )

        # 🔄 Met à jour le bouton visuellement
        await interaction.message.edit(view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if hasattr(self, "message"):
            await self.message.edit(view=self)