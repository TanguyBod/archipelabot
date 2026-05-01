import discord
from discord_bot.utils import build_todo_message

class TodoView(discord.ui.View):

    def __init__(self, player, owner_id):

        super().__init__(timeout=300)

        self.add_item(
            TodoSelect(player, owner_id)
        )

class TodoSelect(discord.ui.Select):

    def __init__(self, player, owner_id):

        self.player = player
        self.owner_id = owner_id

        options = []

        for i, item in enumerate(player.todolist):

            options.append(
                discord.SelectOption(
                    label=item.item_name[:100],
                    value=str(i),
                    description=item.location_name[:100],
                    emoji="✅" if item.doable else "❌"
                )
            )

        super().__init__(
            placeholder="Toggle doable items",
            min_values=1,
            max_values=min(len(options), 25),
            options=options
        )

    async def callback(self, interaction: discord.Interaction):

        if interaction.user.id != self.owner_id:

            await interaction.response.send_message(
                "This is not your todo list.",
                ephemeral=True
            )
            return

        for value in self.values:

            item = self.player.todolist[int(value)]

            item.doable = not item.doable

        # Rebuild updated message
        new_msg = build_todo_message(
            self.player.todolist
        )

        # Rebuild updated view
        new_view = TodoView(
            self.player,
            self.owner_id
        )

        await interaction.response.edit_message(
            content=new_msg,
            view=new_view
        )