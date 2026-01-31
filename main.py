import os
import sys
import asyncio
import sqlite3
import discord
from discord.ext import commands

# ---------------------------------------------------------
#  BASIC STARTUP (NO UPDATER, NO REPAIR SYSTEM)
# ---------------------------------------------------------

print("Auto-update disabled (container mode).")

# ---------------------------------------------------------
#  TOKEN LOADING (RAILWAY-SAFE)
# ---------------------------------------------------------

bot_token = os.getenv("WOS_TOKEN")

if not bot_token:
    print("ERROR: No bot token found in environment variable WOS_TOKEN.")
    sys.exit(1)

# ---------------------------------------------------------
#  DISCORD BOT SETUP
# ---------------------------------------------------------

class CustomBot(commands.Bot):
    async def on_error(self, event_name, *args, **kwargs):
        if event_name == "on_interaction":
            error = sys.exc_info()[1]
            if isinstance(error, discord.NotFound) and error.code == 10062:
                return
        await super().on_error(event_name, *args, **kwargs)

    async def on_command_error(self, ctx, error):
        if isinstance(error, discord.NotFound) and error.code == 10062:
            return
        await super().on_command_error(ctx, error)

intents = discord.Intents.default()
intents.message_content = True

bot = CustomBot(command_prefix="/", intents=intents)

# ---------------------------------------------------------
#  DATABASE SETUP
# ---------------------------------------------------------

if not os.path.exists("db"):
    os.makedirs("db")
    print("db folder created")

databases = {
    "conn_alliance": "db/alliance.sqlite",
    "conn_giftcode": "db/giftcode.sqlite",
    "conn_changes": "db/changes.sqlite",
    "conn_users": "db/users.sqlite",
    "conn_settings": "db/settings.sqlite",
}

connections = {name: sqlite3.connect(path) for name, path in databases.items()}

print("Database connections have been successfully established.")

def create_tables():
    with connections["conn_changes"] as conn_changes:
        conn_changes.execute("""CREATE TABLE IF NOT EXISTS nickname_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            fid INTEGER, 
            old_nickname TEXT, 
            new_nickname TEXT, 
            change_date TEXT
        )""")

        conn_changes.execute("""CREATE TABLE IF NOT EXISTS furnace_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            fid INTEGER, 
            old_furnace_lv INTEGER, 
            new_furnace_lv INTEGER, 
            change_date TEXT
        )""")

    with connections["conn_settings"] as conn_settings:
        conn_settings.execute("""CREATE TABLE IF NOT EXISTS botsettings (
            id INTEGER PRIMARY KEY, 
            channelid INTEGER, 
            giftcodestatus TEXT 
        )""")

        conn_settings.execute("""CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY, 
            is_initial INTEGER
        )""")

    with connections["conn_users"] as conn_users:
        conn_users.execute("""CREATE TABLE IF NOT EXISTS users (
            fid INTEGER PRIMARY KEY, 
            nickname TEXT, 
            furnace_lv INTEGER DEFAULT 0, 
            kid INTEGER, 
            stove_lv_content TEXT, 
            alliance TEXT
        )""")

    with connections["conn_giftcode"] as conn_giftcode:
        conn_giftcode.execute("""CREATE TABLE IF NOT EXISTS gift_codes (
            giftcode TEXT PRIMARY KEY, 
            date TEXT
        )""")

        conn_giftcode.execute("""CREATE TABLE IF NOT EXISTS user_giftcodes (
            fid INTEGER, 
            giftcode TEXT, 
            status TEXT, 
            PRIMARY KEY (fid, giftcode),
            FOREIGN KEY (giftcode) REFERENCES gift_codes (giftcode)
        )""")

    with connections["conn_alliance"] as conn_alliance:
        conn_alliance.execute("""CREATE TABLE IF NOT EXISTS alliancesettings (
            alliance_id INTEGER PRIMARY KEY, 
            channel_id INTEGER, 
            interval INTEGER
        )""")

        conn_alliance.execute("""CREATE TABLE IF NOT EXISTS alliance_list (
            alliance_id INTEGER PRIMARY KEY, 
            name TEXT
        )""")

    print("All tables checked.")

create_tables()

# ---------------------------------------------------------
#  LOAD COGS
# ---------------------------------------------------------

async def load_cogs():
    cogs = [
        "pimp_my_bot", "olddb", "control", "alliance",
        "alliance_member_operations", "bot_operations", "logsystem",
        "support_operations", "gift_operations", "changes", "w", "wel",
        "other_features", "bear_trap", "bear_trap_schedule", "id_channel",
        "backup_operations", "bear_trap_editor", "bear_trap_templates",
        "bear_trap_wizard", "attendance", "attendance_report",
        "minister_schedule", "minister_menu", "minister_archive",
        "registration"
    ]

    failed = []

    for cog in cogs:
        try:
            await bot.load_extension(f"cogs.{cog}")
        except Exception as e:
            print(f"✗ Failed to load cog {cog}: {e}")
            failed.append(cog)

    if failed:
        print(f"\n⚠️  {len(failed)} cog(s) failed to load:")
        for cog in failed:
            print(f"   • {cog}")
        print("\nBot will continue with reduced functionality.\n")

# ---------------------------------------------------------
#  BOT READY EVENT
# ---------------------------------------------------------

@bot.event
async def on_ready():
    try:
        print(f"Logged in as {bot.user}")
        await bot.tree.sync()
    except Exception as e:
        print(f"Error syncing commands: {e}")

# ---------------------------------------------------------
#  MAIN LOOP
# ---------------------------------------------------------

async def main():
    await load_cogs()

    while True:
        try:
            await bot.start(bot_token)
            break
        except discord.HTTPException as e:
            print(f"HTTP error {e.status}, retrying in 30 seconds...")
            await asyncio.sleep(30)
        except Exception as e:
            print(f"Unexpected error: {e}")
            await asyncio.sleep(30)

# ---------------------------------------------------------
#  ENTRY POINT
# ---------------------------------------------------------

if __name__ == "__main__":
    asyncio.run(main())
