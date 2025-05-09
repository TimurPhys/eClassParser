import threading
import time
from telegram.ext import ContextTypes, Updater, Application
from data_parse.parse import getUserPage, getFormattedStatistics
import asyncio

async def request(app: Application, user_id, user_data):
    firstTime = True
    currentProfile = None
    stats = getFormattedStatistics(getUserPage(user_data['activeProfile'], user_data['chosen_period'], user_data['logs']['username'], user_data['logs']['password']))
    if not firstTime and currentProfile == user_data.get('activeProfile'):
        for i in range(0, len(stats)):
            differences = {}
            subject_updated = stats[i]
            subjects_old = user_data.get("stats")[i]
            for key in vars(subject_updated).keys():
                val1 = getaatr(subject_updated, key, None)
                val2 = getaatr(subjects_old, key, None)
                if val1 != val2:
                    differences[key] = (val1, val2)
                    print(differences)
    currentProfile = user_data.get('activeProfile')
    firstTime = False
    user_data["stats"] = stats

async def selenium_frequent_request(app: Application):
    while True:
        for user_id, user_data in app.user_data.items():
            notificationsAllowed = user_data.get('allow_notifications', False)
            isSomewhere = user_data.get("is_somewhere")
            enter_success = user_data.get("enter_success")
            if notificationsAllowed and not isSomewhere and enter_success:
                try:
                    await request(app, user_id, user_data)
                except Exception as e:
                    print(f"Произошла ошибка: {e}")
        await asyncio.sleep(10)