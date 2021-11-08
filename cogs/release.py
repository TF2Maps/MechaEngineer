#un implemented

from asyncio.windows_events import NULL
import discord
from discord import client
from discord.ext.commands import Cog, command, has_any_role
from discord.ext import commands
from utils import load_config

global_config = load_config()
config = global_config

# TWITTER KEYS (...would go here)
consumer_key = None
consumer_secret = None
access_token = None
access_token_secret = None

#colors
tf2_color = 0xB98A2E
art_color = 0xde1f1f
other_color = 0x868686

class twitter(Cog):

    @commands.command()
    @has_any_role('Staff', 'Server Mods', 'Senior Staff', 'Fub')
    async def release(self, ctx):

        #delete message in channel it was sent
        await ctx.message.delete()
        #sends message as dm
        msg = await ctx.author.send("Welcome to TF2Maps release submission. Type cancel at anytime to stop the submission.")
        
        #check to make sure the link is sent in dms
        def check(message):
            return message.author == ctx.author and message.channel == msg.channel

        step = 0  
        submissioncategory = ''
        submissionlink = ''
        canceled = False
        img = ''
        #test number
        while(step < 10): 
            #get submission category    
            if(step == 0):
                msg = await ctx.author.send('**First let me have the category of what you are submitting. Map, Item, Art, or Other**')
                link = await ctx.bot.wait_for('message', check=check)
                print(link.content)
            
                if(link.content == 'map' or link.content == 'Map'):
                    step = 1
                elif(link.content == 'item' or link.content == 'Item'):
                    step = 1
                elif(link.content == 'art' or link.content == 'Art'):
                    step = 1
                elif(link.content == 'other' or link.content == 'Other'):
                    step = 1
                elif(link.content == 'cancel'):
                    canceled = True                        
                    break 
                else:
                    await ctx.author.send('**Invalid category.**')
                    step = 0

            #get link for submission
            if(step == 1):
                #map
                if(link.content == 'map' or link.content == 'Map'):
                    submissioncategory = 'Map'
                    msg = await ctx.author.send('**Great! Now send me either a Steam Workshop link or TF2Maps.net link.**')
                    link = await ctx.bot.wait_for('message', check=check)
                    print(link.content)
                    if valid_link(link.content):
                        await ctx.author.send('**Valid Link.**')
                        submissionlink = link.content
                        step = 2
                    else:
                        step = 1
                #item
                elif(link.content == 'item' or link.content == 'Item'):
                    submissioncategory = 'Item'
                    msg = await ctx.author.send('**Great! Now send me a Steam Workshop link.**')
                    link = await ctx.bot.wait_for('message', check=check)
                    print(link.content)
                    if(link.content == 'cancel'):
                        canceled = True                        
                        break 
                    if valid_link(link.content):
                        await ctx.author.send('**Valid Link.**')
                        submissionlink = link.content
                        step = 2
                    else:
                        step = 1
                #art
                elif(link.content == 'art' or link.content == 'Art'):
                    submissioncategory = 'Art'
                    msg = await ctx.author.send('**Great! Now send me link to the art or directly upload it to discord in this channel.**')
                    link = await ctx.bot.wait_for('message', check=check)
                    if(link.content == 'cancel'):
                        canceled = True                        
                        break 
                    print (link.content)
                    submissionlink = link.content
                    step = 2
                #other
                elif(link.content == 'other' or link.content == 'other'):
                    submissioncategory = 'Other'
                    msg = await ctx.author.send('**Great! Now send me a link to what you are submitting.**')
                    link = await ctx.bot.wait_for('message', check=check)
                    if(link.content == 'cancel'):
                        canceled = True                        
                        break 
                    print(link.content)
                    submissionlink = link.content
                    step = 2             
                else:
                    msg = await ctx.author.send('**Error. Please start the submission over by typing !release in #bot.**')
                    break
            
            if(step == 2):
                if(submissioncategory == 'Map'):
                    pass
                elif(submissioncategory == 'Item'):
                    pass
                elif(submissioncategory == 'Art'):

                    #todo
                    #direct upload image to discord does not work for whatever reason
                    msg = await ctx.author.send('**Does this look alright? Y/N**')
                    embed = discord.Embed()
                    embed.set_author(name=submissioncategory)
                    embed.set_image(url=submissionlink)
                    embed.set_footer(text=global_config.bot_footer)
                    await ctx.author.send(embed=embed)

                    link = await ctx.bot.wait_for('message', check=check)
                    if(link.content == 'Y' or link.content == 'y'):
                        step = 3
                        break
                    else:
                        await ctx.author.send('**Let us start over then.**')
                        step = 0

                elif(submissioncategory == 'Other'):
                    #todo
                    msg = await ctx.author.send('**Does this look alright? Y/N**')
                    embed = discord.Embed()
                    embed.set_author(name=submissioncategory)
                    embed.add_field(name='Content', value=submissionlink, inline=True)
                    embed.set_footer(text=global_config.bot_footer)
                    await ctx.author.send(embed=embed)

                    link = await ctx.bot.wait_for('message', check=check)
                    if(link.content == 'Y' or link.content == 'y'):
                        step = 3
                        break
                    else:
                        await ctx.author.send('**Let us start over then.**')
                        step = 0
                elif(link.content == 'cancel'):
                    canceled = True
                    break              
                else:
                    pass
                    break

        if(canceled == True):
            msg = await ctx.author.send('**Submission canceled. To resubmit type !release in #bot.**')

def submission_confirmation():
    pass

def submission_embed():
    pass

def valid_link(link):
    if (
        #steam workshop
        link.startswith('https://steamcommunity.com/sharedfiles/filedetails/?id=') 
        or link.startswith('https://www.steamcommunity.com/sharedfiles/filedetails/?id=')
        or link.startswith('www.steamcommunity.com/sharedfiles/filedetails/?id=') 
        or link.startswith('steamcommunity.com/sharedfiles/filedetails/?id=')
        or link.startswith('https://steamcommunity.com/workshop/') 
        or link.startswith('steamcommunity.com/workshop/') 
        or link.startswith('www.steamcommunity.com/workshop/')
        or link.startswith('https://www.steamcommunity.com/workshop/') 

        #tf2maps
        or link.startswith('https://tf2maps.net/downloads/')
        or link.startswith('https://tf2maps.net/threads/')

        #for testing
        or link.startswith('test')):
            return True
    else:
        return False