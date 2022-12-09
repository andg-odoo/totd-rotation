class TOTD:
    def __init__(self, document: str, current_week: int):
        self.current_week = current_week - 1
        self._build_schedule(document)


    def _build_schedule(self, document: str):
        BACKUPS = 'BACKUP(S):'
        import pandas as pd
        df = pd.read_excel(document,
                   sheet_name='TODChat Rotation', header=16, usecols="B:H")
        week_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

        self.schedule = [{day: "" for day in week_days}
                    for week in df.columns[:5]]

        self.backups = [name for name in df[BACKUPS].dropna()]

        for week in range(0, len(self.schedule)):
            weekly_schedule = df.transpose().iloc[week]
            for index, day in enumerate(self.schedule[week]):
                self.schedule[week][day] = weekly_schedule[index]

    def next_week(self):
        self.current_week = self.current_week + 1 if self.current_week != 4 else 0

    @property
    def date(self):
        from datetime import datetime
        return datetime.today().strftime('%A')

    @property
    def totd(self):
        return self.schedule[self.current_week][self.date].upper()

    def __repr__(self):
        return 'Todays TOTD is: **%s** with **%s** as Backup' % (self.totd, self.backup)

    @property
    def backup(self):
        import random
        return random.choice(self.backups).upper()

import os

from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL = int(os.getenv('CHANNEL_ID'))
ROLE = int(os.getenv("ROLE_ID"))
PATH = os.getenv('XLSX_PATH')
MESSAGE_TIME = os.getenv('MESSAGE_TIME')

import discord
from discord.ext import commands
from datetime import datetime, time, timedelta
import asyncio


class TOTDBot(commands.Bot):
    def __init__(self, message_time: time, path: str, channel: int, role: int, command_prefix, self_bot):
        intents = discord.Intents.all()
        super().__init__(command_prefix=command_prefix, help_command=None, intents=intents, self_bot=self_bot)
        self.WHEN = message_time
        self.channel = channel
        self.role = role
        self.tracker = TOTD(path, 4)
        self.add_commands()

    async def setup_hook(self) -> None:
        # Increment week monday at midnight
        self.loop.create_task(self.background_task(time(0), self.increment_week, lambda x: x.weekday() == 0))
        # Print TOTD at a specific time
        self.loop.create_task(self.background_task(self.WHEN, self.print_totd, lambda x: x.weekday() < 5))


    async def increment_week(self):
        await self.wait_until_ready()
        self.tracker.next_week()


    async def print_totd(self):  # Fired every day
        await self.wait_until_ready()
        channel = self.get_channel(self.channel)
        totd_string = "<@&%d>: %s" % (self.role, self.tracker)
        await channel.send(totd_string)

    async def background_task(self, WHEN, task, cond):
        now = datetime.now()
        # If we are past the time we want, wait until midnight
        if now.time() > WHEN:
            tomorrow = datetime.combine(now.date() + timedelta(days=1), time(0))
            seconds = (tomorrow - now).total_seconds()
            await asyncio.sleep(seconds)
        while True:
            # Sleep until specific time
            now = datetime.now()
            target_time = datetime.combine(now.date(), WHEN)
            seconds_until_target = (target_time - now).total_seconds()
            await asyncio.sleep(seconds_until_target)
            # Check passed in condition before running task
            if cond(now):
                await task()
            # Sleep until midnight
            tomorrow = datetime.combine(now.date() + timedelta(days=1), time(0))
            seconds = (tomorrow - now).total_seconds()
            await asyncio.sleep(seconds)

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    def add_commands(self):

        @self.command(hidden=True)
        async def totd(ctx):
            totd_string = "<@&%d>: %s" % (self.role, self.tracker)
            await ctx.send(totd_string)


message_time = datetime.strptime(MESSAGE_TIME, '%H::%M::%S').time()
bot = TOTDBot(message_time, path=PATH, channel=CHANNEL, role=ROLE, command_prefix="!", self_bot=False)

async def main():
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())