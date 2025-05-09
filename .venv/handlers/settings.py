from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters
from handlers.conv_chain import SETTINGS
from localization import get_translation

async def period_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('expired'):
        await update.message.reply_text("⏳ Session is over, because of inactivity(10 minutes). Enter /start to continue.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    if context.args:
        value = context.args[0]
        if value in ['1', '2', '3']:
            context.user_data['chosen_period'] = int(value)
            await update.message.reply_text(
                get_translation('period_updated',
                              context.user_data.get('language', context.user_data['language']),
                              value=value)
            )
        else:
            await update.message.reply_text(
                get_translation('period_range_error',
                              context.user_data.get('language', context.user_data['language']))
            )
    else:
        await update.message.reply_text(
            get_translation('period_usage',
                          context.user_data.get('language', context.user_data['language']))
        )
    return SETTINGS

async def good_mark_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('expired'):
        await update.message.reply_text("⏳ Session is over, because of inactivity(10 minutes). Enter /start to continue.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    if context.args:
        try:
            value = int(context.args[0])
            if 1 <= value <= 9:
                context.user_data['good_mark'] = value
                await update.message.reply_text(
                    get_translation('good_mark_updated',
                                    context.user_data.get('language', context.user_data['language']),
                                    value=value
                                    ))
            else:
                await update.message.reply_text(
                    get_translation('mark_range_error',
                                    context.user_data.get('language', context.user_data['language']))
                )
        except ValueError:
            await update.message.reply_text(
                get_translation('number_required',
                                context.user_data.get('language', context.user_data['language']))
            )
    else:
        await update.message.reply_text(
            get_translation('good_mark_usage',
                            context.user_data.get('language', context.user_data['language']))
        )
    return SETTINGS

async def good_percent_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('expired'):
        await update.message.reply_text("⏳ Session is over, because of inactivity(10 minutes). Enter /start to continue.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    if context.args:
        try:
            value = int(context.args[0])
            if 10 <= value <= 90:
                context.user_data['good_percent_mark'] = value
                await update.message.reply_text(
                    get_translation('good_percent_updated',
                                  context.user_data.get('language', 'en'),
                                  value=value
                    )
                )
            else:
                await update.message.reply_text(
                    get_translation('percent_range_error',
                                   context.user_data.get('language', 'en'))
                )
        except ValueError:
            await update.message.reply_text(
                get_translation('number_required',
                              context.user_data.get('language', 'en'))
            )
    else:
        await update.message.reply_text(
            get_translation('good_percent_usage',
                          context.user_data.get('language', 'en'))
        )
    return SETTINGS
async def absence_border(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('expired'):
        await update.message.reply_text("⏳ Session is over, because of inactivity(10 minutes). Enter /start to continue.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    if context.args:
        try:
            value = int(context.args[0])
            if 1 <= value <= 5:
                context.user_data['absence_border'] = value
                await update.message.reply_text(
                    get_translation('absence_updated',
                                  context.user_data.get('language', context.user_data['language']),
                                  value=value)
                )
            else:
                await update.message.reply_text(
                    get_translation('absence_range_error',
                                  context.user_data.get('language', context.user_data['language']))
                )
        except ValueError:
            await update.message.reply_text(
                get_translation('number_required',
                              context.user_data.get('language', context.user_data['language']))
            )
    else:
        await update.message.reply_text(
            get_translation('absence_usage',
                          context.user_data.get('language', context.user_data['language']))
        )
    return SETTINGS

async def set_other_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('expired'):
        await update.message.reply_text("⏳ Session is over, because of inactivity(10 minutes). Enter /start to continue.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    if context.args:
        value = context.args[0]
        if value in ['ru', 'en', 'lv']:
            context.user_data['language'] = value
            await update.message.reply_text(
                get_translation('language_updated',
                              context.user_data.get('language', context.user_data['language']),
                              value=value))
        else:
            await update.message.reply_text(
                get_translation('language_value_error',
                              context.user_data.get('language', context.user_data['language']))
            )
    else:
        await update.message.reply_text(
            get_translation('language_usage',
                          context.user_data.get('language', context.user_data['language']))
        )
    return SETTINGS

async def allow_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('expired'):
        await update.message.reply_text("⏳ Session is over, because of inactivity(10 minutes). Enter /start to continue.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    if context.args:
        try:
            value = int(context.args[0])
            if value in [0, 1]:
                context.user_data['allow_notifications'] = value
                notification_status = "notifications_enabled" if value == 1 else "notifications_disabled"

                await update.message.reply_text(get_translation(notification_status, context.user_data.get('language', 'en'), value=value))
            else:
                await update.message.reply_text(get_translation("invalid_value_error", context.user_data.get('language', 'en')))
        except ValueError:
            await update.message.reply_text(get_translation('number_range_error', context.user_data.get('language', 'en')))
    else:
        await update.message.reply_text(get_translation('value_required', context.user_data.get('language', 'en')))
    return SETTINGS

async def default(update: Update, context: ContextTypes.DEFAULT_TYPE, firstSetup = False) -> None:
    if (firstSetup):
        context.user_data.update({
            "logs": {
                'password': '',
                'username': ''
            },
            "language": '',
            "enter_success": False,
            "first_setup": True,
            "allow_notifications": False,
            "active_profile": "",
            'expired': False
        })
    else:
        await update.message.reply_text(get_translation('settings_reset_success', context.user_data.get('language', 'en')))
    context.user_data.update({
        "is_somewhere": False,
        "absence_border": 2,
        "chosen_period": 3,
        "good_mark": 4,
        "good_percent_mark": 50,
    })


