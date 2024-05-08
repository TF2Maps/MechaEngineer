# Std Lib Imports

# 3rd Party Imports
import discord
from discord.ext.commands import Cog, slash_command, user_command
import databases

# Local Imports
from utils import load_config, cog_error_handler
from utils.emojis import github
from utils.discord import not_nobot_role_slash, roles_required

global_config = load_config()
config = global_config.cogs.verification


class Verification(Cog):
    cog_command_error = cog_error_handler

    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        self.bot.add_view(MyView(self.bot))
        #for starting a new embed
        channel = self.bot.get_channel(global_config.verification_channel_id)
        #await channel.send(f"# RECOMMENDED WAY! \n Click the button to get verified after linking your discord and steam on the forums. <https://tf2maps.net>", view=MyView(self.bot))
        pass


    @user_command(
        name="verify", 
        description=config.verify.help, 
        guild_ids=global_config.bot_guild_ids,
        checks=[
            roles_required(config.verify.role_names),
            not_nobot_role_slash()
        ]
    )
    async def verify(self, ctx, member: discord.Member):
        unverified_role = discord.utils.get(ctx.guild.roles, name="Unverified")
        verified_role = discord.utils.get(ctx.guild.roles, name="Verified")

        #for if they have both! take away unverified.
        if unverified_role in member.roles and verified_role in member.roles:
            await member.remove_roles(unverified_role)
            await ctx.respond(f"{member.name} has both Unverified and Verified. Removing Unverified.", ephemeral=True)
            return
        
        #check if they have a verified role already
        if verified_role in member.roles and unverified_role not in member.roles:
            await ctx.respond(f"{member.name} is already Verified!", ephemeral=True)
            return

        if unverified_role in member.roles:
            await member.remove_roles(unverified_role)
        await member.add_roles(verified_role)
        await ctx.respond(f"{member.name} is Verified now.", ephemeral=True)

class MyView(discord.ui.View):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(timeout=None) # timeout of the view must be set to None

    @discord.ui.button(label="Verify Me!", custom_id="button-1", style=discord.ButtonStyle.primary)
    async def button_callback(self, button, interaction):
        
        database = databases.Database(global_config.databases.tf2maps_site)
        await database.connect()
        
        #reference discord ID for user
        query = "SELECT user_id FROM xf_user_connected_account WHERE provider_key = :field_value"
        values = {"field_value": interaction.user.id}
        discord_id = interaction.user.id
        result = await database.fetch_one(query=query, values=values)

        if(result != None):
            #get steam id
            forum_id = result[0]
            query = "SELECT provider_key FROM xf_user_connected_account WHERE provider = 'th_cap_steam' AND user_id = :user_id"
            values = {"user_id": forum_id}
            result = await database.fetch_one(query=query, values=values)
            #if steam id present
            if(result != None):
                steam_id = result[0].decode("utf-8")

                #roles
                unverified_role = discord.utils.get(interaction.guild.roles, name="Unverified")
                verified_role = discord.utils.get(interaction.guild.roles, name="Verified")

                if unverified_role in interaction.user.roles:
                    await interaction.user.remove_roles(unverified_role)
                await interaction.user.add_roles(verified_role)

                # send DM?
                await interaction.response.send_message("Welcome to TF2Maps! Check your DM for more info!", ephemeral=True)
                user = await interaction.client.fetch_user(interaction.user.id)
                try:
                    await user.send("Welcome to TF2Maps!")
                #if it errors our for some reason
                except:
                    pass

                #verification log
                channel = self.bot.get_channel(global_config.verification_log_channel_id)

                #embed
                embed = discord.Embed(description=f"")
                embed.set_author(name=f"Verification", icon_url="https://cdn.discordapp.com/emojis/829026378078224435.png?v=1")
                embed.add_field(name=f"TF2M Profile", value=f"https://tf2maps.net/members/{forum_id}", inline=False)
                embed.add_field(name=f"Steam Profile", value=f"https://steamcommunity.com/profiles/{steam_id}", inline=False)
                embed.add_field(name=f"Discord Profile", value=f"<@{discord_id}>", inline=False)
                embed.set_footer(text=global_config.bot_footer)
                await channel.send(embed=embed)

            else:
                await interaction.response.send_message("You do not have steam linked! https://tf2maps.net/account/connected-accounts/", ephemeral=True)
        else:
            await interaction.response.send_message("No forum account was found. Please check your connected accounts https://tf2maps.net/account/connected-accounts/", ephemeral=True)