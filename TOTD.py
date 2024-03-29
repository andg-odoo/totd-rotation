from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import discord
from discord.ext import commands
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
import asyncio
import random
from itertools import zip_longest

from dotenv import load_dotenv
import os

import logging
# from systemd import journal
logger = logging.getLogger(__name__)
# logger.addHandler(journal.JournalHandler(SYSLOG_IDENTIFIER='custom_unit_name'))
logger.setLevel(logging.DEBUG)

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
        self.document_id = document
        document = self._fetch_drive(self.document_id)
        self._build_schedule(document)

    def refresh(self) -> None:
        file_name = self._fetch_drive(document_id=self.document_id)
        self._build_schedule(file_name)

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
        return self.schedule[self.current_week][self.date]

    def __repr__(self):
        logger.info(f"Today is {self.date} in week {self.current_week}")
        if self.date == 'Saturday' or self.date == 'Sunday':
            return 'No TOTD today it\'s a weekend!'
        return 'Todays TOTD is: ***%s*** with ***%s*** as Backup' % (self.totd, self.backup)

    @property
    def backup(self):
        day = datetime.today().weekday()
        backup_id = day % len(self.backups)
        return self.backups[backup_id]


def to_timezone(timestamp: time|datetime, zone=ZoneInfo('US/Pacific')):
    return timestamp.replace(tzinfo=zone)

