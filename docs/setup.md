# Setup

> ⚠️ Currently, only self-hosting is supported.  
> A hosted/public version may be available in the future for users who do not want to host the bot themselves.

> ⚠️ Windows hasn't been tested yet, i cannot garuantee that code will work (you still can launch it with [WSL](https://learn.microsoft.com/en-us/windows/wsl/install))

---

# Self-hosting Guide

Before running the bot, you need to create a Discord bot application and invite it to your server.

If you already have a Discord bot configured, you can skip directly to [Clone the project and install dependencies](#clone-the-project-and-install-dependencies).

---

# Create a Discord Bot

To create a Discord bot, first log into the [Discord Developer Portal](https://discord.com/developers/applications).

## 1. Create a new application

- Click **New Application**
- Choose a name for your bot
- Create the application

---

## 2. Configure installation settings

Open the **Installation** tab and configure the following settings:

### Installation Context
Enable:

- `Guild Install`

### Default Install Settings

#### Scopes
Enable:

- `application.commands`
- `bot`

#### Bot Permissions
Enable:

- `Send Messages`

---

## 3. Configure the bot

Go to the **Bot** tab.

### Recommended settings

- *(Optional)* Upload a profile picture
- Set the bot username
- Enable:
  - `Public Bot`
  - `Message Content Intent`

### Important
Copy and save the bot token somewhere secure. We'll need it later.

---

## 4. Invite the bot to your server

Go back to the **Installation** tab.

Under **Install Link**:

- Select `Discord Provided Link`
- Copy the generated URL
- Open it in your browser
- Select the server where you want to install the bot

Your bot is now registered and ready to use.

## 5. Add Administrator Permissions to the Bot (Optional)

During world configuration, you may provide sensitive information such as an IP address or password. Granting administrator permissions to the bot allows it to automatically delete messages containing this data during setup phases, improving security.

> ⚠️ This step is optional but recommended if you frequently configure worlds with sensitive information in chat.

### How to enable it

1. Open your Discord server settings  
2. Go to the **Roles** section  
3. Find the role associated with your bot  
4. Click **Edit Role**  
5. Under the **Permissions** tab, enable **Administrator**

---

# Setup the Archipelago MultiWorld

When generating the Archipelago MultiWorld you'll have to add the [archilink.yaml](https://github.com/TanguyBod/ArchiLink/blob/main/archilink.yaml) in order to allow the bot to access messages sent by the server.

# Clone the project and install dependencies

Clone the repository:

```bash
git clone https://github.com/TanguyBod/ArchiLink.git
cd ArchiLink
```

---

## Create a virtual environment *(recommended)*

### Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
```

---

## Install dependencies

```bash
pip install -r requirements.txt
```

---

# Configure Environment Variables

Create a `.env` file at the root of the project.

You can either:

* Rename `.env.template` to `.env`
* Or create a new `.env` file and copy the contents of `.env.template`

Fill in the following values:

```env
DISCORD_APP_TOKEN=your_discord_bot_token
DISCORD_COMMAND_PREFIX=! 
DATA_DIRECTORY=/path/to/worlds/data
```

### Variables description

| Variable                 | Description                                                              |
| ------------------------ | ------------------------------------------------------------------------ |
| `DISCORD_APP_TOKEN`      | The Discord bot token obtained during bot creation.                      |
| `DISCORD_COMMAND_PREFIX` | The prefix used for bot commands (for example `!`).                      |
| `DATA_DIRECTORY`         | Directory where ArchiLink will store world data and configuration files. |

---

# Launch the application

Start the bot with:

```bash
python src/main.py
```

If everything is configured correctly, your bot should now be online.

---

# Troubleshooting

## Bot does not respond

Make sure:

- The bot is online in your Discord server
- `Message Content Intent` is enabled
- The bot token is correct
- The bot has permission to send messages

---

## Missing dependencies

Make sure you are using the correct Python version and that your virtual environment is activated before running:

```bash
pip install -r requirements.txt
```


# Done 🎉

Your bot is now setup and ready to use.

Your first interaction with it should be to add a new MultiWorld. To do so, use !newWorld command. Then you can either configure the world to track manually or uploading a json file. If you want to upload a json file, there is a template to fill :`config.template.json`

All fields are described [here](https://github.com/TanguyBod/ArchiLink/blob/main/docs/json.md)

Have fun!