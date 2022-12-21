# Tech Of The Day Discord Bot

This discord bot will pull from the TOTD Google Sheets document and notify the server it is in at a set time each workday who is TOTD.

To set this up, follow the discord join link obtained from Andg and add the Bot to your server.

### ENV Keys:

```
DISCORD_TOKEN:	The Bot's Access Token
CHANNEL_ID:	The channel ID you want it to send the message in.
ROLE_ID:	The role ID if you want it to ping a role every time it messages (Otherwise will just start with Good Morning)

XLSX_PATH:	The path to the locally downloaded spreadsheet if not connected to drive
GDRIVE_ID:	The file ID for for the spreadsheet in google drive

MESSAGE_TIME:	What time you want the bot to send the message (In %H:%M:%S format)
CURRENT_WEEK:	The current TOTD rotation week necessary for kickstarting the server
```

### Commands:

`!totd`: 

    Will print out the current TOTD with the backup randomly selected from the list of backups:

> *
>     "Good Morning: Todays TOTD is:**XX** with **YY** as Backup"*

    If a`ROLE_ID` is passed to the .env file then it will ping that role instead:

> *
>     "**@support**: Todays TOTD is: **XX** with **YY** as Backup"*

    This message will automatically run at a specified each day in a set channel based off of`CHANNEL_ID` and `MESSAGE_TIME` environment variables. (Default to 9 am local time)

`!set-week week_num`:

    This will set the TOTD week number in-case the bot gets out of sync or needs to be adjusted without having to change the env variable.


### Setup:

1. After cloning this repo run: `pip install -r requirements.txt`
2. Enable Developer Mode In Discord Settings > Advanced > Developer Mode which will allow you to get the Role and Channel IDs.
3. Right Click the choosen channel and Role to get their IDs and place them into the environment file.
4. After setting up the Discord side, the next step is how to obtain the file.
   1. If you are using the downloaded file just place the path to the file in `XLSX_PATH` and you are done. You can skip the rest of step 4.
   2. If you are using the Google Drive Path, you must first setup a Google Cloud Api account and project. This option is much harder to setup so I will write docs for it later in case anyone else needs it. But I recommend XLSX instead for simple use.
5. The next important step is specify what week the rotation is currently at. This will kick off the system and from here on out every Monday at 00:00:00 it will advance the week by one. Ideally there should be no need to change it from there but if need be there is always `!set-week`.
6. Finally, the last steps are to generate and invite link and invite the bot to your server.
7. To run the bot use `python TOTD.py`
