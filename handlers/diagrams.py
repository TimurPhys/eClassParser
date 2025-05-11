from telegram import Update
from telegram.ext import ContextTypes
import matplotlib.pyplot as plt
from data_parse.parse import getAverageMainScore, getAveragePercentScore
from localization import get_translation

def build_plot(data, what, session_id, order = False, lang = 'en', good_mark = 4, good_percent_mark = 50):
    # what = "main_grades" или "percent_grades"
    avg_line = None
    def sortFunc(e):
        if what == "main_grades":
            return e.getAverageMarks()
        elif what == "percent_grades":
            return e.getAveragePercentMarks()
    data.sort(key=sortFunc, reverse=order)
    student_grades = []
    subjects = []
    colors = []

    for subject in data:
        if(what == "main_grades"):
            if(subject.mainMarks):
                avg_line = getAverageMainScore(data, True)
                subjects.append(subject.name)
                student_grades.append(subject.getAverageMarks())
                if(subject.getAverageMarks() >= good_mark):
                    colors.append('#acd87a')
                else:
                    colors.append('#e9caa1')
        elif(what == "percent_grades"):
            if (subject.percentMarks):
                avg_line = getAveragePercentScore(data, True)
                subjects.append(subject.name)
                student_grades.append(subject.getAveragePercentMarks())
                if (subject.getAveragePercentMarks() >= good_percent_mark):
                    colors.append('#acd87a')
                else:
                    colors.append('#e9caa1')



    for i, subject in enumerate(subjects):
        dividedName = subject.split()
        if len(dividedName) > 3:
            subjects[i] = (f"{' '.join(dividedName[0:2])} \n"
                       f"{' '.join(dividedName[2: len(dividedName)])}")

    # Настройки графика
    fig, ax = plt.subplots(figsize=(12, 6))

    y_pos = range(len(subjects))

    # Создаем массив с предметами, где
    ax.barh([ax + 0.4 for ax in y_pos], student_grades, color=colors, height=0.4)

    # Подписи значений
    for i, v in enumerate(student_grades):
        ax.text(v + 0.1, i + 0.4, str(v), va='center', fontsize=8)
    # Вертикальная линия среднего
    ax.axvline(avg_line, color='red', linestyle='--', linewidth=1)
    plt.annotate(f"{avg_line:.2f}{'%' if what == 'percent_grades' else ''} vid.",
                 xy=(avg_line, 0), xytext=(-ax.bbox.width * 0.02, -30),
                 textcoords='offset points',
                 ha='left', va='top', color='red')
    # Подписи и оформление
    ax.set_yticks([y + 0.2 for y in y_pos])
    ax.set_yticklabels(subjects)
    ax.set_xlim(0, 10 if what == "main_grades" else 100)
    ax.set_title(get_translation(
        'avg_subject_grades_title' if what == "main_grades" else 'avg_work_grades_percent_title',
        lang
    ))
    ax.legend()

    student_grades = []
    subjects = []
    colors = []
    avg_line = None
    plt.savefig(f"{what}_{session_id}")
    plt.close()