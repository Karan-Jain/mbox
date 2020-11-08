from typing import List, Union
import discord
import os, sys
import logging
import tasks.preinitialization
import tasks.parser
import tasks.profile

discord_token = os.environ.get('DiscordToken_mbox')
mbox = discord.Client()

logging_level = logging.INFO
if len(sys.argv) > 1:
    if sys.argv[1] == 'debug':
        logging_level = logging.DEBUG

logging.basicConfig(
    level=logging_level,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("debug.log", encoding='utf8'),
        logging.StreamHandler()
    ]
)

watching_channels = []
profiles: List[tasks.profile.Profile] = []

@mbox.event
async def on_ready():
    logging.info('Logged on as {0.user}'.format(mbox))
    await tasks.preinitialization.generate_profiles(mbox.guilds, mbox, profiles)
    for profile in profiles:
        if(not profile.ready):
            await profile.setup()

@mbox.event
async def on_typing(channel, user, when):
    logging.debug('Typing from {0.name}'.format(user))

@mbox.event
async def on_guild_join(guild):
    logging.info('Joined Server: {0.name}'.format(guild))
    await guild.text_channels[0].send('Thanks for adding Music Bot!')
    await tasks.preinitialization.generate_profile(guild, mbox, profiles)
    for profile in profiles:
        if(not profile.ready):
            await profile.setup()
    print(len(profiles))

@mbox.event
async def on_guild_remove(guild):
    logging.info('Removed from Server: {0.name}'.format(guild))
    for profile in profiles:
        if profile.guild == guild:
            await profile.messenger.unregister_all()
            profiles.remove(profile)
    print(len(profiles))


@mbox.event
async def on_message(message):
    if message.author == mbox.user:
        return

    logging.debug('Message from {0.author}: {0.content}'.format(message))
    if message.content == 'stop':
        logging.info('Received stop from {0.name}'.format(message.author))
        await mbox.logout()
    
    for profile in profiles:
        if message.content == 'test':
            logging.info('Received test from {0.name}'.format(message.author))
            await message.delete()
            profile.player.connected_client.pause()
            break
        if message.content == 'rem':
            logging.info('Received rem from {0.name}'.format(message.author))
            await message.delete()
            await profile.messenger.gui['lyrics'].actions[0].remove_all()
            break
        if profile.messenger.command_channel == message.channel:
            await message.delete()
            await tasks.parser.message(message, profile)
            break

@mbox.event
async def on_reaction_add(reaction: discord.Reaction, user: Union[discord.Member, discord.User]):
    if user != mbox.user:
        if reaction.message.author == mbox.user:
            await reaction.message.remove_reaction(reaction, user)

mbox.run(discord_token)
