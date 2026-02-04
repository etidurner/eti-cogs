from .linkreplace import LinkReplace


async def setup(bot):
    await bot.add_cog(LinkReplace(bot))
