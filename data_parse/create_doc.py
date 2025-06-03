from data_parse.parse import (
      getMainMarksStatistics,
      getAbsenceStatistics,
      getPercentsStatistics,
      getAverageMainScore,
      getAveragePercentScore,
      getNvStatistics,
      getPassesStatistics
)
from telegram._update import Update
from telegram.ext import ContextTypes, ConversationHandler

async def make_overall_stats_doc(update: Update, context: ContextTypes.DEFAULT_TYPE):
      try:
            stats = context.user_data.get('formatedDataArray')
            studentNameSurname = context.user_data.get('studentInfo')[0].replace(" ", "_")
            answer = (f"-----Main information-----\n"
            f"Student: {context.user_data.get('studentInfo')[0]}\n"
            f"Institution and grade: {context.user_data.get('studentInfo')[1]}\n\n"
            f"-----Criterias-----\n"
            f"GoodMarkBorder: {context.user_data.get('good_mark')}\n"
            f"GoodPercentBorder: {context.user_data.get('good_percent_mark')}\n"
            f"AbsenceBorder: {context.user_data.get('absence_border')}\n\n"
            f"-----Statistics-----\n")
            if getAverageMainScore(stats, dataOnly=True) != 0.0:
                  answer += (f"!!!{getAverageMainScore(stats, lang=context.user_data.get('language'), formatted=False)}\n"
                  f"{getMainMarksStatistics(stats, lang=context.user_data.get('language'), formatted=False)}\n")
            if getAveragePercentScore(stats, dataOnly=True) != 0.0:
                  answer += (f"!!!{getAveragePercentScore(stats, lang=context.user_data.get('language'), formatted=False)}\n"
                  f"{getPercentsStatistics(stats, lang=context.user_data.get('language'), formatted=False)}\n")
            if getPassesStatistics(stats):
                  answer += f"{getPassesStatistics(stats, lang=context.user_data.get('language'), formatted=False)}\n"
            answer += (f"{getAbsenceStatistics(stats, lang=context.user_data.get('language'), formatted=False)}\n"
            f"{getNvStatistics(stats, lang=context.user_data.get('language'), formatted=False)}\n"
            f"-----End-----")
            with open(f"{studentNameSurname}_{update.effective_user.id}.txt", 'w', newline='', encoding='utf-8') as file:
                  file.write(answer)

      except Exception as e:
            await update.message.reply_text(f"❌ An error occured: {str(e)}.")
            return ConversationHandler.END

