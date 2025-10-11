import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load token from .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Intents setup
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="--", intents=intents)

# ========== EVENTS ==========
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    print("🌸 Bot is live and ready to go!")

@bot.event
async def on_member_join(member):
    guild = member.guild

    # Create roles if missing
    unverified = discord.utils.get(guild.roles, name="Unverified")
    verified = discord.utils.get(guild.roles, name="Verified")
    if not unverified:
        unverified = await guild.create_role(name="Unverified")
    if not verified:
        verified = await guild.create_role(name="Verified")

    # Assign Unverified on join
    await member.add_roles(unverified)

    # Create or find welcome and verify channels
    welcome_channel = discord.utils.get(guild.text_channels, name="👋│𝐰𝐞𝐥𝐜𝐨𝐦𝐞")
    if not welcome_channel:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        welcome_channel = await guild.create_text_channel("👋│𝐰𝐞𝐥𝐜𝐨𝐦𝐞", overwrites=overwrites)

    verify_channel = discord.utils.get(guild.text_channels, name="✅ verify")
    if not verify_channel:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        verify_channel = await guild.create_text_channel("✅ verify", overwrites=overwrites)

    # Welcome embed
    embed = discord.Embed(
        title="🌸 𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐭𝐨 𝐭𝐡𝐞 𝐒𝐞𝐫𝐯𝐞𝐫!",
        description=f"Hey {member.mention}, we're happy to have you here! ✨\nHead to **#✅ verify** to unlock everything 💫",
        color=0xFAD6A5
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else guild.icon.url)
    embed.set_footer(text=f"Member #{len(guild.members)} • {guild.name}")
    await welcome_channel.send(embed=embed)

    # Send verification embed (once)
    existing = [msg async for msg in verify_channel.history(limit=5)]
    if not any("Verify Yourself" in (msg.embeds[0].title if msg.embeds else "") for msg in existing):
        v_embed = discord.Embed(
            title="🔒 Verify Yourself",
            description="Click the ✅ below to verify and unlock all channels 🌸",
            color=0xF2B5D4
        )
        v_embed.set_footer(text="Verification System • Stay Safe 🌷")
        msg = await verify_channel.send(embed=v_embed)
        await msg.add_reaction("✅")

# ========== REACTIONS ==========
@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    if reaction.message.channel.name == "✅ verify" and str(reaction.emoji) == "✅":
        guild = reaction.message.guild
        verified = discord.utils.get(guild.roles, name="Verified")
        unverified = discord.utils.get(guild.roles, name="Unverified")
        member = guild.get_member(user.id)

        if unverified in member.roles:
            await member.remove_roles(unverified)
            await member.add_roles(verified)
            await user.send("✅ You’re now verified! Enjoy the server 💫")

# ========== COMMANDS ==========
@bot.command()
async def tag(ctx, *, arg):
    if arg.lower() == "7x":
        await ctx.send("🌸 **7x Gang on Top!** ✨")
    else:
        await ctx.send(f"⚡ No tag found for '{arg}'")

@bot.command()
@commands.has_permissions(administrator=True)
async def greet(ctx, member: discord.Member = None):
    """Send a test welcome message manually"""
    member = member or ctx.author
    guild = ctx.guild

    welcome_channel = discord.utils.get(guild.text_channels, name="👋│𝐰𝐞𝐥𝐜𝐨𝐦𝐞")
    if not welcome_channel:
        await ctx.send("⚠️ No welcome channel found.")
        return

    embed = discord.Embed(
        title="🌸 𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐭𝐨 𝐭𝐡𝐞 𝐒𝐞𝐫𝐯𝐞𝐫!",
        description=f"Hey {member.mention}, we're so happy to have you here! ✨\n\nPlease head to **#✅ verify** to unlock all channels 💫",
        color=0xFAD6A5
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else guild.icon.url)
    embed.set_footer(text=f"Member #{len(guild.members)} • {guild.name}")

    await welcome_channel.send(embed=embed)
    await ctx.send("✅ Test welcome message sent!")

# ========== RUN ==========
bot.run(TOKEN)
