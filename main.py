import discord
from discord.ext import commands
import os
import random
import datetime

# --- CONFIGURATION ---
TOKEN = 'MTQ4MDUzNjMzODQ4MTU0OTMyMg.GXtwP1.yJXDoAMG5H8z5hINaCi5ZLbqjvBO8iHRSjNZYA'
GEN_CHANNEL_ID = 1480531258516963519  # Where users type commands
LOG_CHANNEL_ID = 1478094558666555432 # CHANGE THIS: ID of your private staff log channel
PREFIX = '?'
COOLDOWN_TIME = 60 # Seconds between uses

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# Ensure the stock folder exists
if not os.path.exists("stock"):
    os.makedirs("stock")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print(f'Gen Channel: {GEN_CHANNEL_ID}')
    print(f'Log Channel: {LOG_CHANNEL_ID}')

@bot.command()
@commands.cooldown(1, COOLDOWN_TIME, commands.BucketType.user)
async def fgen(ctx, name: str = None):
    # Only allow in specific gen channel
    if ctx.channel.id != GEN_CHANNEL_ID:
        return

    if name is None:
        ctx.command.reset_cooldown(ctx)
        embed = discord.Embed(title="â Error", description="Usage: `?fgen <category>`\nExample: `?fgen fortnite`", color=0xff0000)
        return await ctx.send(embed=embed)

    file_path = f"stock/{name.lower()}.txt"

    if not os.path.exists(file_path):
        ctx.command.reset_cooldown(ctx)
        embed = discord.Embed(title="ð¦ Error", description=f"Category `{name}` does not exist. Use `?stock`.", color=0xffa500)
        return await ctx.send(embed=embed)

    with open(file_path, "r") as f:
        lines = f.readlines()

    if not lines:
        ctx.command.reset_cooldown(ctx)
        embed = discord.Embed(title="ð Out of Stock", description=f"No accounts left for **{name}**.", color=0xffa500)
        return await ctx.send(embed=embed)

    # Pick and remove account
    account = random.choice(lines).strip()
    lines.remove(account + "\n" if account + "\n" in lines else account)

    with open(file_path, "w") as f:
        f.writelines(lines)

    # 1. Send DM to User
    try:
        dm_embed = discord.Embed(title="ð Velocity Generator", color=0x3498db)
        dm_embed.add_field(name="Service", value=name.capitalize(), inline=True)
        dm_embed.add_field(name="Account", value=f"`{account}`", inline=False)
        dm_embed.set_footer(text="Velocity Systems â Don't share these details!")
        await ctx.author.send(embed=dm_embed)

        # 2. Public Channel Confirmation
        channel_embed = discord.Embed(title="â Success", description=f"{ctx.author.mention}, your **{name.capitalize()}** account has been sent to your DMs!", color=0x2ecc71)
        await ctx.send(embed=channel_embed)

        # 3. Private Logging
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(title="ð Generation Log", color=0x000000, timestamp=datetime.datetime.now())
            log_embed.add_field(name="User", value=f"{ctx.author} ({ctx.author.id})", inline=False)
            log_embed.add_field(name="Category", value=name.capitalize(), inline=True)
            log_embed.add_field(name="Details", value=f"||{account}||", inline=True) # Spoiled for privacy
            await log_channel.send(embed=log_embed)

    except discord.Forbidden:
        await ctx.send(f"â {ctx.author.mention}, I couldn't DM you! Please enable your DMs and try again in {COOLDOWN_TIME}s.")

@bot.command()
async def stock(ctx):
    if ctx.channel.id != GEN_CHANNEL_ID:
        return

    files = [f for f in os.listdir("stock") if f.endswith(".txt")]
    embed = discord.Embed(title="ð Current Velocity Stock", color=0x3498db)
    
    if not files:
        embed.description = "No categories found."
    else:
        for file in files:
            category = file.replace(".txt", "").capitalize()
            with open(f"stock/{file}", "r") as f:
                count = len(f.readlines())
            embed.add_field(name=category, value=f"`{count} accounts`", inline=True)

    await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        msg = f"â³ **Cooldown!** Please wait `{error.retry_after:.1f}s` before generating another account."
        await ctx.send(msg, delete_after=5)

bot.run(TOKEN)
