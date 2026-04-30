import discord
from models.item import Item

class Button(discord.ui.View):
    def __init__(self, item: Item = None, bot_client = None):
        super().__init__(timeout=600)
        self.active = False 
        self.item = item
        self.bot_client = bot_client

    @discord.ui.button(label="Add to todolist", style=discord.ButtonStyle.primary)
    async def toggle(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.active:
            self.active = True
            button.label = "Remove from todolist"
            button.style = discord.ButtonStyle.danger

            # Add the item to the player's todolist
            print("Looking for player sending the item : "+self.item.player_sending.player_name)
            player_sending = self.bot_client.player_db.get_player_by_name(self.item.player_sending.player_name)
            # Check if the item is already in the player's todolist to avoid duplicates
            for item in player_sending.todolist:
                if item.item_name == self.item.item_name and item.location_name == self.item.location_name:
                    await interaction.response.send_message(
                        f"{self.item.item_name} is already in {player_sending.player_name}'s todolist!", ephemeral=True
                    )
                    return
            print(f"Adding item {self.item.item_name} to todolist of player {player_sending.player_name}")
            player_sending.todolist.append(self.item)
            await interaction.response.send_message(
                f"Added {self.item.item_name} to {player_sending.player_name}'s todolist!", ephemeral=True
            )

        else:
            self.active = False
            button.label = "Add to todolist"
            button.style = discord.ButtonStyle.primary

            # Remove the item from the player's todolist
            player_sending = self.bot_client.player_db.get_player_by_name(self.item.player_sending.player_name)
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