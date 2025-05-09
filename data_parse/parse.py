from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
from bs4 import BeautifulSoup
from localization import get_translation
from datetime import date
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def init_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")  # Обязательно для Docker
    options.add_argument("--disable-dev-shm-usage")  # Избегаем проблем с памятью

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)  # Таймаут 30 секунд
    return driver
def getProfiles(username, password):
    driver = init_driver()
    profilesDict = {}

    driver.get("https://www.e-klase.lv/")
    wait = WebDriverWait(driver, 15)

    submitButton = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "button.btn-success[data-btn='submit']"))
    )
    # submitButton = driver.find_element(By.CSS_SELECTOR, "button.btn-success[data-btn='submit']")

    driver.execute_script(f"document.getElementsByName('UserName')[0].value = '{username}';")
    driver.execute_script(f"document.getElementsByName('Password')[0].value = '{password}';")
    driver.execute_script("arguments[0].click();", submitButton)

    time.sleep(1)

    driver.get('https://my.e-klase.lv/Family/UserLoginProfile')

    profilesContainer = wait.until(
        EC.presence_of_element_located((By.CLASS_NAME, 'modal-options'))
    )
    # profilesContainer = driver.find_element(By.CLASS_NAME, 'modal-options')
    all_small_elements = profilesContainer.find_elements(By.CSS_SELECTOR, '.modal-options-choice small')

    for i in range(1, len(all_small_elements)+1):
        profilesDict[i] = {
            'profileName': profilesContainer.find_elements(By.CLASS_NAME, 'modal-options-title')[i-1].text,
            'institution': profilesContainer.find_elements(By.CSS_SELECTOR, '.modal-options-choice small')[i-1].text
        }
    driver.quit()
    return profilesDict.copy()

def getUserPage(profileNumber, period, username, password):
    driver = init_driver()

    driver.get("https://www.e-klase.lv/")
    wait = WebDriverWait(driver, 15)


    submitButton = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "button.btn-success[data-btn='submit']"))
    )

    driver.execute_script(f"document.getElementsByName('UserName')[0].value = '{username}';")
    driver.execute_script(f"document.getElementsByName('Password')[0].value = '{password}';")
    driver.execute_script("arguments[0].click();", submitButton)

    time.sleep(1)

    driver.get('https://my.e-klase.lv/Family/UserLoginProfile')

    enterButtons = wait.until(
        EC.presence_of_all_elements_located((By.NAME, "pf_id"))
    )

    driver.execute_script("arguments[0].click();", enterButtons[profileNumber])

    time.sleep(1)

    today = date.today()
    formatted_date = today.strftime("%d.%m.%Y")

    if(today.month >= 1 and today.month <= 7):
        if(period == 1):
            driver.get(f"https://my.e-klase.lv/Family/ReportPupilMarks/Get?SelectedPeriod=01.09.2024.%2331.12.2024.&PeriodStart=03.05.2025.&PeriodEnd=03.05.2025.&IncludeWeightedAverages=true&IncludeNonAttendances=true&IncludePupilBehaviourRecords=true&DiscTypeObligatory=true&DiscTypeObligatory=false&DiscTypeInterest=true&DiscTypeInterest=false&DiscTypeFacultative=true&DiscTypeFacultative=false&DiscTypeExtendedDay=true&DiscTypeExtendedDay=false")
        elif(period == 2):
            driver.get(f"https://my.e-klase.lv/Family/ReportPupilMarks/Get?SelectedPeriod=01.01.2025.%23{formatted_date}.&PeriodStart=03.05.2025.&PeriodEnd=03.05.2025.&IncludeWeightedAverages=true&IncludeNonAttendances=true&IncludePupilBehaviourRecords=true&DiscTypeObligatory=true&DiscTypeObligatory=false&DiscTypeInterest=true&DiscTypeInterest=false&DiscTypeFacultative=true&DiscTypeFacultative=false&DiscTypeExtendedDay=true&DiscTypeExtendedDay=false")
        elif(period == 3): # Весь год
            driver.get("https://my.e-klase.lv/Family/ReportPupilMarks/Get")
    if(today.month <= 12 and today.month >= 9):
        driver.get("https://my.e-klase.lv/Family/ReportPupilMarks/Get")

    time.sleep(1)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()
    return soup

