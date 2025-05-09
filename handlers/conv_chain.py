from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    BotCommand,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
    CallbackQueryHandler,
    CallbackContext,
    JobQueue
)
import asyncio
from data_parse.parse import getProfiles, getUserPage, getStudentInfo, getEachProfileInfo, getFormattedStatistics
from handlers.analysis_commands import handle_button_click
from localization import get_translation
from handlers.analysis_commands import get_stats_keyboard

start_commands = [
    BotCommand("start", "Start conversation"),
    # BotCommand("help", "FAQ"),
    BotCommand( 'cancel', 'Exit conversation')
]

# def commandAppend(commands, name, commandText):
#     if BotCommand(name, commandText) not in commands:
#         commands.append(BotCommand(name, commandText))
#     return commands
# def commandRemove(commands, name, commandText):
#     if BotCommand(name, commandText) in commands:
#         commands.remove(BotCommand(name, commandText))
#     return commands

LANGUAGE, START, SETTINGS, CHOICE, AUTO, USERNAME, PASSWORD, DATA, REQUEST, MENU, END = range(11)
from handlers.settings import (
   good_mark_handler,
   good_percent_handler,
   period_handler,
   absence_border,
   set_other_language,
   default,
   allow_notifications
)
import datetime as dt
import logging

user_timeout_jobs = {}
async def timeout_callback(context: ContextTypes.DEFAULT_TYPE):
    """Вызывается при таймауте"""
    try:
        user_id = context.job.user_id
        context.user_data['expired'] = True
        if user_id in user_timeout_jobs:
            del user_timeout_jobs[user_id]
    except Exception as e:
        logging.error(f"Timeout error: {e}")

async def reset_timeout(update: Update, context: CallbackContext):
    """Сбрасывает таймер неактивности"""
    try:
        context.user_data['expired'] = False
        user_id = update.effective_user.id
        if user_id in user_timeout_jobs:
            user_timeout_jobs[user_id].schedule_removal()

        job = context.job_queue.run_once(
            callback=timeout_callback,
            when=dt.timedelta(minutes=10),
            user_id=user_id
        )

        user_timeout_jobs[user_id] = job
    except Exception as e:
        logging.error(f"Timeout error: {e}")

async def greetBlock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if (not context.user_data.get('first_setup')):
        await reset_timeout(update, context)
        await default(update, context, True)
        await update.message.reply_text("🌟 *Welcome to Your e-klase Assistant!* 🌟\n\n"
           "📊 I'll help you track and analyze your academic performance with powerful statistics\n"
           "✨ Features include:\n"
           "   • Grade analytics\n"
           "   • Attendance monitoring\n"
           "   • Progress visualization\n\n"
           "🌍 Please select your preferred language to continue:\n"
           "   [Choose below ↓]",
            parse_mode='Markdown', reply_markup=ReplyKeyboardMarkup([
            ["Русский", "Latviešu", "English"]
        ], one_time_keyboard=True, resize_keyboard=True))
        context.user_data["is_somewhere"] = True
        return LANGUAGE
    await reset_timeout(update, context)
    return await beginWork(update, context)

