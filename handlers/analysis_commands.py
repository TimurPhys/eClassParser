from telegram._update import Update
from telegram._replykeyboardremove import ReplyKeyboardRemove
from telegram._inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram._inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from data_parse.parse import (getMainMarksStatistics,
                              getAbsenceStatistics,
                              getPercentsStatistics,
                              getAverageMainScore,
                              getAveragePercentScore,
                              getNvStatistics,
                              getPassesStatistics)
from handlers.diagrams import build_plot
from localization import get_translation
from data_parse.create_doc import make_overall_stats_doc
import os


def get_stats_keyboard(language: str = "en", dataArray: list = []) -> InlineKeyboardMarkup:
    keyboard = []

    # Создаем временные списки для кнопок
    avg_row = []
    stats_row = []
    attendance_row = []

    # Добавляем кнопки средних оценок (если есть данные)
    if getAverageMainScore(dataArray, dataOnly=True) != 0.0:
        avg_row.append(
            InlineKeyboardButton(
                get_translation('btn_avg_grade', language),
                callback_data="show_average_marks"
            )
        )
        stats_row.append(
            InlineKeyboardButton(
                get_translation('btn_grade_stats', language),
                callback_data="show_full_stats"
            )
        )

    # Добавляем кнопки процентных оценок (если есть данные)
    if getAveragePercentScore(dataArray, dataOnly=True) != 0.0:
        avg_row.append(
            InlineKeyboardButton(
                get_translation('btn_avg_percent', language),
                callback_data="show_average_percent_marks"
            )
        )
        stats_row.append(
            InlineKeyboardButton(
                get_translation('btn_percent_stats', language),
                callback_data="show_full_percent_stats"
            )
        )

    # Добавляем ряды только если они не пустые
    if avg_row:
        keyboard.append(avg_row)
    if stats_row:
        keyboard.append(stats_row)

    # Кнопки посещаемости
    attendance_row.append(
        InlineKeyboardButton(
            get_translation('btn_absences', language),
            callback_data="show_absences"
        )
    )
    if getPassesStatistics(dataArray):
        attendance_row.append(
            InlineKeyboardButton(
                get_translation('btn_passes', language),
                callback_data="show_passes"
            )
        )

    keyboard.append(attendance_row)

    # Кнопка отсутствующих оценок
    keyboard.append([
        InlineKeyboardButton(
            get_translation('btn_missing_grades', language),
            callback_data="show_nv"
        )
    ])
    keyboard.append([
        InlineKeyboardButton(
            get_translation("generate_txt", language),
            callback_data="make_txt_file"
        )
    ])

    return InlineKeyboardMarkup(keyboard)

async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('expired'):
        await update.message.reply_text("⏳ Session is over, because of inactivity(10 minutes). Enter /start to continue.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    query = update.callback_query
    await query.answer()

    data = context.user_data['formatedDataArray']
    language = context.user_data.get('language', 'en')
    callback = query.data

    if callback == 'show_average_marks':
        await update.callback_query.message.reply_text(getAverageMainScore(data,False, language), parse_mode='HTML')
    elif callback == 'show_average_percent_marks':
        await update.callback_query.message.reply_text(getAveragePercentScore(data,False, language), parse_mode='HTML')
    elif callback == 'show_absences':
        await update.callback_query.message.reply_text(getAbsenceStatistics(data, language, context.user_data.get('absence_border')), parse_mode='HTML')
    elif callback == 'show_full_stats':
        user_id = update.effective_user.id
        build_plot(data, 'main_grades', session_id=user_id, lang=language, good_mark=context.user_data.get('good_mark'))
        with open(f"main_grades_{user_id}.png", "rb") as chart:
            await update.callback_query.message.reply_photo(chart, caption=get_translation('your_grade_stats', language))
        os.remove(f"main_grades_{user_id}.png")
        await update.callback_query.message.reply_text(getMainMarksStatistics(data, language, context.user_data.get('good_mark')), parse_mode='HTML')
    elif callback == 'show_full_percent_stats':
        user_id = update.effective_user.id
        build_plot(data, "percent_grades", session_id=user_id, lang=language, good_percent_mark=context.user_data.get('good_percent_mark'))
        with open(f"percent_grades_{user_id}.png", "rb") as chart:
            await update.callback_query.message.reply_photo(chart, caption=get_translation('your_percent_stats', language))
        os.remove(f"percent_grades_{user_id}.png")
        await update.callback_query.message.reply_text(getPercentsStatistics(data, language, context.user_data.get('good_percent_mark')), parse_mode='HTML')
    elif callback == 'show_nv':
        await update.callback_query.message.reply_text(getNvStatistics(data, language), parse_mode='HTML')
    elif callback == 'show_passes':
        await update.callback_query.message.reply_text(getPassesStatistics(data, language), parse_mode='HTML')
    elif callback == "make_txt_file":
        studentNameSurname = context.user_data.get('studentInfo')[0].replace(" ", "_")
        await make_overall_stats_doc(update, context)
        with open(f"{studentNameSurname}_{update.effective_user.id}.txt", "rb") as file:
            await update.callback_query.message.reply_document(
                document=file,
                caption=get_translation("overall_file", language),
                filename=f"{studentNameSurname}_stats"
            )
        os.remove(f"{studentNameSurname}_{update.effective_user.id}.txt")
    await update.callback_query.message.reply_text(get_translation('what_else_to_show', context.user_data.get('language', 'en')),
                                                   reply_markup=get_stats_keyboard(language, context.user_data['formatedDataArray']))

    # return ConversationHandler.END