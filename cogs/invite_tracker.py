import datetime
import os

import nextcord
from nextcord.enums import DefaultAvatar
from nextcord.ext.commands.context import Context
from config import *
from nextcord.ext import commands

from ._functions import *


class InviteTracker(commands.Cog, name="Invite Tracker"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = Config("invite_tracker")

        try:
            os.mkdir("invite-logs")
        except:
            pass

        if "COUNTED_INVITES" not in self.config:
            self.config["COUNTED_INVITES"] = {}
            self.config.save()

        if "OLD_COUNTED_INVITES" not in self.config:
            self.config["OLD_COUNTED_INVITES"] = {}
            self.config.save()

    def cog_check(self, ctx: commands.Context):
        if ctx.guild:
            return ctx.author.guild_permissions.manage_roles
        else:
            return False

    async def make_leaderboard(self, ctx: commands.Context, invites_count: dict):
        fields = {}
        for id_str, amount in invites_count.items():
            try:
                fields[str(await ctx.guild.fetch_member(int(id_str)))] = amount
            except:
                pass

        temp = [(x, y) for x, y in fields.items()]
        fields = {
            key: val for key, val in sorted(temp, key=lambda x: x[1], reverse=True)
        }

        return fancy_embed("Invite Leaderboard", fields=fields)

    @property
    def invites_count(self):
        count = {}
        for _, data in self.config["COUNTED_INVITES"].items():
            if data["creator_id"] not in count:
                count[data["creator_id"]] = data["uses"]
            else:
                count[data["creator_id"]] += data["uses"]

        for _, data in self.config["OLD_COUNTED_INVITES"].items():
            if data["creator_id"] in count:
                count[data["creator_id"]] -= data["uses"]

        return count

    @property
    def previous_invites_count(self):
        if os.path.exists(f"invite-logs/{self.previous_week}.json"):
            with open(f"invite-logs/{self.previous_week}.json", "r") as f:
                return json.load(f)

    @property
    def this_week(self):
        now = datetime.datetime.now()
        return f"{now.isocalendar()[1]}-{now.year}"

    @property
    def previous_week(self):
        now = datetime.datetime.now() - datetime.timedelta(7)
        return f"{now.isocalendar()[1]}-{now.year}"

    @commands.command("leaderboard")
    async def show_leaderboard(self, ctx:commands.Context):
        embed = await self.make_leaderboard(ctx, self.invites_count)
        await ctx.reply(embed=embed)

    @commands.command("prev_leaderboard")
    async def show_prev_leaderboard(self, ctx:commands.Context):
        data = self.previous_invites_count
        if data:
            embed = await self.make_leaderboard(ctx, data)
            await ctx.reply(embed=embed)
        else:
            await ctx.reply("No leaderboard available.")

    @commands.Cog.listener()
    async def on_member_join(self, m: nextcord.Member):
        if not os.path.exists(f"invite-logs/{self.this_week}.json"):
            self.config["OLD_COUNTED_INVITES"].update(self.config["COUNTED_INVITES"])
            self.config.save()

        all_invites = await m.guild.invites()
        for inv in all_invites:
            if inv.code not in self.config["COUNTED_INVITES"]:
                self.config["COUNTED_INVITES"][inv.code] = {
                    "uses": inv.uses,
                    "creator_id": str(inv.inviter.id),
                }
            else:
                self.config["COUNTED_INVITES"][inv.code]["uses"] = inv.uses

        with open(f"invite-logs/{self.this_week}.json", "w+") as f:
            json.dump(self.invites_count, f)

        self.config.save()

    @commands.command("test")
    async def test(self, ctx:commands.Context):
        await self.on_member_join(ctx.author)


def setup(bot):
    bot.add_cog(InviteTracker(bot))
