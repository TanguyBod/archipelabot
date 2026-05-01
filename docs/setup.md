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

> You can add more permissions later if your bot requires them.

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

# Configuration

Copy the configuration template:

```bash
cp config.template.json config.json
```

Then open `config.json` and fill in all required fields.

See [JSON configuration reference](https://github.com/TanguyBod/ArchiLink/blob/main/docs/json.md) for a complete description of each field.

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

Have fun!