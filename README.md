# ArchiLink
A Discord bot designed to interact with an **Archipelago Multiworld** session directly from your server.
It allows players to track progress, request hints, and collaborate more efficiently without leaving Discord.
Its main features are the following :

- 📦 View all collected items across players
- 🔍 Request in-game hints directly from Discord
- 📝 Add hints to another player's to-do list
- 🔔 Get notified when your required item is found
- 🤝 Improve coordination in multiworld sessions

## Setup

Currently only self-hosting is supported but will be hosted in the futur for those that cannot/doesn't want to host it.

### Self-hosting

Before hosting a discord bot for your server, you'll have to create one : [reference to discord bot creation]

#### Clone the project and install dependencies

```bash
git clone https://github.com/TanguyBod/ArchiLink.git
```

It is recommended to create a virtual environment before installing the dependencies :
```bash
python -m venv ./.venv
source .venv/bin/activate
```

Then install dependencies :
```bash
pip install -r requirements.txt
```

#### Configuration file

Once the repo is cloned and dependencies installed, you can copy the json template : 
```bash
cp config.template.json config.json
```

Then open ```config.json``` and fill all fields. See [Insert JSON.md reference] for fields description.

#### Launch the application

Launch the application by running : 
```bash
python src/main.py
```
Your bot is now setup ! Have fun !

## Commands

Here is the list of available commands:

| Command | Description |
|--------|------------|
| `!register <player_name>` | Link your Discord account to a player. You will receive notifications about this player's items and gain access to their todo list and updates. |
| `!unregister [player_name]` | Unlink your account. If no player is specified, unregisters from your current player. If provided, unregisters from that specific player. |
| `!players` | Display the list of all players in the tracker. |
| `!hint <hint>` | Send a hint to the tracker. The hint will be processed and can be added to the target player's todo list. |
| `!new` | Show new items received since your last check. Results are sent via DM to avoid channel spam. |
| `!enableping` | Enable notifications when an item in your todo list is found by another player. |
| `!disableping` | Disable notifications for found items. |
| `!todo` | Display your current todo list. |
| `!clear_todo` | Clear your todo list. |
| `!remove_todo <item_name>` | Remove the specified item from your todolist |
| `!help [command]` | Show all commands or detailed info for a specific command. |

