import discord


def isCommand(message):
    return message.content.startswith('!help') or message.content.startswith('-help')

class helpMenu(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value=None

    @discord.ui.button(label = "Player Stats", style=discord.ButtonStyle.green)
    async def personalStats(self,interaction, button): 
        embed = discord.Embed(title="Manual: Personal Stats", description="Display AoE2 ladder rating of discord user")
        embed.add_field(name="Set your AoE profile", value="*-steamid <your steam id>* or *-relicid <link to your aoe2recs or aoe2companion profile>*", inline=False)
        embed.add_field(name="Set a friend's AoE profile", value="*-steamid <steam id> @User* or *-relicid <link to aoe2recs or aoe2companion profile> @User*", inline=False)
        embed.add_field(name="View personal stats", value="*-stats*", inline=False)
        embed.add_field(name="View User's stats", value="*-stats @User*",inline = False)
        embed.add_field(name="NOTE", value="Your steam id is under account details. It's a long long integer.",inline = False)
        await interaction.response.edit_message(embed=embed)


    @discord.ui.button(label = "Bracket leaderboard", style=discord.ButtonStyle.red)
    async def viewGuildLeaderboard(self,interaction, button): 
        embed = discord.Embed(title="Manual: Bracket leaderboard")
        embed.add_field(name="Note", value="Channel name must be *number*-*number* or lt-*number* or gt-*number*. '*number*' must be between 0 and 3000.",inline=False)
        embed.add_field(name="View", value="*-bracket*" )
        embed.add_field(name="Add/Remove", value="See manual for *-stats*", inline=False)
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label = "aoe2de:// links", style=discord.ButtonStyle.gray)
    async def customLobbyLinks(self,interaction, button): 
        embed = discord.Embed(title="Manual: Clickable aoe2de:// links", description="Join and spectate buttons for custom lobby links")
        embed.add_field(name="Why?", value="Discord doesn't allow aoe2de:// to be clickable. This bot creates a http link that redirects to the aoe2de link, thereby saving players from having to copy paste custom lobby links.", inline=False)
        embed.add_field(name="How?", value="Just drop a aoe2de:// link and the bot will do the rest.", inline=False)
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="Search", style=discord.ButtonStyle.green)
    async def SearchPlayer(self, interaction, button):
        embed = discord.Embed(title="Manual: Search")
        embed.description = "Use ```-search search-text``` to search up a player name. Example: ```-search kuelfd```"
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="FAQ", style=discord.ButtonStyle.blurple)
    async def FAQBox(self, interaction, button):
        embed = discord.Embed(title="Manual: FAQ")
        embed.description = "``` 1. For relic id, don't use aoe2insights. Use aoe2recs or aoe2companion instead.\n2. To find your steam id, look under Account Details on your steam page. It's a long long integer.```"
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label = "Help", style=discord.ButtonStyle.gray)
    async def helpCommand(self,interaction, button): 
        embed = discord.Embed(title="Manual: Help", description="Use -help or mention the bot to pull up bot manual")
        await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label = "Record Analysis", style=discord.ButtonStyle.gray)
    async def recAnalysisF(self,interaction, button): 
        embed = discord.Embed(title="Manual: Analysis", description="Short summary of aoe2record file.")
        embed.add_field(name="Analyse a record", value="**-result** and attach the record file to the message.", inline=False)
        await interaction.response.edit_message(embed=embed)

async def respond(message):
        await message.channel.send(view=helpMenu(), embed=discord.Embed(title="Bot Manual", description="Use the buttons to see manual on different features"))