async def setLanguage(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text.strip()
    lang_map = {
        "Русский": 'ru',
        "Latviešu": 'lv',
        "English": 'en'
    }

    if choice not in lang_map:
        await update.message.reply_text("Please select a valid language option")
        return LANGUAGE  # Повторяем выбор языка

    context.user_data['language'] = lang_map[choice]
    await update.message.reply_text(
        get_translation('language_was_set', context.user_data['language']),
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    # Atbilde: "✅ Language successfully set!"

    # Явный переход в следующее состояние
    return await beginWork(update, context)

async def beginWork(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if context.user_data.get('expired'):
        await update.message.reply_text("⏳ Session is over, because of inactivity(10 minutes). Enter /start to continue.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    await update.message.reply_text(
        get_translation('greeting', context.user_data['language']), parse_mode="Markdown" ,
        reply_markup=ReplyKeyboardMarkup(
            [[get_translation('start_buttons', context.user_data['language']).get('start'),
             get_translation('start_buttons', context.user_data['language']).get('settings')]],
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )
    return CHOICE

async def getChoice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if context.user_data.get('expired'):
        await update.message.reply_text("⏳ Session is over, because of inactivity(10 minutes). Enter /start to continue.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    """Получаем персональный код"""
    choice = update.message.text
    if choice == get_translation('start_buttons', context.user_data['language']).get('start'):
        if(context.user_data['enter_success']):
            await update.message.reply_text(
            get_translation('enter_success', context.user_data['language']),
            reply_markup=ReplyKeyboardMarkup(
                [[get_translation('YesOrNo', context.user_data['language']).get('yes'),
                  get_translation('YesOrNo', context.user_data['language']).get('no')]],
                one_time_keyboard=True,
                resize_keyboard=True
            ))
            return AUTO
        await update.message.reply_text(get_translation('personal_code', context.user_data['language']), reply_markup=ReplyKeyboardRemove())
        return USERNAME
    elif choice == get_translation('start_buttons', context.user_data['language']).get('settings'):
        await update.message.reply_text(get_translation('settingsMessage', context.user_data['language']), parse_mode='Markdown', reply_markup=ReplyKeyboardRemove())
        return SETTINGS

async def getAutoChoice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if context.user_data.get('expired'):
        await update.message.reply_text("⏳ Session is over, because of inactivity(10 minutes). Enter /start to continue.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    choice = update.message.text
    if (choice == get_translation('YesOrNo', context.user_data['language']).get('yes')):
        await update.message.reply_text(get_translation('auto_enter', context.user_data['language']), reply_markup=ReplyKeyboardRemove())
        return await getCertainProfile(update, context)
    elif (choice == get_translation('YesOrNo', context.user_data['language']).get('no')):
        await update.message.reply_text(get_translation('personal_code', context.user_data['language']))
        return USERNAME

async def getUsername(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if context.user_data.get('expired'):
        await update.message.reply_text("⏳ Session is over, because of inactivity(10 minutes). Enter /start to continue.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    """Получаем персональный код"""
    context.user_data["logs"]["username"] = update.message.text
    await update.message.reply_text(get_translation('password', context.user_data['language']))
    return PASSWORD


async def getPassword(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if context.user_data.get('expired'):
        await update.message.reply_text("⏳ Session is over, because of inactivity(10 minutes). Enter /start to continue.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    """Получаем пароль"""
    context.user_data["logs"]["password"] = update.message.text
    await update.message.reply_text(get_translation('do_you_confirm', context.user_data['language']),
        reply_markup=ReplyKeyboardMarkup(
            [[get_translation('YesOrNo', context.user_data['language']).get('yes'),
                  get_translation('YesOrNo', context.user_data['language']).get('no')]],
            one_time_keyboard=True,
            resize_keyboard=True
        )
        )
    return DATA


async def getData(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if context.user_data.get('expired'):
        await update.message.reply_text("⏳ Session is over, because of inactivity(10 minutes). Enter /start to continue.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    """Делаем запрос на сервер"""
    answer = update.message.text
    if(answer == get_translation('YesOrNo', context.user_data['language']).get('yes')):
        await update.message.reply_text(get_translation('processing_request', context.user_data['language']))
        return await getCertainProfile(update, context)
    elif(answer == get_translation('YesOrNo', context.user_data['language']).get('no')):
        await update.message.reply_text(get_translation('refusement', context.user_data['language']), reply_markup=ReplyKeyboardRemove())
        await cancel(update, context)
        context.user_data["enter_success"] = False
        return ConversationHandler.END

## Я подтвердил свои данные, есть логин и пароль. Теперь надо сделать запрос и вывести найденные активные профили

async def getCertainProfile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if context.user_data.get('expired'):
        await update.message.reply_text("⏳ Session is over, because of inactivity(10 minutes). Enter /start to continue.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    # try:
    profiles = getProfiles(context.user_data['logs']['username'], context.user_data['logs']['password'])
    language = context.user_data.get('language', 'en')
    context.user_data['profiles'] = profiles

    # Создаем красивый текст с профилями
    profiles_text = f"{get_translation('available_profiles', language)}\n\n"
    profiles_text += getEachProfileInfo(profiles, language)
    #
    # Создаем клавиатуру с нумерованными кнопками
    profilesKeyboard = [[KeyboardButton(f"{get_translation('profile', language)} {i}")] for i in range(1, len(profiles) + 1)]
    profilesKeyboard.append([
        KeyboardButton(f"{get_translation('cancel', language)}")  # Кнопка отмены
    ])
    await update.message.reply_text(
        f"{get_translation('select_profile_prompt', language)}\n\n"
        f"{profiles_text}",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=profilesKeyboard,  # Явно указываем параметр keyboard
            resize_keyboard=True,
            one_time_keyboard=True
        ),
        parse_mode="HTML"
    )
    # except Exception as e:
    #     await update.message.reply_text(f"❌ An error occured: {str(e)}.")
    #     return ConversationHandler.END  # или верни нужное состояние
    return REQUEST


async def process_data_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    answer = update.message.text
    if answer == get_translation('cancel', context.user_data['language']):
        return await cancel(update, context)
    else:
        try:
            profileNumber = int(answer[-1])
        except ValueError:
            await update.message.reply_text(get_translation("enterValid", context.user_data['language']))
            return REQUEST

        # print(context.user_data['profiles'])

        if profileNumber in [i for i in range(1, len(context.user_data['profiles'])+1)]:
            context.user_data["activeProfile"] = profileNumber
            await update.message.reply_text(get_translation('data_request', context.user_data['language']),
                                            reply_markup=ReplyKeyboardRemove())
            await asyncio.sleep(1)  # Добавляем задержку
            try:
                # Вызов вашей Selenium-функции
                dataPage = getUserPage(int(profileNumber)-1, context.user_data['chosen_period'], context.user_data['logs']['username'], context.user_data['logs']['password'])
                context.user_data['studentInfo'] = getStudentInfo(dataPage)
                context.user_data['formatedDataArray'] = getFormattedStatistics(dataPage)
                # Формируем ответ
                response = (
                    get_translation('found_student', context.user_data['language'],
                        student_name=context.user_data['studentInfo'][0],
                        students_institution=context.user_data['studentInfo'][1]
                    )
                )
                context.user_data["enter_success"] = True

                await update.message.reply_text(response, reply_markup=get_stats_keyboard(context.user_data['language'], context.user_data['formatedDataArray']), parse_mode='Markdown')

                return MENU
            except Exception as e:
                context.user_data["enter_success"] = False
                await update.message.reply_text(f"❌ An error occured: {str(e)}.")
                return ConversationHandler.END
        else:
            await update.message.reply_text(get_translation("enterValid", context.user_data['language']))
            return REQUEST


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена диалога"""
    context.user_data['is_somewhere'] = False
    await update.message.reply_text(
        get_translation('cancel_message', context.user_data['language']),
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def setup_handlers(app: Application):
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', greetBlock)],
        states={
            LANGUAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, setLanguage)
            ],
            START: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, beginWork)
            ],
            CHOICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, getChoice)
            ],
            SETTINGS: [
                CommandHandler('period', period_handler),
                CommandHandler('goodMarkBorder', good_mark_handler),
                CommandHandler('goodPercentBorder', good_percent_handler),
                CommandHandler('absenceBorder', absence_border),
                CommandHandler('language', set_other_language),
                CommandHandler('default', default),
                CommandHandler('start', greetBlock),
                CommandHandler('allowNotifications', allow_notifications),
            ],
            AUTO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, getAutoChoice)
            ],
            USERNAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, getUsername)
            ],
            PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, getPassword)
            ],
            REQUEST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_data_request)
            ],
            DATA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, getData)
            ],
            MENU: [
                CallbackQueryHandler(handle_button_click)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)],

    )
    # Регистрируем обработчики
    app.add_handler(conv_handler)