# profiles = getProfiles("070307-20802", "w6naudas")
#
# page = getUserPage(1, 3, "070307-20802", "w6naudas")

def getEachProfileInfo(profiles, lang = "en"):
    answer = ""
    for i in range(1, len(profiles)+1):
        answer += (
            f"👤 <b>{get_translation('profile', lang)} {i}:</b>\n"
            f"   ├ <i>{get_translation('name', lang)}:</i> {profiles[i]['profileName']}\n"
            f"   └ <i>{get_translation('additional_info', lang)}:</i> {profiles[i]['institution']}\n\n"
        )
    return answer

def getStudentInfo(userPage):
    infoDiv = userPage.find('div', {"class": "student-selector-option"})
    if infoDiv:
        studentName = infoDiv.find('span', {"class": "name"}).get_text()
        studentsInstitution = infoDiv.find('small').get_text()
    return [studentName, studentsInstitution]

def getFormattedStatistics(userPage):
    class Subject:
        def __init__(self, name, mainMarks=[], percentMarks=[], absences={}, nvCount=0, passes=0, notPasses = 0):
            self.name = name
            self.mainMarks = mainMarks
            self.percentMarks = percentMarks
            self.absences = absences
            self.passes = passes
            self.notPasses = notPasses
            self.nvCount = nvCount

        def getAverageMarks(self):
            if not self.mainMarks:  # Если список пуст
                return 0.0
            return round(sum(self.mainMarks) / len(self.mainMarks), 2)

        def getAveragePercentMarks(self):
            if not self.percentMarks:  # Если список пуст
                return 0.0
            return round(sum(self.percentMarks) / len(self.percentMarks), 2)
        def areThereAnyAbsences(self):
            if self.absences["n"] == 0 and self.absences["ns"] == 0 and self.absences["nc"] == 0:
                return False
            return True

    def find_all(a_str, sub):
        array = []
        start = 0
        while True:
            start = a_str.find(sub, start)
            if start > 0:
                array.append(start)
                start += len(sub)  # use start += 1 to find overlapping matches
            else:
                return array
    # initial values
    subjects = []
    mainMarks = []
    percentMarks = []
    absenceDict = {
        "n": 0,
        "ns": 0,
        "nc": 0,
    }
    nvCount = 0
    subPasses = 0
    notPasses = 0
    # initial values
    table = userPage.find('tbody', {'data-bind': 'foreach: marks'})
    if table:
        for tr in table.find_all('tr'):
            cells = tr.find_all('td')

            row_data = [td.get_text(strip=True) for td in cells]
            for elIndex, el in enumerate(row_data):
                mainMarksIndex = find_all(el, '(p.d.)')
                percentMarksIndex = find_all(el, '%')

                if (elIndex != 0):
                    for i in range(1, len(el)):
                        if(el[i] == 'i' and el[i-1] != 'n'):
                            subPasses += 1
                    for i in range(0, len(el)):
                        if(el[i] == 'n' and i != len(el)-1):
                            if(el[i+1] == "s"):
                                absenceDict["ns"] += 1
                            elif(el[i+1] == "c"):
                                absenceDict["nc"] += 1
                            elif(el[i+1] == "v"):
                                nvCount += 1
                            elif(el[i+1] == "i"):
                                notPasses += 1
                            else:
                                absenceDict["n"] += 1
                        elif(el[i] == 'n' and i == len(el)):
                            absenceDict["n"] += 1

                    for i in percentMarksIndex:
                        k = i - 1
                        start = i - 1
                        while el[k].isnumeric() or el[k] == ",":
                            k -= 1
                        end = k
                        percentMark = el[end+1:start+1]
                        percentMark = percentMark.replace(',', '.')
                        percentMarks.append(float(percentMark))
                    for i in mainMarksIndex:
                        k = i - 1
                        start = i - 1
                        value = el[k]
                        while el[k].isnumeric():
                            k-=1
                        if start - k == 1:
                            mainMarks.append(int(el[i - 1]))
                        elif start - k == 2:
                            mainMarks.append(int(el[i - 2] + el[i - 1]))
            subjects.append(Subject(row_data[0], mainMarks.copy(), percentMarks.copy(), absenceDict.copy(), nvCount, subPasses, notPasses))

            nvCount = 0
            subPasses = 0
            notPasses = 0
            absenceDict["n"] = 0
            absenceDict["ns"] = 0
            absenceDict["nc"] = 0
            mainMarks = []
            percentMarks = []
    return subjects