class TOTDBot(commands.Bot):
    def __init__(self, command_prefix, self_bot, **kwargs):
        intents = discord.Intents.all()
        super().__init__(command_prefix=command_prefix,
                         help_command=None, intents=intents, self_bot=self_bot)
        self.WHEN = to_timezone(kwargs.get('time', time(9, 0, 0)))
        self.channel_id = kwargs.get('channel')
        self.role = kwargs.get('role')
        self.tracker = TOTD(kwargs.get('path'), kwargs.get('week'))
        self.add_commands()

    async def setup_hook(self) -> None:
        # Increment week monday at midnight
        self.loop.create_task(self.background_task(
            to_timezone(time(0)), self.increment_week, lambda x: x.weekday() == 0))
        # Print TOTD at a specific time
        self.loop.create_task(self.background_task(
            self.WHEN, self.print_totd, lambda x: x.weekday() < 5))
        
        #Create list of people Thursday morning for ticket review
        self.loop.create_task(self.background_task(
            self.WHEN, self.generate_popcorn, lambda x: x.weekday() == 3))

    async def increment_week(self):
        await self.wait_until_ready()
        self.tracker.next_week()

    def build_totd_string(self, ctx):
        logger.info(f"Today is {self.tracker.date} in week {self.tracker.current_week}")
        if self.tracker.date == 'Saturday' or self.tracker.date == 'Sunday':
            return 'No TOTD today it\'s a weekend!'
        totd_name = self.tracker.totd
        backup_name = self.tracker.backup
        totd_member, backup_member = None, None

        for member in ctx.guild.members:
            if f"({totd_name.lower()})" in member.name.lower():
                totd_member = member
            if f"({backup_name.lower()})" in member.name.lower():
                backup_member = member

        if totd_member:
            totd_name = totd_member.mention
        if backup_member:
            backup_name = backup_member.name
        return 'Good Morning: Todays TOTD is: ***%s*** with ***%s*** as Backup' % (totd_name, backup_name)

    async def print_totd(self):  # Fired every day
        await self.wait_until_ready()
        ctx = self.get_channel(self.channel_id)
        if ctx:
            logger.info(f"Sending message to {ctx}")
            await ctx.send(self.build_totd_string(ctx))
        else:
            logger.warning("No Channel Set, not sending message today")

    def build_table(self, names):
        longest = max(names, key=len)
        width = len(longest) + 3
        table = ''
        numbered_names = tuple(enumerate(names))
        offset = len(numbered_names[::2])
        for a, b in zip_longest(numbered_names[::2], numbered_names[1::2]):
            table += "\n{0:2} {1}{2:2} {3}".format(a[0]//2, a[1].ljust(width), b[0]//2 + offset if b else "", b[1] if b else "")
        return table

    async def generate_popcorn(self):
        await self.wait_until_ready()
        ctx = self.get_channel(self.channel_id)
        if ctx:
            logger.info(f"Generating present order to {ctx}")
            if role := ctx.guild.get_role(self.role):
                tech_members = role.members 
                tech_order = [memb.display_name for memb in tech_members if "(jam)" not in memb.display_name]
                random.shuffle(tech_order)

                message = "Today's Presenting Order is:\n```"
                message += self.build_table(tech_order)
                message += "\n```*Note that if you are in onboarding currently you don't have to present.*"

                await ctx.send(message)

    async def background_task(self, WHEN, task, cond):
        now = datetime.now(ZoneInfo('US/Pacific'))
        logger.info(f"It is now: {now.timetz()}, waiting until {WHEN}")
        # If we are past the time we want, wait until midnight
        if now.timetz() > WHEN:
            tomorrow = datetime.combine(now.date() + timedelta(days=1), time(0), ZoneInfo('US/Pacific'))
            seconds = (tomorrow - now).total_seconds()
            logger.info(f"I need to sleep {seconds} seconds until midnight")
            await asyncio.sleep(seconds)
        while True:
            # Sleep until specific time
            now = datetime.now(ZoneInfo('US/Pacific'))
            target_time = datetime.combine(now.date(), WHEN, ZoneInfo('US/Pacific'))
            logger.info(target_time)
            seconds_until_target = (target_time - now).total_seconds()
            logger.info(f"I need to sleep {seconds_until_target} seconds until {WHEN}")
            await asyncio.sleep(seconds_until_target)
            # Check passed in condition before running task
            logger.info("Inside: Done waiting, checking condition")
            now = datetime.now(ZoneInfo('US/Pacific'))
            if cond(now):
                logger.info(f"Performing task at: {now}")
                await task()
            # Sleep until midnight
            tomorrow = datetime.combine(now.date() + timedelta(days=1), time(0), ZoneInfo('US/Pacific'))
            seconds = (tomorrow - now).total_seconds()
            logger.info(f"Done with task, I need to sleep {seconds} seconds until midnight")
            await asyncio.sleep(seconds)

    async def on_ready(self):
        logger.info('Logged in as')
        logger.info(self.user.name)
        logger.info(self.user.id)
        logger.info(f'Sending next message at: {self.WHEN}')
        logger.info(f'It is currently {datetime.now(ZoneInfo("US/Pacific"))}')
        logger.info('------')

    def add_commands(self):

        @self.command(hidden=True)
        async def totd(ctx: commands.Context):
            await ctx.send(self.build_totd_string(ctx))

        @self.command(name='set-week', hidden=True)
        async def set_week(ctx: commands.Context, week_num: str):
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

        @self.command(name='fetch-totd', hidden=True)
        async def update_rotation(ctx: commands.Context):
            self.tracker.refresh()
            await ctx.send("Refreshed Rotation. Run !totd to get the new TOTD")

        # @self.command(name="thursday")
        # async def thursday(ctx: commands.Context):
        #     logger.info(f"Generating present order to {ctx}")
        #     if role := ctx.guild.get_role(self.role):
        #         tech_members = role.members 
        #         tech_order = [memb.display_name for memb in tech_members if "(jam)" not in memb.display_name]
        #         random.shuffle(tech_order)

        #         message = "Today's Presenting Order is:\n```"
        #         message += self.build_table(tech_order)
        #         message += "\n```*Note that if you are in onboarding currently you don't have to present.*"

        #         await ctx.send(message)

message_time = to_timezone(datetime.strptime(MESSAGE_TIME, '%H:%M:%S')).timetz()
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
