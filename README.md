# ArchiLink

A Discord bot designed to interact with an **Archipelago Multiworld** session directly from your server.

While existing tools (such as [Bridgeipelago](https://github.com/Quasky/bridgeipelago/tree/main)) already provide item tracking and hint management, **ArchiLink focuses on improving coordination between players by introducing cross-player todo lists**. This allows players to explicitly communicate needs and priorities, making multiworld collaboration significantly smoother and more structured.
ArchiLink can handle multiple worlds, each of them require a seperated discord channel.

Players can track progress, request hints, and — most importantly — **assign items or goals to other players via shared todo lists** directly from Discord.

Its main features are the following:

- 📦 View all collected items across players  
- 🧾 Create and manage todo lists for other players to communicate needs  
- 🔍 Request in-game hints directly from Discord  
- 📝 Add hints or items to another player's todo list  
- 🔔 Get notified when your required item is found  
- 🤝 Improve coordination and teamwork in multiworld sessions  

[Discord Link](https://discord.gg/7dEp4cMnWF)

## 

## Docker

If you plan to use this bot inside docker follow instructions [here](https://github.com/TanguyBod/ArchiLink/blob/main/docs/docker.md), otherwise go to the next section.

## Setup

All setup steps are described [here](https://github.com/TanguyBod/ArchiLink/blob/main/docs/setup.md).

# Commands

There are to sets of commands available, one set to manage worlds (start or stop tracking multiworld) and the other set to interact with these worlds.

Here is the list of commands to manage worlds :

| Command | Description |
|--------|------------|
| `!newWorld` | Initializes the bot to follow an Archipelago multiworld. Two way to configure the world are available : manual configuration or
uploading a config.json file. This command can be used anywhere. |
| `!deleteWorld` | Delete the world associated to the current channel (the bot will no longer track progress) |

Once a world is instanciated, you can interact with it with these commands :

| Command | Description |
|--------|------------|
| `!register <player_name>` | Link your Discord account to a player. You will receive notifications about this player's items and gain access to player-specific commands such as `!todo`, `!wishlist`, and `!new`. You can register to multiple players. |
| `!unregister [player_name]` | Unlink your account from a player. If no player is specified, unregisters from all registered players. |
| `!players` | Display the list of all players in the multiworld. |
| `!current` | Display the current slot you are tracking. This is the player that will be used by `!todo`, `!hint` or `!wishlist` commands. You can change this players using `!switch` command. |
| `!switch [player_name]` | Change your tracked slot to the next one in your registered slots or to the specified one if specified. This will change the slot that will be used by `!todo`, `!hint` or `!wishlist` commands. |
| `!hint <text>` | Send a hint request to the tracker. Recognized hints may allow interaction (e.g., adding items to todo lists). |
| `!new` | Check newly received items since your last check (sent via DM). |
| `!todo` | Display your current todo list. |
| `!clearTodo` | Clear your entire todo list. |
| `!removeTodo <item_name>` | Remove a specific item from your todo list. |
| `!progressGraph` | Generate a progression graph for all players (completion %, locations checked, etc.). |
| `!wishlist` | Display items other players have marked for you. |
| `!wastedOnArchipelago` | Display your total playtime in the multiworld session. |
| `!deaths` | Display your total death count. |
| `!deathgraph` | Generate a graph of your deaths over time. |
| `!progressGraph` | Generate a bar chart representing the number of checks found relative to the total number of checks per player for every player (above the bar is the number of checks found by this player)
| `!globaldeaths` | Display a comparative graph of deaths across all players. |
| `!enableping` | Enable notifications when an item in your todo list is found by another player. |
| `!disableping` | Disable ping notifications. |
| `!enablenewitems` | Enable automatic DM notifications for new items when connecting to the game. |
| `!disablenewitems` | Disable automatic DM notifications for new items (use `!new` manually instead). |
| `!help [command]` | Show all commands or detailed info for a specific command. |

