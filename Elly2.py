import os
import discord
from dotenv import load_dotenv
load_dotenv()


TOKEN = os.getenv('ELLY_DISCORD_TOKEN')

client = discord.Client(intents=discord.Intents.all())

unassignableRoles = {'admin','admins','Girl Power', 'monka'}


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if len(message.content) > 250 or message.author.bot:
        return
    if message.content.startswith('-rmrole '):
        if not message.role_mentions:
            await message.channel.send('Mention the role you want to remove')
            return
        roleX = message.role_mentions[0]
        if roleX.name in unassignableRoles:
            await message.channel.send('That role is not assignable')
            return
        await message.author.remove_roles(roleX, reason="You did this to yourself")
        await message.channel.send('Role remove! ... Probably. Use -setciv @Role to set roles.')

    if message.content.startswith('-setrole '):
        if not message.role_mentions:
            await message.channel.send('Mention the role you want to set')
            return
        roleX = message.role_mentions[0]
        if roleX.name in unassignableRoles:
            await message.channel.send('That role is not assignable')
            return
        await message.author.add_roles(roleX, reason="You did this to yourself")
        await message.channel.send('Role set! ... Probably. Use -rmciv @Role to remove the role.')


client.run(TOKEN)
