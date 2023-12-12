from mgz.summary import Summary
import json
import discord

civId = json.load(open('./modules/100.json', 'r'))

def getWinners(file):
    winners = []
    with open(file,'rb') as aoe2rec:
        s = Summary(aoe2rec)
        players = s.get_players()
        for p in players:
            if p['winner']:
                winners+=[p['name']]
    return winners

def summaryEmbedPlayers(file):
    embed = discord.Embed(title='Rec Analysis')
    with open(file,'rb') as aoe2rec:
        s = Summary(aoe2rec)
        players = s.get_players()
        winners = []
        for p in players:
            if p['winner']:
                winners+=[p['name']]
        embed.description = ", ".join(winners) + " won."
        for p in players:
            embed.add_field(name=f"{'AI' if not p['name'] else p['name']} ({p['user_id']}) as {civId['civilizations'][str(p['civilization'])]['name']}", value=f"ELO={p['rate_snapshot']}", inline=False)
        return embed
    return embed

def summaryEmbedSettings(file):
    embed = discord.Embed(title='Rec Analysis')
    with open(file,'rb') as aoe2rec:
        s = Summary(aoe2rec)
        settings = s.get_settings()
        map_ = s.get_map()
        embed.add_field(name='map', value=map_['name'], inline=False)
        embed.add_field(name='type', value=str(settings['type'][1]), inline=True)
        embed.add_field(name='pop cap', value=str(settings['population_limit']), inline=True)
        embed.add_field(name='speed', value=str(settings['speed'][1]), inline=True)
        embed.add_field(name='diplomacy', value=str(settings['diplomacy_type']), inline=False)
        embed.add_field(name='starting resources', value=str(settings['starting_resources'][1]), inline=True)
        embed.add_field(name='starting age', value=str(settings['starting_age'][1]), inline=True)
        embed.add_field(name='end age', value=str(settings['ending_age'][1]), inline=True)
        embed.add_field(name='victory', value=str(settings['victory_condition'][1]), inline=True)
    return embed

class summaryView(discord.ui.View):
    def __init__(self, file):
        super().__init__(timeout=1000)
        self.agefile = file
        self.playersEmbed = summaryEmbedPlayers(file)
        self.settingsEmbed = summaryEmbedSettings(file)

    @discord.ui.button(label="Players", style=discord.ButtonStyle.blurple)
    async def players(self, interaction, button):
        await interaction.response.edit_message(embed=self.playersEmbed)

    @discord.ui.button(label="Settings", style=discord.ButtonStyle.blurple)
    async def settings(self, interaction, button):
        await interaction.response.edit_message(embed=self.settingsEmbed)

def summaryUI(file):
    embed = summaryEmbedPlayers(file)
    view = summaryView(file)
    return (embed,view)

def isCommand(message):
    return message.content.startswith('-result') or message.content.startswith('!result')

async def respond(message):
    if not message.attachments:
        await message.channel.send('No file attached')
        return
    aoe2recordfile = message.attachments[0]
    aoe2recordfilename = f'./aoe2record_{message.author.name}.aoe2record'
    await aoe2recordfile.save(aoe2recordfilename)
    embed, view = summaryUI(aoe2recordfilename)
    await message.channel.send(embed=embed, view=view)
