import discord
from discord.ext import commands
import os
import random
import datetime

# --- RAILWAY CONFIGURATION ---
# In the Railway Dashboard, go to 'Variables' and add:
# DISCORD_TOKEN = your_token_here
TOKEN = os.environ.get('DISCORD_TOKEN') 

# Channels
GEN_CHANNEL_ID = 1480531258516963519
LOG_CHANNEL_ID = 123456789012345678  # Update this to your Staff Log Channel ID
PREFIX = '?'
COOLDOWN_TIME = 60 

if not TOKEN:
    print("❌ ERROR: DISCORD_TOKEN variable not found in Railway Settings.")
    exit()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# Ensure the stock folder exists for Railway's local storage
if not os.path.exists("stock"):
    os.makedirs("stock")

@bot.event
async def on_ready():
    print(f'Velocity Gen Online on Railway')
    print(f'Logged in as {bot.user}')

# --- USER COMMANDS ---

@bot.command()
@commands.cooldown(1, COOLDOWN_TIME, commands.BucketType.user)
async def fgen(ctx, name: str = None):
    if ctx.channel.id != GEN_CHANNEL_ID:
        return

    if name is None:
        ctx.command.reset_cooldown(ctx)
        return await ctx.send("❌ Usage: `?fgen <category>`", delete_after=5)

    file_path = f"stock/{name.lower()}.txt"

    if not os.path.exists(file_path):
        ctx.command.reset_cooldown(ctx)
        return await ctx.send(f"❌ Category `{name}` doesn't exist. Use `?stock`.", delete_after=5)

    try:
        with open(file_path, "r") as f:
            lines = f.readlines()

        if not lines:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"📉 `{name}` is currently out of stock!", delete_after=5)

        # Pick and remove account
        account = random.choice(lines).strip()
        lines.remove(account + "\n" if account + "\n" in lines else account)

        with open(file_path, "w") as f:
            f.writelines(lines)

        # User DM
        dm = discord.Embed(title="🚀 Velocity Generator", color=0x3498db)
        dm.add_field(name="Service", value=name.upper(), inline=True)
        dm.add_field(name="Account Details", value=f"```\n{account}\n```", inline=False)
        dm.set_footer(text="Velocity Systems — Fast & Free")
        await ctx.author.send(embed=dm)

        # Public Confirm
        await ctx.send(f"✅ {ctx.author.mention}, account sent to DMs!", delete_after=10)

        # Staff Log
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log = discord.Embed(title="🛒 Gen Log", color=0x2ecc71, timestamp=datetime.datetime.now())
            log.add_field(name="User", value=f"{ctx.author} (`{ctx.author.id}`)")
            log.add_field(name="Service", value=name.upper())
            log.add_field(name="Details", value=f"||{account}||")
            await log_channel.send(embed=log)

    except discord.Forbidden:
        await ctx.send(f"❌ {ctx.author.mention}, I can't DM you! Please open your DMs.", delete_after=10)
    except Exception as e:
        print(f"Error: {e}")

@bot.command()
async def stock(ctx):
    if ctx.channel.id != GEN_CHANNEL_ID and ctx.channel.id != LOG_CHANNEL_ID:
        return

    embed = discord.Embed(title="📊 Current Inventory", color=0x3498db)
    files = [f for f in os.listdir("stock") if f.endswith(".txt")]
    
    if not files:
        embed.description = "The generator is currently empty."
    else:
        for file in files:
            cat = file.replace(".txt", "").upper()
            with open(f"stock/{file}", "r") as f:
                count = len(f.readlines())
            embed.add_field(name=cat, value=f"`{count} accounts`", inline=True)

    await ctx.send(embed=embed)

# --- ADMIN COMMANDS ---

@bot.command()
@commands.has_permissions(administrator=True)
async def add(ctx, category: str, *, account: str):
    file_path = f"stock/{category.lower()}.txt"
    with open(file_path, "a") as f:
        f.write(f"{account}\n")
    await ctx.send(f"✅ Added to **{category.upper()}**.", delete_after=5)

@bot.command()
@commands.has_permissions(administrator=True)
async def remove(ctx, category: str):
    file_path = f"stock/{category.lower()}.txt"
    if os.path.exists(file_path):
        os.remove(file_path)
        await ctx.send(f"🗑️ Deleted category **{category.upper()}**.", delete_after=5)
    else:
        await ctx.send("❌ Not found.", delete_after=5)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Wait `{error.retry_after:.1f}s`", delete_after=5)
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("🚫 Admin permissions required.", delete_after=5)

bot.run(TOKEN)

