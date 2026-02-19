from __future__ import annotations

import re
from typing import Dict, List, Optional
from urllib.parse import urlparse

import discord
from redbot.core import Config, commands

URL_REGEX = re.compile(
    r"(?P<url>(?:https?://)?[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?:/[^\s<>]*)?)",
    re.IGNORECASE,
)


def normalize_host(host: str) -> str:
    host = host.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def extract_host(url: str) -> Optional[str]:
    if url.startswith("http://") or url.startswith("https://"):
        parsed = urlparse(url)
    else:
        parsed = urlparse("https://" + url)
    if not parsed.netloc:
        return None
    return parsed.netloc


def replace_host(url: str, new_host: str) -> str:
    has_scheme = url.startswith("http://") or url.startswith("https://")
    parsed = urlparse(url if has_scheme else "https://" + url)

    path = parsed.path or ""
    query = f"?{parsed.query}" if parsed.query else ""
    fragment = f"#{parsed.fragment}" if parsed.fragment else ""

    if has_scheme:
        return f"{parsed.scheme}://{new_host}{path}{query}{fragment}"
    return f"{new_host}{path}{query}{fragment}"


class LinkReplace(commands.Cog):
    """Resend matched links with replaced domains."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=9134021511)
        self.config.register_guild(rules={}, channels=[])

    @commands.group(name="linkreplace", aliases=["lr"], invoke_without_command=True)
    @commands.guild_only()
    async def linkreplace(self, ctx: commands.Context):
        """Manage link replacement rules and channels."""
        await ctx.send_help()

    @linkreplace.group(name="rule", invoke_without_command=True)
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def rule(self, ctx: commands.Context):
        """Manage replacement rules."""
        await ctx.send_help()

    @rule.command(name="add")
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def rule_add(self, ctx: commands.Context, source: str, target: str):
        """Add a replacement rule.

        Example: [p]linkreplace rule add x.com xproxy.com
        """
        source_norm = normalize_host(source)
        target_norm = normalize_host(target)

        async with self.config.guild(ctx.guild).rules() as rules:
            rules[source_norm] = target_norm

        await ctx.send(f"Rule added: {source_norm} -> {target_norm}")

    @rule.command(name="remove")
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def rule_remove(self, ctx: commands.Context, source: str):
        """Remove a replacement rule."""
        source_norm = normalize_host(source)

        async with self.config.guild(ctx.guild).rules() as rules:
            if source_norm in rules:
                del rules[source_norm]
                await ctx.send(f"Rule removed: {source_norm}")
                return

        await ctx.send(f"No rule found for: {source_norm}")

    @rule.command(name="list")
    @commands.guild_only()
    async def rule_list(self, ctx: commands.Context):
        """List replacement rules."""
        rules: Dict[str, str] = await self.config.guild(ctx.guild).rules()
        if not rules:
            await ctx.send("No rules configured.")
            return

        lines = [f"{src} -> {dst}" for src, dst in rules.items()]
        await ctx.send("Rules:\n" + "\n".join(lines))

    @linkreplace.group(name="channel", invoke_without_command=True)
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def channel(self, ctx: commands.Context):
        """Manage channels where replacement is active."""
        await ctx.send_help()

    @channel.command(name="add")
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def channel_add(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
        """Add a channel to monitor.

        Defaults to the current channel if not provided.
        """
        target = channel or ctx.channel
        async with self.config.guild(ctx.guild).channels() as channels:
            if target.id not in channels:
                channels.append(target.id)
        await ctx.send(f"Channel added: {target.mention}")

    @channel.command(name="remove")
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def channel_remove(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
        """Remove a channel from monitoring."""
        target = channel or ctx.channel
        async with self.config.guild(ctx.guild).channels() as channels:
            if target.id in channels:
                channels.remove(target.id)
                await ctx.send(f"Channel removed: {target.mention}")
                return
        await ctx.send(f"Channel not configured: {target.mention}")

    @channel.command(name="list")
    @commands.guild_only()
    async def channel_list(self, ctx: commands.Context):
        """List monitored channels."""
        channel_ids: List[int] = await self.config.guild(ctx.guild).channels()
        if not channel_ids:
            await ctx.send("No channels configured.")
            return

        channels = [ctx.guild.get_channel(cid) for cid in channel_ids]
        lines = [ch.mention for ch in channels if ch is not None]
        await ctx.send("Channels:\n" + "\n".join(lines))

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild:
            return
        if message.author.bot:
            return
        if not message.content:
            return

        channel_ids: List[int] = await self.config.guild(message.guild).channels()
        if not channel_ids or message.channel.id not in channel_ids:
            return

        rules: Dict[str, str] = await self.config.guild(message.guild).rules()
        if not rules:
            return

        matches = URL_REGEX.findall(message.content)
        if not matches:
            return

        replaced_links: List[str] = []
        for url in matches:
            host = extract_host(url)
            if not host:
                continue

            host_norm = normalize_host(host)
            target_host = rules.get(host_norm)
            if not target_host:
                continue

            replaced_links.append(replace_host(url, target_host))

        if replaced_links:
            header = f"{message.author.mention} sent:\n"
            await message.channel.send(header + "\n".join(replaced_links))
