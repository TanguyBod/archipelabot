import asyncio
import discord
import json
        
STEPS = [
    "ArchipelagoConfig",
    "DiscordConfig",
    "AdvancedConfig"
]
        
class WorldConfigSelection(discord.ui.View):
    def __init__(self, author: discord.User, data: dict, timeout=600):
        super().__init__(timeout=timeout)
        self.author = author
        self.data = data
        self.blocked = False
    
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not self.author:
            return True
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(
                "You are not allowed to use this menu.",
                ephemeral=True
            )
            return False
        return True

    # Manual configuration button opens the ConfigWizardView
    @discord.ui.button(label="Manual Configuration", style=discord.ButtonStyle.green)
    async def manual(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.blocked:
            return
        self.blocked = True
        view = ConfigWizardView(data=self.data)
        step_name = STEPS[0]
        embed = discord.Embed(
            title="⚙️ Configuration - ArchipelagoConfig",
            description=f"There are 3 steps to configure a new multiworld instance. Use the buttons to navigate and edit each section.\
\nYou have 10 minutes to complete the configuration, after that the wizard will expire and you will need to start again.\
\nCurrently on step 1/3: {step_name}",
            color=0x00ffcc
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        # Block until the view is stopped, then check if data is complete and create the multiworld instance
        await view.wait()
        if view.data is None:
            await interaction.followup.send("Configuration cancelled or timed out.", ephemeral=True)
            return
        self.data.update(view.data)
        self.stop()
        
    # Import from file button (Ask user to upload a JSON file, then parse it and create multiworld instance)
    @discord.ui.button(label="Import JSON", style=discord.ButtonStyle.blurple)
    async def import_file(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.blocked:
            return
        self.blocked = True

        await interaction.response.send_message(
            "Please upload a JSON configuration file within 5 minutes.",
            ephemeral=True
        )

        def check(message: discord.Message):
            return (
                message.author.id == interaction.user.id
                and message.channel.id == interaction.channel.id
                and len(message.attachments) > 0
            )

        try:
            message = await interaction.client.wait_for(
                "message",
                check=check,
                timeout=300
            )
            attachment = message.attachments[0]
            if not attachment.filename.endswith(".json"):
                await interaction.followup.send(
                    "The uploaded file must be a JSON file.",
                    ephemeral=True
                )
                return
            file_bytes = await attachment.read()
            try:
                data = json.loads(file_bytes.decode("utf-8"))
            except json.JSONDecodeError:
                await interaction.followup.send(
                    "Invalid JSON file.",
                    ephemeral=True
                )
                return
            self.data.update(data)
            # Confirm reception and try to delete the user's message to avoid clutter
            try:
                await message.delete()
            except discord.Forbidden:
                pass
            await interaction.followup.send(
                "Configuration imported successfully.",
                ephemeral=True
            )
            self.stop()

        except asyncio.TimeoutError:
            await interaction.followup.send(
                "Timeout: no file received within 5 minutes.",
                ephemeral=True
            )
            
class ConfigWizardState:
    def __init__(self):
        self.data = {
            "ArchipelagoConfig": {},
            "DiscordConfig": {},
            "AdvancedConfig": {}
        }
        self.step = 0

class ConfigWizardView(discord.ui.View):

    def __init__(self, data: dict):
        super().__init__(timeout=600)
        self.data = data
        self.state = ConfigWizardState()

    # Dynamic message update based on current step
    async def update_message(self, interaction: discord.Interaction):

        step_name = STEPS[self.state.step]

        embed = discord.Embed(
            title=f"⚙️ Configuration - {step_name}",
            description=f"Step {self.state.step + 1}/{len(STEPS)}",
            color=0x00ffcc
        )

        embed.add_field(
            name="Current data",
            value=f"```json\n{json.dumps(self.state.data[step_name], indent=4)}\n```",
            inline=False
        )

        await interaction.response.edit_message(embed=embed, view=self)

    # Back button
    @discord.ui.button(label="◀", style=discord.ButtonStyle.primary)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):

        if self.state.step > 0:
            self.state.step -= 1

        await self.update_message(interaction)

    # Next button
    @discord.ui.button(label="▶", style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):

        if self.state.step < len(STEPS) - 1:
            self.state.step += 1

        await self.update_message(interaction)

    # Edit button opens modal for current step
    @discord.ui.button(label="Edit", style=discord.ButtonStyle.green)
    async def edit(self, interaction: discord.Interaction, button: discord.ui.Button):

        step = STEPS[self.state.step]

        modals = {
            "ArchipelagoConfig": ArchipelagoModal,
            "DiscordConfig": DiscordConfigModal,
            "AdvancedConfig": AdvancedModal
        }

        await interaction.response.send_modal(
            modals[step](self.state, self)
        )

    # Export button save current config and create multiworld instance
    @discord.ui.button(label="Save config", style=discord.ButtonStyle.success)
    async def export(self, interaction: discord.Interaction, button: discord.ui.Button):
        
        self.data = self.state.data
        await interaction.response.send_message(
            f"```json\n{json.dumps(self.state.data, indent=4)}\n```",
            ephemeral=True
        )
        self.stop()

class ArchipelagoModal(discord.ui.Modal, title="Archipelago Config"):

    def __init__(self, state, view):
        super().__init__()
        self.state = state
        self.view = view

        config = state.data.get("ArchipelagoConfig", {})

        self.client_url = discord.ui.TextInput(
            label="Client URL",
            placeholder="https://archipelago.gg or 127.0.0.1",
            default=config.get("client_url", ""),
            required=True
        )

        self.client_port = discord.ui.TextInput(
            label="Client Port",
            placeholder="8000",
            default=config.get("client_port", ""),
            required=True
        )

        self.password = discord.ui.TextInput(
            label="Password",
            placeholder="Leave empty if no password",
            default=config.get("password") or "",
            required=False
        )

        self.bot_slot = discord.ui.TextInput(
            label="Bot Slot",
            default=config.get("bot_slot", "ArchiLink"),
            required=True
        )
        
        self.self_hosted = discord.ui.TextInput(
            label="Self Hosted (true/false)",
            default=str(config.get("self_hosted", False)).lower(),
            required=True
        )

        self.add_item(self.client_url)
        self.add_item(self.client_port)
        self.add_item(self.password)
        self.add_item(self.bot_slot)
        self.add_item(self.self_hosted)

    async def on_submit(self, interaction: discord.Interaction):

        self.state.data["ArchipelagoConfig"] = {
            "client_url": self.client_url.value,
            "client_port": self.client_port.value,
            "password": self.password.value or None,
            "bot_slot": self.bot_slot.value or "ArchiLink",
            "self_hosted": False
        }

        await self.view.update_message(interaction)

        
class DiscordConfigModal(discord.ui.Modal, title="Discord Config"):

    def __init__(self, state, view):
        super().__init__()
        self.state = state
        self.view = view
        
        self.normal_channel_id = discord.ui.TextInput(
            label="Normal Channel ID",
            placeholder="Enter the ID of the normal channel",
            default=state.data.get("DiscordConfig", {}).get("normal_channel_id", ""),
            required=True
        )
        
        self.ping_channel_id = discord.ui.TextInput(
            label="Ping Channel ID",
            placeholder="Enter the ID of the ping channel (optional)",
            default=state.data.get("DiscordConfig", {}).get("ping_channel_id", "") or "",
            required=False
        )
        
        self.admin_ids = discord.ui.TextInput(
            label="Admin IDs (comma separated)",
            placeholder="Enter the IDs of the admins, separated by commas (optional)",
            default=",".join(state.data.get("DiscordConfig", {}).get("admin_ids", [])),
            required=False
        )
        
        self.add_item(self.normal_channel_id)
        self.add_item(self.ping_channel_id)
        self.add_item(self.admin_ids)
    
    async def on_submit(self, interaction: discord.Interaction):

        self.state.data["DiscordConfig"] = {
            "normal_channel_id": self.normal_channel_id.value,
            "ping_channel_id": self.ping_channel_id.value or None,
            "admin_ids": []
        }
        
        await self.view.update_message(interaction)
        
class AdvancedModal(discord.ui.Modal, title="Advanced Config"):

    def __init__(self, state, view):
        super().__init__()
        self.state = state
        self.view = view

        self.custom_deathlink_flavor = discord.ui.TextInput(
            label="Custom Deathlink Flavor (true/false)",
            placeholder="true/false",
            required=True,
            default="false"
        )

        self.auto_ping_new_items = discord.ui.TextInput(
            label="Auto Ping New Items (true/false)",
            placeholder="true/false",
            required=True,
            default="true"
        )
        
        self.player_colors_limited = discord.ui.TextInput(
            label="Ban item color for players (true/false)",
            placeholder="true/false",
            required=True,
            default="false"
        )
                
        self.add_item(self.custom_deathlink_flavor)
        self.add_item(self.auto_ping_new_items)
        self.add_item(self.player_colors_limited)
    async def on_submit(self, interaction: discord.Interaction):

        self.state.data["AdvancedConfig"] = {
            "custom_deathlink_flavor": self.custom_deathlink_flavor.value.lower() == "true",
            "auto_ping_new_items": self.auto_ping_new_items.value.lower() != "false",
            "player_colors_limited": self.player_colors_limited.value.lower() == "true"
        }
        
        await self.view.update_message(interaction)