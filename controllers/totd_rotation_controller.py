# -*- coding: utf-8 -*-
from odoo import http

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import pandas as pd

from datetime import datetime
import random

from dotenv import load_dotenv
import os

load_dotenv()
GDRIVE_ID = os.getenv('GDRIVE_ID')
CURRENT_WEEK = int(os.getenv('CURRENT_WEEK', 1))


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


class totdRotationController(http.Controller):
    @http.route("/totd", type="http", auth="public", website=True)
    def books(self, **kwargs):
        # checked_out_books = (
        #     http.request.env["library.rental"].search([]).rented_books_ids
        # )
        # available_books = http.request.env["library.copies"].search(
        #     [("id", "not in", checked_out_books.ids)]
        # )
        totd = TOTD(GDRIVE_ID, CURRENT_WEEK)
        return http.request.render(
            "library_management.books_website",
            {"totd": totd},
        )