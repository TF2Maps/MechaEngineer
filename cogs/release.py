# Std Lib Imports
import sqlite3
from urllib.parse import urlparse, quote
from datetime import datetime, timedelta
import tempfile
import os

# 3rd Party Imports
from bs4 import BeautifulSoup
import discord
from discord.ext.commands import Cog, slash_command
import httpx
import databases
import tweepy

# Local Imports
from utils import load_config, cog_error_handler
from utils.discord import not_nobot_role_slash, roles_required
from utils.emojis import success, warning, error, info, loading
from utils.moderation import *
from utils.files import compress_file, download_file, get_download_filename, upload_to_gameserver, upload_to_redirect, remote_file_exists, redirect_file_exists, check_redirect_hash, dropbox_download, remote_file_size

global_config = load_config()
config = global_config.cogs.release
twitter_cfg = global_config.twitter

#
# Twitter integrations
#
consumer_key = twitter_cfg.consumer_key
consumer_secret = twitter_cfg.consumer_secret
access_token = twitter_cfg.access_token
access_token_secret = twitter_cfg.access_token_secret
bearer_token = twitter_cfg.bearer_token

apiv2 = tweepy.Client(
    bearer_token=bearer_token,
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    access_token=access_token,
    access_token_secret=access_token_secret
)

auth = tweepy.OAuth1UserHandler(
   consumer_key, consumer_secret,
   access_token, access_token_secret
)
api = tweepy.API(auth)


