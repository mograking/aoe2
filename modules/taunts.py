import discord



taunts = {}
taunts[11]="./public/Herb_laugh.ogg"
taunts[2]="./public/No.ogg"
taunts[1]="./public/Yes.ogg"
taunts[14]="./public/Start_the_game.ogg"
taunts[105]="./public/T_105.ogg"

def isCommand(message):
    return message.content.strip() in ["1","2","11","14","105"]

async def respond(message):
    tauntNu = int(message.content.strip())
    await message.channel.send(file=discord.File(taunts[tauntNu]))



