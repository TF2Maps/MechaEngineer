
class Fun(commands.Cog):

    @commands.command()
    @commands.has_any_role('Gold Stars', 'Server Mods', 'Staff')
    async def roll(self, ctx):
        await ctx.send(f":game_die: Rolled a {random.randint(1,6)}")

    @commands.command()
    @commands.has_any_role('Gold Stars', 'Server Mods', 'Staff')
    async def flip(self, ctx):
        await ctx.send(f":coin: {random.choice(['Heads','Tails'])}")

    @commands.command()
    @commands.cooldown(1, 300, commands.BucketType.user)
    @commands.has_any_role('Gold Stars', 'Server Mods', 'Staff')
    async def cat(self, ctx):
        async with httpx.AsyncClient() as client:
            resp = await client.get('https://api.thecatapi.com/v1/images/search')
            if resp.status_code != 200:
                return await ctx.send('No cat found :(')
            js = resp.json()
            await ctx.send(embed=discord.Embed(title='Random Cat').set_image(url=js[0]['url']))

    @commands.command()
    @commands.cooldown(1, 300, commands.BucketType.user)
    @commands.has_any_role('Gold Stars', 'Server Mods', 'Staff')
    async def inspire(self, ctx):
        async with httpx.AsyncClient() as client:
            resp = await client.get('https://inspirobot.me/api?generate=true')
            if resp.status_code != 200:
                return await ctx.send('Not today buddy')
            await ctx.send(embed=discord.Embed(title='Inspiration').set_image(url=resp.text))

    @commands.command()
    @commands.cooldown(1, 300, commands.BucketType.user)
    @commands.has_any_role('Gold Stars', 'Server Mods', 'Staff')
    async def dog(self, ctx):
        """Gives you a random dog."""
        async with httpx.AsyncClient() as client:
            resp = await client.get('https://random.dog/woof')
            if resp.status_code != 200:
                return await ctx.send('No dog found :(')

            filename = resp.text
            url = f'https://random.dog/{filename}'
            filesize = ctx.guild.filesize_limit if ctx.guild else 8388608
            if filename.endswith(('.mp4', '.webm')):
                async with ctx.typing():
                    other = await client.get(url)
                    if other.status_code != 200:
                        return await ctx.send('Could not download dog video :(')

                    if int(other.headers['Content-Length']) >= filesize:
                        return await ctx.send(f'Video was too big to upload... See it here: {url} instead.')

                    fp = io.BytesIO(await other.read())
                    await ctx.send(file=discord.File(fp, filename=filename))
            else:
                await ctx.send(embed=discord.Embed(title='Random Dog').set_image(url=url))