#the actual plugin
class Release(Cog):
    cog_command_error = cog_error_handler

    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        admin_channel = self.bot.get_channel(global_config.map_release_admin_channel_id)
        await admin_channel.send("The bot has restarted. All pending releases will need to be resubmitted.")
        bot_channel = self.bot.get_channel(global_config.bot_channel_id)
        await bot_channel.send("The bot has been restarted. Pending /release's will need to be resubmitted.")

        await self.db_pending_clear()

    @Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user):
        channel = reaction.message.channel
        approval_channel_id = global_config.map_release_admin_channel_id

        #only work in the channel
        if(channel.id == approval_channel_id):
            #how many votes required
            #so we stop spamming the db
            if(reaction.count > 4):
                return
            if(reaction.count > 3):
                #make sure it's actually the message
                if(reaction.message.content.startswith("Pending release!")):
                    #db info
                    database = databases.Database(global_config.databases.tf2maps_bot)
                    await database.connect()

                    #get embed information
                    embedMsg = reaction.message.embeds[0]
                    map_name = embedMsg.title
                    steam_link = embedMsg.fields[0].value
                    tf2maps_link = embedMsg.fields[1].value
                    map_author = embedMsg.fields[2].value

                    #channels
                    release_channel = self.bot.get_channel(global_config.map_release_channel_id)
                    forum_channel = self.bot.get_channel(global_config.map_release_forum_id)
                    admin_channel = self.bot.get_channel(global_config.map_release_admin_channel_id)

                    #emote info
                    discord_approval_emoji = "✅"
                    discord_disapproval_emoji = "❎"
                    
                    #not approved
                    if(str(reaction.emoji) == discord_disapproval_emoji):

                        #check if it's been approved already
                        query = "SELECT approved FROM releases WHERE steam_link = :steam_link AND tf2maps_link = :tf2maps_link AND approved = 'pending'"
                        values = {"steam_link": steam_link, "tf2maps_link": tf2maps_link}
                        result = await database.fetch_one(query=query, values=values)

                        #if it's pending do this
                        if result:
                            query = "UPDATE releases SET approved = 'declined', approved_time = :approved_time WHERE steam_link = :steam_link AND tf2maps_link = :tf2maps_link AND approved = 'pending'"
                            values = {"approved_time": datetime.now(), "steam_link": steam_link, "tf2maps_link": tf2maps_link}
                            result = await database.execute(query=query, values=values)

                            await admin_channel.send("Post has been declined.")
                            return
                        return

                    #approval
                    if(str(reaction.emoji) == discord_approval_emoji):

                        #check if it's been approved already
                        query = "SELECT approved FROM releases WHERE steam_link = :steam_link AND tf2maps_link = :tf2maps_link AND approved = 'pending'"
                        values = {"steam_link": steam_link, "tf2maps_link": tf2maps_link}
                        result = await database.fetch_one(query=query, values=values)

                        #if it's pending do this
                        if result:

                            #get discord image url
                            query = "SELECT discord_attachment_url FROM releases WHERE steam_link = :steam_link AND tf2maps_link = :tf2maps_link AND approved = 'pending'"
                            values = {"steam_link": steam_link, "tf2maps_link": tf2maps_link}
                            result = await database.fetch_one(query=query, values=values)                            
                            imgURL = result[0]

                            # we have to download the image... wtf
                            filepath = os.path.join(tempfile.mkdtemp(), "img.png")
                            await download_file(imgURL, filepath)

                            #create shitter post
                            tweetMessage = f"New map {map_name}, #released on the workshop! \nSteam: {steam_link} \nTF2Maps: {tf2maps_link}"
                            tweet_status = await self.tweet(filepath, tweetMessage)
                            twitter_url = f"https://twitter.com/tf2maps/{str(tweet_status.data['id'])}"

                            #post content to channels
                            #create thread
                            forum_tags = forum_channel.available_tags
                            workshopTag = None
                            mapTag = None
                            for tag in forum_tags:
                                if tag.name == "Map":
                                    mapTag = tag
                                if tag.name == "Workshop":
                                    workshopTag = tag                            

                            #get discord ID
                            query = "SELECT submitting_user_id FROM releases WHERE steam_link = :steam_link AND tf2maps_link = :tf2maps_link AND approved = 'pending'"
                            values = {"steam_link": steam_link, "tf2maps_link": tf2maps_link}
                            result = await database.fetch_one(query=query, values=values)

                            #check if thread was submitted
                            query = "SELECT map_forum_post_id FROM releases WHERE steam_link = :steam_link AND tf2maps_link = :tf2maps_link AND approved = 'pending'"
                            values = {"steam_link": steam_link, "tf2maps_link": tf2maps_link}
                            result = await database.fetch_one(query=query, values=values)
                            
                            #if no thread id submitted create thread
                            if result[0] == None:
                                thread = await forum_channel.create_thread(
                                    name=map_name,
                                    content=f"NEW MAP RELEASED!!! <@{result[0]}> \n {twitter_url}",
                                    embed=embedMsg,
                                    #these are a bitch to get
                                    applied_tags=[workshopTag, mapTag],
                                    slowmode_delay=0,
                                    reason="Approved map release"
                                )
                                created_thread = await thread.fetch_message(thread.id)
                            #if thread submitted
                            else:
                                created_thread = result[0]

                            #send in release channel
                            if result[0] == None:
                                map_release_message = await release_channel.send(f"A new map has been released! Discuss it here: <#{created_thread.id}>", embed=embedMsg)
                                thread_id = created_thread.id
                            else:
                                map_release_message = await release_channel.send(f"A new map has been released! Discuss it here: <#{result[0]}>", embed=embedMsg)
                                thread_id = result[0]
                            await map_release_message.publish()

                            query = "UPDATE releases SET approved = 'approved', approved_time = :approved_time, map_release_message_id = :map_release_message_id, map_forum_post_id = :map_forum_post_id, twitter_post_url= :twitter_post_url WHERE steam_link = :steam_link AND tf2maps_link = :tf2maps_link AND approved = 'pending'"
                            values = {"approved_time": datetime.now(), "steam_link": steam_link, "tf2maps_link": tf2maps_link, "map_release_message_id": map_release_message.id, "map_forum_post_id": thread_id, "twitter_post_url": twitter_url}
                            result = await database.execute(query=query, values=values)
                            return
                        return

    @slash_command(
        name="removereleaserecord", 
        description=config.removereleaserecord.help, 
        guild_ids=global_config.bot_guild_ids,
        checks=[
            roles_required(config.removereleaserecord.role_names),
            not_nobot_role_slash()
        ]
    )
    async def relremovereleaserecordase(self, ctx, steam_link, tf2maps_link):
        database = databases.Database(global_config.databases.tf2maps_bot)
        await database.connect()

        if not str(steam_link).startswith("https://steamcommunity.com/sharedfiles/filedetails/"):
            await ctx.respond(f"{error} `{steam_link}` is not a valid link.")
            return
        if not str(tf2maps_link).startswith("https://tf2maps.net/downloads/"):
            await ctx.respond(f"{error} `{tf2maps_link}` is not a valid link.")
            return

        query = "SELECT steam_link FROM releases WHERE steam_link = :steam_link"
        values = {"steam_link": steam_link}
        result = await database.fetch_one(query=query, values=values)
        if(result == None):
            await ctx.respond(f"{error} Cannot find a map using that steam url.")
            return

        #tf2m link
        query = "SELECT tf2maps_link FROM releases WHERE tf2maps_link = :tf2maps_link"
        values = {"tf2maps_link": tf2maps_link}
        result = await database.fetch_one(query=query, values=values)
        if(result == None):
            await ctx.respond(f"{error} Cannot find a map using that tf2m url.")
            return
        
        query = "DELETE FROM releases WHERE steam_link = :steam_link AND tf2maps_link = :tf2maps_link"
        values = {"steam_link": steam_link, "tf2maps_link": tf2maps_link}
        result = await database.execute(query=query, values=values)

        await ctx.respond(f"{success} The record `{steam_link} {tf2maps_link}` has been dropped from the releases table.")

    @slash_command(
        name="release", 
        description=config.release.help, 
        guild_ids=global_config.bot_guild_ids,
        checks=[
            roles_required(config.release.role_names),
            not_nobot_role_slash()
        ]
    )
    async def release(
        self, 
        ctx, 
        steam_link, 
        tf2maps_link, 
        thumbnail: discord.Attachment,
        finished_work_thread: discord.Option(input_type=str, description='Supply the channel in # format using the discord modal. Example #mapthread.', required=False),
    ):
        
        #if they enter a thread
        if finished_work_thread is not None:
            if finished_work_thread.startswith("<#"):
                try:
                    finished_work_thread_id = int(finished_work_thread[2:-1])

                    #get channel
                    supplied_channel = self.bot.get_channel(finished_work_thread_id)
                    
                    #check if channel even exists
                    try:
                        #REAL CHANNEL
                        real_channel = supplied_channel.name
                    except AttributeError:
                        await ctx.respond(f"{error} That is not a valid thread. The bot recieved `{finished_work_thread}`.", ephemeral=True)
                        return

                except ValueError:
                    await ctx.respond(f"{error} That is not a valid thread. The bot recieved `{finished_work_thread}`.", ephemeral=True)
                    return
                
            else:
                await ctx.respond(f"{error} That is not a valid thread.", ephemeral=True)
                return

        #check if it's a valid image first
        image_type = thumbnail.content_type
        if image_type != "image/png" and image_type != "image/jpeg":
            await ctx.respond(f"{error} That is not a valid image. Supported image types are `.png` `.jpg`", ephemeral=True)
            return


        #db notes
        #id - pk int (not needed for sqlite)
        
        #steam_link - string
        #tf2maps_link - string
        #submitting_user_id - int
        #admin_message_id - int
        #map_release_message_id - int
        #map_forum_post_id - int
        #approved - pending, approved, declined
        #submission_time - datetime
        #approved_time - datetime
        """
        create table releases (id int not null auto_increment, steam_link varchar(255), tf2maps_link varchar(255), submitting_user_id BIGINT, admin_message_id BIGINT, map_release_message_id BIGINT, map_forum_post_id BIGINT, approved varchar(255), submission_time datetime, approved_time datetime, primary key(id))
        """

        #db
        database = databases.Database(global_config.databases.tf2maps_bot)
        await database.connect()

        #check when user last posted a release
        user_id = ctx.author.id
        present = datetime.now()
        query = "SELECT submission_time FROM releases WHERE submitting_user_id = :user_id"
        values = {"user_id": user_id}
        result = await database.fetch_one(query=query, values=values)
        try:
            past = result[0]
            NUMBER_OF_SECONDS = 86400 # seconds in 24 hours
            if not (present - past).total_seconds() > NUMBER_OF_SECONDS:
                await ctx.respond(f"{warning} It's been less than a day since you've submitted a map for release. Please wait for a day to pass to prevent the system being flooded. Thank you.", ephemeral=True)
                return
        except:
            #there is no past!
            pass
        
        admin_channel = self.bot.get_channel(global_config.map_release_admin_channel_id)

        #search WS for map name
        ws_name = await self.get_ws_name(steam_link)
        if ws_name is None:
            await ctx.respond(f"{error} No valid Steam Workshop link was submitted.", ephemeral=True)
            return

        #workshop gamemode
        ws_gamemode = await self.get_ws_gamemode(steam_link)

        #get tf2maps author
        tf2m_username = await self.get_tf2m_name(tf2maps_link)
        if tf2m_username is None:
            await ctx.respond(f"{error} cannot find tf2m username. Make sure you've supplied a tf2maps.net download link!", ephemeral=True)
            return

        #check to see if map links have been submitted before and accepted
        #steam link
        query = "SELECT steam_link FROM releases WHERE steam_link = :steam_link AND approved IN ('approved', 'pending')"
        values = {"steam_link": steam_link}
        result = await database.fetch_one(query=query, values=values)
        if(result != None):
            await ctx.respond(f"{warning} This has been submitted before. Contact staff if this is an error.")
            return

        #tf2m link
        query = "SELECT tf2maps_link FROM releases WHERE tf2maps_link = :tf2maps_link AND approved IN ('approved', 'pending')"
        values = {"tf2maps_link": tf2maps_link}
        result = await database.fetch_one(query=query, values=values)
        if(result != None):
            await ctx.respond(f"{warning} This has been submitted before. Contact staff if this is an error.")
            return

        #create embed
        embed = discord.Embed(title=f"{ws_name}", description=ws_gamemode, colour=discord.Colour.orange())
        embed.add_field(name=f"Steam Workshop:", value=f"{steam_link}", inline=False)
        embed.add_field(name=f"Tf2maps.net Link:", value=f"{tf2maps_link}", inline=False)
        embed.add_field(name=f"Author: ", value=f"{tf2m_username}", inline=False)
        embed.set_image(url=thumbnail)
        embed.set_footer(text=global_config.bot_footer)

        #send to admins
        #if no thread id
        if finished_work_thread is None:
            message = await admin_channel.send(f"Pending release! Submitted by {ctx.author.name}", embed=embed)
        #if thread id
        else:
            message = await admin_channel.send(f"Pending release! Submitted by {ctx.author.name}. \n**IMPORTANT:** Supplied thread <#{finished_work_thread_id}>. Make sure this is correct.", embed=embed)
        
        #add reactions
        await message.add_reaction("✅")
        await message.add_reaction("❎")

        #if thread no ID
        if finished_work_thread is None:
            query = "INSERT INTO releases (steam_link, tf2maps_link, submitting_user_id, admin_message_id, approved, submission_time, discord_attachment_url) VALUES (:steam_link, :tf2maps_link, :submitting_user_id, :admin_message_id, :approved, :submission_time, :discord_attachment_url)"
            values = {"steam_link": steam_link, "tf2maps_link": tf2maps_link, "submitting_user_id": ctx.author.id, "admin_message_id": message.id, "approved": "pending", "submission_time": datetime.now(), "discord_attachment_url": thumbnail.url}
            result = await database.execute(query=query, values=values)
        #if thread id
        else:
            query = "INSERT INTO releases (steam_link, tf2maps_link, submitting_user_id, admin_message_id, approved, submission_time, discord_attachment_url, map_forum_post_id) VALUES (:steam_link, :tf2maps_link, :submitting_user_id, :admin_message_id, :approved, :submission_time, :discord_attachment_url, :map_forum_post_id)"
            values = {"steam_link": steam_link, "tf2maps_link": tf2maps_link, "submitting_user_id": ctx.author.id, "admin_message_id": message.id, "approved": "pending", "submission_time": datetime.now(), "discord_attachment_url": thumbnail.url, "map_forum_post_id": finished_work_thread_id}
            result = await database.execute(query=query, values=values)

        #reply to use, sometimes it times out
        await ctx.respond(f"{success} The map has been submitted for release! Pending staff approval. Contact Us if it doesn't look right ASAP.", embed=embed, ephemeral=True)

    #tweeting
    @staticmethod
    async def tweet(image, message): #, reply):
    #posting to twitter
        media = api.media_upload(image)
        media_id = media.media_id
        message = message + " #TF2"

        item_tweet = apiv2.create_tweet(text=message, media_ids=[media_id])

        return item_tweet

    #for clearing all pending maps during a bot restart
    @staticmethod
    async def db_pending_clear():
        database = databases.Database(global_config.databases.tf2maps_bot)
        await database.connect()

        query = "DELETE FROM releases WHERE approved = 'pending'"
        result = await database.fetch_one(query=query)

        return

    @staticmethod
    async def get_ws_gamemode(link):
        parsed_url = urlparse(link)

        tags = None
        tagArr = []
        gamemode = None
        if str(link).startswith("https://steamcommunity.com/sharedfiles/filedetails/"):
            async with httpx.AsyncClient() as client:
                    response = await client.get(link, follow_redirects=True, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')

            #get them tags
            #thanks for the code emp
            tags = soup.find('div', class_= 'col_right')
            if(tags is None):
                tags = soup.find('div', class_= 'sidebar')
                #item_type = 'Collection'
                #isCollection = True

            for ptag in tags.find_all('div', class_='workshopTags'):
                # prints the p tag content
                tagArr.append(ptag.text)

            #steam does this weirdly so we have too as well
            for tagz in tagArr:
                if (tagz.startswith("Game Mode:")):
                    gamemode = ""
                    gamemode += tagz

        return gamemode

    @staticmethod
    async def get_ws_name(link):
        parsed_url = urlparse(link)

        name = None
        if str(link).startswith("https://steamcommunity.com/sharedfiles/filedetails/"):
            async with httpx.AsyncClient() as client:
                response = await client.get(link, follow_redirects=True, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            name = soup.select(".workshopItemTitle")[0].text

        return name
    
    @staticmethod
    async def get_tf2m_name(link):
        name = None
        if str(link).startswith("https://tf2maps.net/downloads/"):
            async with httpx.AsyncClient() as client:
                response = await client.get(link, follow_redirects=True, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            name = soup.select(".username")[0].text
        return name