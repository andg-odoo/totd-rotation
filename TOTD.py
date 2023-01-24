from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import discord
from discord.ext import commands
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
import asyncio
import random

from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL = int(os.getenv('CHANNEL_ID'))
ROLE = int(os.getenv("ROLE_ID")) if os.getenv('ROLE_ID') else None
PATH = os.getenv('XLSX_PATH')
GDRIVE_ID = os.getenv('GDRIVE_ID')
MESSAGE_TIME = os.getenv('MESSAGE_TIME')
CURRENT_WEEK = int(os.getenv('CURRENT_WEEK'))


class TOTD:
    def __init__(self, document: str, current_week: int):
        self.current_week = current_week - 1

        document = self._fetch_drive(document)
        self._build_schedule(document)

    def _fetch_drive(self, document_id: str, file_name: str = 'totd.xlsx') -> str:
        if os.getenv('GDRIVE_ID'):
            # If we have a Google Drive ID download the file using the credentials.json and store it locally to use instead of the other file.
            gauth = GoogleAuth()

            gauth.LocalWebserverAuth()
            drive = GoogleDrive(gauth)
            downloaded = drive.CreateFile({'id': document_id})
            # downloaded.FetchMetadata(fields='modifiedDate')
            downloaded.GetContentFile(
                file_name, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            document_id = file_name
        return document_id

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
        return datetime.today().strftime('%A')

    @property
    def totd(self):
        return self.schedule[self.current_week][self.date].upper()

    def __repr__(self):
        if self.date == 'Saturday' or self.date == 'Sunday':
            return 'No TOTD today it\'s a weekend!'
        return 'Todays TOTD is: **%s** with **%s** as Backup' % (self.totd, self.backup)

    @property
    def backup(self):
        return random.choice(self.backups).upper()


class TOTDBot(commands.Bot):
    def __init__(self, command_prefix, self_bot, **kwargs):
        intents = discord.Intents.all()
        super().__init__(command_prefix=command_prefix,
                         help_command=None, intents=intents, self_bot=self_bot)
        self.WHEN = kwargs.get('time', time(9, 0, 0, tzinfo=ZoneInfo('US/Pacific')))
        self.channel = self.get_channel(kwargs.get('channel'))
        self.role = kwargs.get('role')
        self.tracker = TOTD(kwargs.get('path'), kwargs.get('week'))
        self.add_commands()

    async def setup_hook(self) -> None:
        # Increment week monday at midnight
        self.loop.create_task(self.background_task(
            time(0), self.increment_week, lambda x: x.weekday() == 0))
        # Print TOTD at a specific time
        self.loop.create_task(self.background_task(
            self.WHEN, self.print_totd, lambda x: x.weekday() < 5))

    async def increment_week(self):
        await self.wait_until_ready()
        self.tracker.next_week()

    def __repr__(self):
        if self.role:
            totd_string = "<@&%d>: %s" % (self.role, self.tracker)
        else:
            totd_string = "Good Morning: %s" % (self.tracker)
        return totd_string

    async def print_totd(self):  # Fired every day
        await self.wait_until_ready()
        if self.channel:
            await self.channel.send(self)

    async def background_task(self, WHEN, task, cond):
        now = datetime.now().astimezone(ZoneInfo('US/Pacific'))
        # If we are past the time we want, wait until midnight
        if now.timetz() > WHEN:
            tomorrow = datetime.combine(
                now.date() + timedelta(days=1), time(0), ZoneInfo('US/Pacific'))
            seconds = (tomorrow - now).total_seconds()
            await asyncio.sleep(seconds)
        while True:
            # Sleep until specific time
            now = datetime.now().astimezone(ZoneInfo('US/Pacific'))
            target_time = datetime.combine(now.date(), WHEN, ZoneInfo('US/Pacific'))
            seconds_until_target = (target_time - now).total_seconds()
            await asyncio.sleep(seconds_until_target)
            # Check passed in condition before running task
            if cond(datetime.now().astimezone(ZoneInfo('US/Pacific'))):
                await task()
            # Sleep until midnight
            tomorrow = datetime.combine(
                now.date() + timedelta(days=1), time(0), ZoneInfo('US/Pacific'))
            seconds = (tomorrow - now).total_seconds()
            await asyncio.sleep(seconds)

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print(f'Sending next message at: {self.WHEN}')
        print('------')

    def add_commands(self):

        @self.command(hidden=True)
        async def totd(ctx):
            await ctx.send(self)

        @self.command(name='set-week', hidden=True)
        async def set_week(ctx, week_num):
            try:
                int_week = int(week_num)
                int_week -= 1 # decrement to 0 index internally
                if int_week >= 0 and int_week < 5:
                    self.tracker.current_week = int_week
                    await ctx.send("*It is now week:* **%s**" % (self.tracker.current_week + 1))
                else:
                    await ctx.send("**Error:** *Must be an int between 1 and 5 inclusive.*")
            except:
                await ctx.send("**Error:** *Must be an int between 1 and 5 inclusive.*")


message_time = datetime.strptime(MESSAGE_TIME, '%H:%M:%S').astimezone(ZoneInfo('US/Pacific')).timetz()
print(message_time)
bot = TOTDBot(command_prefix="!",
              self_bot=False,
              time=message_time,
              path=GDRIVE_ID,
              channel=CHANNEL,
              role=ROLE,
              week=CURRENT_WEEK)


async def main():
    await bot.start(TOKEN,)

if __name__ == "__main__":
    asyncio.run(main())
