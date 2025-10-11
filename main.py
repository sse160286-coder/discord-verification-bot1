import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# ------- CONFIG (IDs & role names) -------
VERIFY_CHANNEL_ID = 1426527917956927510    # channel where users react to verify
WELCOME_CHANNEL_ID = 1426504228393713735   # channel to send welcome messages
UNVERIFIED_ROLE_NAME = "Unverified"
VERIFIED_ROLE_NAME = "Verified"

# ------- INTENTS -------
intents = discord.Intents.default()
intents.members = True        # required to see members / on_member_join
intents.messages = True       # required for message fetches/history
intents.reactions = True      # required for reaction events (raw or normal)
intents.message_content = True  # not strictly needed for this task but commonly used

bot = commands.Bot(command_prefix="--", intents=intents)


# ------------------ HELPERS ------------------
async def ensure_roles_exist(guild: discord.Guild):
    """Return tuple (unverified_role, verified_role), creating roles if missing."""
    unverified = discord.utils.get(guild.roles, name=UNVERIFIED_ROLE_NAME)
    verified = discord.utils.get(guild.roles, name=VERIFIED_ROLE_NAME)

    if not unverified:
        try:
            unverified = await guild.create_role(name=UNVERIFIED_ROLE_NAME)
            print(f"Created role {UNVERIFIED_ROLE_NAME} in {guild.name}")
        except discord.Forbidden:
            print("Missing permission to create Unverified role.")
    if not verified:
        try:
            verified = await guild.create_role(name=VERIFIED_ROLE_NAME)
            print(f"Created role {VERIFIED_ROLE_NAME} in {guild.name}")
        except discord.Forbidden:
            print("Missing permission to create Verified role.")

    return unverified, verified


# ------------------ EVENTS ------------------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    print("🌸 Bot ready")


@bot.event
async def on_member_join(member: discord.Member):
    guild = member.guild
    unverified, verified = await ensure_roles_exist(guild)

    # Try to assign Unverified role
    if unverified:
        try:
            await member.add_roles(unverified, reason="New member - set Unverified")
        except discord.Forbidden:
            print("Missing permission to add roles to new member.")

    # Send welcome embed to the specific WELCOME_CHANNEL_ID
    welcome_channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if welcome_channel is None:
        # fallback: try to find by name or create a text channel
        welcome_channel = discord.utils.get(guild.text_channels, id=WELCOME_CHANNEL_ID)
    if welcome_channel is None:
        # last-resort: try to create a welcome channel (only if bot has perms)
        try:
            welcome_channel = await guild.create_text_channel("welcome")
        except discord.Forbidden:
            print(f"Cannot find or create welcome channel {WELCOME_CHANNEL_ID}")
            return

    embed = discord.Embed(
        title="🌸 Welcome to the Server!",
        description=f"Hey {member.mention}, we're happy to have you here! ✨\nHead to <#{VERIFY_CHANNEL_ID}> to verify and unlock everything 💫",
        color=0xFAD6A5
    )
    # safe avatar/icon usage
    avatar_url = getattr(member, "avatar", None)
    if avatar_url:
        try:
            embed.set_thumbnail(url=member.display_avatar.url)
        except Exception:
            pass
    try:
        embed.set_footer(text=f"Member #{len(guild.members)} • {guild.name}")
    except Exception:
        pass

    try:
        await welcome_channel.send(embed=embed)
    except discord.Forbidden:
        print(f"Missing permission to send welcome message in channel {WELCOME_CHANNEL_ID}.")


# Use raw event so we catch reactions for messages not in cache
@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    # ignore DMs
    if payload.guild_id is None:
        return

    # only care about the configured verify channel
    if payload.channel_id != VERIFY_CHANNEL_ID:
        return

    # only care about ✅ (unicode)
    emoji_name = getattr(payload.emoji, "name", str(payload.emoji))
    if emoji_name != "✅" and str(payload.emoji) != "✅":
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return

    # get member object (try cache, then fetch)
    member = guild.get_member(payload.user_id)
    if member is None:
        try:
            member = await guild.fetch_member(payload.user_id)
        except Exception:
            return

    # ignore bots
    if member.bot:
        return

    # Ensure roles exist
    unverified, verified = await ensure_roles_exist(guild)
    if not verified:
        # can't give role if it doesn't exist and we couldn't create it
        return

    # Try to remove Unverified and add Verified
    try:
        if unverified and unverified in member.roles:
            await member.remove_roles(unverified, reason="User verified via reaction")
        await member.add_roles(verified, reason="User verified via reaction")
    except discord.Forbidden:
        # missing Manage Roles permission or role hierarchy issue
        channel = bot.get_channel(payload.channel_id)
        if channel:
            try:
                await channel.send(f"⚠️ I don't have permission to assign roles. Please give me Manage Roles and ensure my role is above {VERIFIED_ROLE_NAME}.")
            except Exception:
                pass
        print("Missing permission to manage roles or role hierarchy problem.")
        return
    except Exception as e:
        print("Error while changing roles:", e)
        return

    # Try to DM the user (ignore if they disabled DMs)
    try:
        await member.send("✅ You’re now verified! Enjoy the server 💫")
    except Exception:
        pass

    # Optionally: remove the user's reaction to keep the verify message tidy
    try:
        channel = bot.get_channel(payload.channel_id)
        if channel:
            message = await channel.fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, member)
    except Exception:
        # ignore failures here (lack of Manage Messages, etc.)
        pass


# ------------------ SIMPLE COMMANDS ------------------
@bot.command()
async def tag(ctx, *, arg):
    if arg.lower() == "7x":
        await ctx.send("🌸 **7x Gang on Top!** ✨")
    else:
        await ctx.send(f"⚡ No tag found for '{arg}'")


@bot.command()
@commands.has_permissions(administrator=True)
async def greet(ctx, member: discord.Member = None):
    member = member or ctx.author
    welcome_channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if welcome_channel is None:
        await ctx.send("⚠️ Welcome channel not found.")
        return

    embed = discord.Embed(
        title="🌸 Welcome to the Server!",
        description=f"Hey {member.mention}, we're so happy to have you here! ✨\nPlease head to <#{VERIFY_CHANNEL_ID}> to unlock all channels 💫",
        color=0xFAD6A5
    )
    try:
        await welcome_channel.send(embed=embed)
        await ctx.send("✅ Test welcome message sent!")
    except Exception:
        await ctx.send("⚠️ Failed to send welcome message. Check my permissions.")


# ------------------ RUN ------------------
bot.run(TOKEN)
