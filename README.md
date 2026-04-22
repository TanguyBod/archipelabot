# Archipelabot
Discord bot interacting with Archipelago World.
This bot allow players to interact with the **Archipelago Multiworld** directly in Discord.
It's main features are the following :

  - Display all item collected by any player
  - Request hints
  - Add hints to other player's todolist
  - Prevent one player when it's wanted item has been found
  - Many more, try it to discover them !

## Setup

Currently only self-hosting is supported but will be hosted in the futur for those that cannot/doesn't want to host it.

### Self-hosting

#### Clone the project and install dependencies

```bash
git clone https://github.com/TanguyBod/archipelabot.git
```

It is recommanded to create a virtual environnement before installing the dependencies :
```bash
python -m venv ./.venv
source .venv/bin/activate
```

Then install dependencies :
```bash
pip install -r requirements.txt
```

#### Configuration file

Once the repo is cloned and depencies installed, you can copy the json template : 
```bash
cp config.template.json config.json
```

Then open ```config.json``` and fill all fields. See [Insert JSON.md reference] for field description.