# statistics = getFormattedStatistics(page)

def getMainMarksStatistics(stats, lang = "en", goodMarkBorder = 5):
    answer = ''
    for subject in stats:
        if(subject.mainMarks):
            value = subject.getAverageMarks()
            answer += (
                f'📚 {get_translation("grades_for", lang)} <b>{subject.name}</b>: {", ".join(map(str, subject.mainMarks))}\n'
                f'⭐ {get_translation("average_grade", lang)}: <b>{value:.2f}</b> {"✅" if value >= goodMarkBorder else "❌"}\n\n')
    return answer

def getPercentsStatistics(stats, lang = "en", goodPercentBorder = 50):
    answer = ''
    for subject in stats:
        value = subject.getAveragePercentMarks()
        if (subject.percentMarks):
            answer += (
                f'📝 {get_translation("percentage_works_for", lang)} <b>{subject.name}</b>: {", ".join(f"{x}%" for x in subject.percentMarks)}\n'
                f'📊 {get_translation("average_percentage", lang)}: <b>{value:.2f}%</b> {"✅" if value >= goodPercentBorder else "❌"}\n\n')
    return answer

def getAbsenceStatistics(stats, lang = "en", absenceBorder = 2):
    answer = ''
    flag = True
    for subject in stats:
        if (subject.areThereAnyAbsences()):
            flag = False
        answer += (f'⏱️ {get_translation("absences_for", lang)} <b>{subject.name}</b>:\n'
                   f'{"✅" if subject.absences["n"] <= absenceBorder else "❌"} <i>n:</i> <b>{subject.absences["n"]}</b>'
                   f' || <i>ns:</i> <b>{subject.absences["ns"]}</b> || <i>nc:</i> <b>{subject.absences["nc"]}</b>\n\n')
    if flag:
        return get_translation('no_absences_achievement', lang)
    return answer

def getAverageMainScore(stats, dataOnly = False, lang = "en"):
    sum_marks = sum(stat.getAverageMarks() for stat in stats if stat.mainMarks)
    new_stats = [i for i in stats if i.mainMarks]
    avg = round(sum_marks / len(new_stats), 2) if new_stats else 0
    return avg if dataOnly else f"⭐ <i>{get_translation('overall_avg_grade', lang)}:</i> <b>{avg}</b>"

def getAveragePercentScore(stats, dataOnly = False, lang = "en"):
    sum_percents = sum(stat.getAveragePercentMarks() for stat in stats if stat.percentMarks)
    new_stats = [i for i in stats if i.percentMarks]
    avg = round(sum_percents / len(new_stats), 2) if new_stats else 0
    return avg if dataOnly else f"📈 <i>{get_translation('overall_avg_percentage', lang)}:</i> <b>{avg}%</b>"

def getNvStatistics(stats, lang = "en"):
    answer = ''
    has_nv = False
    for subject in stats:
        if subject.nvCount:
            has_nv = True
            answer += f"⚠️ {get_translation('nv_count_for', lang)} <b>{subject.name}</b>: {subject.nvCount}\n\n"
    return answer if has_nv else f"🎉 <b>{get_translation('no_nv', lang)}</b>"

def getPassesStatistics(stats, lang = "en"):
    answer = ''
    flag = True
    for subject in stats:
        if subject.passes or subject.notPasses:
            answer += (f"{get_translation('pass_fail_header', lang)} <b>{subject.name}</b>:\n"
                        f"✅<b>{get_translation('passed', lang)}</b>: {subject.passes}\n"
                        f"❌<b>{get_translation('failed', lang)}</b>: {subject.notPasses}\n\n")
            flag = False
    if flag:
        return False
    return answer

# print(getPassesStatistics(statistics))
