def check_config(data) :
    # Check if all required fields are present
    required_fields = [
        "ArchipelagoConfig",
        "DiscordConfig",
        "AdvancedConfig"
    ]
    for field in required_fields:
        if field not in data:
            return data, False
        
    # Check if all required subfields are present
    archipelago_config_fields = [
        "client_url",
        "client_port",
        "password",
        "bot_slot",
        "self_hosted"
    ]
    for field in archipelago_config_fields:
        if field not in data["ArchipelagoConfig"]:
            return data, False
        
    discord_config_fields = [
        "normal_channel_id",
        "ping_channel_id",
        "admin_ids"
    ]
    for field in discord_config_fields:
        if field not in data["DiscordConfig"]:
            return data, False
        
    advanced_config_fields = [
        "custom_deathlink_flavor",
        "auto_ping_new_items"
    ]    
    for field in advanced_config_fields:
        if field not in data["AdvancedConfig"]:
            return data, False
        
    # Trim data to only the required fields to avoid storing unnecessary data
    trimmed_data = {}
    trimmed_data["ArchipelagoConfig"] = {field: data["ArchipelagoConfig"][field] for field in archipelago_config_fields}
    trimmed_data["DiscordConfig"] = {field: data["DiscordConfig"][field] for field in discord_config_fields}
    trimmed_data["AdvancedConfig"] = {field: data["AdvancedConfig"][field] for field in advanced_config_fields}
        
    return trimmed_data, True