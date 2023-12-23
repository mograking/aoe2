from mgz.summary import Summary
import json
import os
import discord

civId= {
  "civilizations": {
    "1": {
      "name": "Britons"
    },
    "2": {
      "name": "Franks"
    },
    "3": {
      "name": "Goths"
    },
    "4": {
      "name": "Teutons"
    },
    "5": {
      "name": "Japanese"
    },
    "6": {
      "name": "Chinese"
    },
    "7": {
      "name": "Byzantines"
    },
    "8": {
      "name": "Persians"
    },
    "9": {
      "name": "Saracens"
    },
    "10": {
      "name": "Turks"
    },
    "11": {
      "name": "Vikings"
    },
    "12": {
      "name": "Mongols"
    },
    "13": {
      "name": "Celts"
    },
    "14": {
      "name": "Spanish"
    },
    "15": {
      "name": "Aztecs"
    },
    "16": {
      "name": "Mayans"
    },
    "17": {
      "name": "Huns"
    },
    "18": {
      "name": "Koreans"
    },
    "19": {
      "name": "Italians"
    },
    "20": {
      "name": "Hindustanis"
    },
    "21": {
      "name": "Incas"
    },
    "22": {
      "name": "Magyars"
    },
    "23": {
      "name": "Slavs"
    },
    "24": {
      "name": "Portuguese"
    },
    "25": {
      "name": "Ethiopians"
    },
    "26": {
      "name": "Malians"
    },
    "27": {
      "name": "Berbers"
    },
    "28": {
      "name": "Khmer"
    },
    "29": {
      "name": "Malay"
    },
    "30": {
      "name": "Burmese"
    },
    "31": {
      "name": "Vietnamese"
    },
    "32": {
      "name": "Bulgarians"
    },
    "33": {
      "name": "Tatars"
    },
    "34": {
      "name": "Cumans"
    },
    "35": {
      "name": "Lithuanians"
    },
    "36": {
      "name": "Burgundians"
    },
    "37": {
      "name": "Sicilians"
    },
    "38": {
      "name": "Poles"
    },
    "39": {
      "name": "Bohemians"
    },
    "40": {
      "name": "Dravidians"
    },
    "41": {
      "name": "Bengalis"
    },
    "42": {
      "name": "Gurjaras"
    },
    "43": {
      "name": "Romans"
    },
    "44": {
      "name": "Armenians"
    },
    "45": {
      "name": "Georgians"
    }
  }
}

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
