from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import traceback
import time
from bs4 import BeautifulSoup
from localization import get_translation
from datetime import date
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import os
import json

def save_cookies(driver, user_id):
    cookies = driver.get_cookies()

    os.makedirs("cookies", exist_ok=True)
    with open(f"cookies/user_{user_id}.json", "w") as file:
        json.dump(cookies, file)

def load_cookies(user_id):
    cookie_file = f"cookies/user_{user_id}.json"

    if not os.path.exists(cookie_file):
        return False
    with open(cookie_file, "r") as f:
        return json.load(f)

def init_driver():
    chrome_path = "/usr/bin/google-chrome"
    chromedriver_path = "/usr/bin/chromedriver"

    # Настройки Chrome
    chrome_options = Options()
    chrome_options.binary_location = chrome_path  # Важно!
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")  # Обязательно для Linux без GUI
    chrome_options.add_argument("--disable-dev-shm-usage")  # Для ограниченной памяти
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

    # Инициализация драйвера
    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    # driver.set_page_load_timeout(30)  # Таймаут 30 секунд
    return driver

drivers = {}
twoFaAuthorizedUsers = {}
def getProfiles(username, password, session_id):
    profilesDict = {}
    driver = None
    if not drivers.get(session_id):
        driver = init_driver()
        drivers[session_id] = driver
    else:
        driver = drivers.get(session_id)
    try:
        if not twoFaAuthorizedUsers.get(session_id):
            driver.get("https://www.e-klase.lv") # Захожу на сайта е-класса
            cookies = load_cookies(session_id)
            if cookies:
                driver.delete_all_cookies()
                for cookie in cookies:
                    if not cookie['domain'].startswith('.'):
                        if 'e-klase.lv' in cookie['domain']:
                            cookie['domain'] = '.e-klase.lv'  # Универсальный для всех поддоменов
                        else:
                            print(f"Пропускаем cookie для чужого домена: {cookie['domain']}")
                            continue
                    try:
                        driver.add_cookie(cookie)
                    except Exception as e:
                        print(f"Ошибка при добавлении cookie {cookie.get('name')}: {str(e)}")
                driver.refresh()
            submitButton = driver.find_element(By.CSS_SELECTOR, "button.btn-success[data-btn='submit']") # Нахожу кнопку отправки логов

            driver.execute_script(f"document.getElementsByName('UserName')[0].value = '{username}';") # Нахожу поле ввода логина и ввожу туда логин
            driver.execute_script(f"document.getElementsByName('Password')[0].value = '{password}';") # Нахожу поле ввода пароль и ввожу туда пароль
            driver.execute_script("arguments[0].click();", submitButton) # Нажимаю на кнопку отправки логов

        time.sleep(2) # Жду пока прогрузится страница

        if (driver.current_url == "https://my.e-klase.lv/two-factor-auth/#/view?type=WebLogin"
                and not twoFaAuthorizedUsers.get(session_id)): # Если мы попали в окно двухфакторной аутентификации, то
            authButton = driver.find_element(By.XPATH,
                                             "//*[text()='Nosūtīt SMS ar kodu']")  # Находим кнопку авторизации
            driver.execute_script("arguments[0].click();", authButton)  # Кликаем по кпопке авторизации
            return False

        time.sleep(2) # Ждем 2 секунды, чтобы прогрузилась страничка

        driver.get('https://my.e-klase.lv/Family/UserLoginProfile')
        profilesContainer = driver.find_element(By.CLASS_NAME, 'modal-options')
        all_small_elements = profilesContainer.find_elements(By.CSS_SELECTOR, '.modal-options-choice small')

        for i in range(1, len(all_small_elements)+1):
            profilesDict[i] = {
                'profileName': profilesContainer.find_elements(By.CLASS_NAME, 'modal-options-title')[i-1].text,
                'institution': profilesContainer.find_elements(By.CSS_SELECTOR, '.modal-options-choice small')[i-1].text
            }
        twoFaAuthorizedUsers[session_id] = False
        return profilesDict.copy()

    except TimeoutException as e:
        print(f"⏳ TimeoutException: {str(e)}")
        traceback.print_exc()
        driver.quit()
        del drivers[session_id]
        return None

    except (NoSuchElementException, IndexError, WebDriverException) as e:
        print(f"❌ Ошибка при получении страницы пользователя: {e}")
        traceback.print_exc()
        driver.quit()
        del drivers[session_id]
        return None

def twoFactorAuth(code, session_id):
    driver = drivers.get(session_id)
    try:
        otp_input = driver.find_element(By.CSS_SELECTOR, ".OTPInput")  # Находим поле ввода кода
        otp_input.send_keys(code)  # Вводим полученный код

        driver.execute_script("""
            arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
            arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
        """, otp_input)  # Синтаксис для получения события, что значения введены, типа, чтобы кнопка стала активной
        time.sleep(1)  # Ждем 1 секунду

        sendButton = driver.find_element(By.XPATH, "//button[contains(., 'Apstiprināt')]")  # Ищем кнопку отправки кода
        sendButton.click()  # Отправляем код нажатием кнопки

        time.sleep(2)  # Ждем пока прогрузится страница
        print(driver.page_source)
        trustButton = driver.find_elements(By.XPATH,
                                           "//button[.//span[text()=' Uzticēties ierīcei un turpināt ']]")  # Ищем кнопку доверия источнику

        if trustButton:  # Проверяем нашлась ли кнопка
            print("Кнопка доверия источнику найдена!")
            trustButton[0].click()  # Нажимаем на кпопку

        twoFaAuthorizedUsers[session_id] = True
    except Exception as e:
        print(f"Incorrect entered code: {str(e)}")
        twoFaAuthorizedUsers[session_id] = False
        driver.quit()
        del drivers[session_id]
        return None
def getUserPage(profileNumber, period, session_id):
    driver = drivers.get(session_id)
    try:
        driver.get('https://my.e-klase.lv/Family/UserLoginProfile')
        enterButtons = driver.find_elements(By.NAME, "pf_id")

        if profileNumber >= len(enterButtons):
            raise IndexError("Incorrect profile number")

        driver.execute_script("arguments[0].click();", enterButtons[profileNumber])
        time.sleep(1)

        save_cookies(driver, session_id)
        today = date.today()
        formatted_date = today.strftime("%d.%m.%Y")

        if 1 <= today.month <= 7:
            if period == 1:
                driver.get(f"https://my.e-klase.lv/Family/ReportPupilMarks/Get?SelectedPeriod=01.09.2024.%2331.12.2024.&PeriodStart=03.05.2025.&PeriodEnd=03.05.2025.&IncludeWeightedAverages=true&IncludeNonAttendances=true&IncludePupilBehaviourRecords=true&DiscTypeObligatory=true&DiscTypeObligatory=false&DiscTypeInterest=true&DiscTypeInterest=false&DiscTypeFacultative=true&DiscTypeFacultative=false&DiscTypeExtendedDay=true&DiscTypeExtendedDay=false")
            elif period == 2:
                driver.get(f"https://my.e-klase.lv/Family/ReportPupilMarks/Get?SelectedPeriod=01.01.2025.%23{formatted_date}.&PeriodStart=03.05.2025.&PeriodEnd=03.05.2025.&IncludeWeightedAverages=true&IncludeNonAttendances=true&IncludePupilBehaviourRecords=true&DiscTypeObligatory=true&DiscTypeObligatory=false&DiscTypeInterest=true&DiscTypeInterest=false&DiscTypeFacultative=true&DiscTypeFacultative=false&DiscTypeExtendedDay=true&DiscTypeExtendedDay=false")
            elif period == 3:
                driver.get("https://my.e-klase.lv/Family/ReportPupilMarks/Get")
        elif 9 <= today.month <= 12:
            driver.get("https://my.e-klase.lv/Family/ReportPupilMarks/Get")

        time.sleep(1)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        return soup

    except TimeoutException as e:
        print(f"⏳ TimeoutException: {str(e)}")
        traceback.print_exc()
        driver.quit()
        del drivers[session_id]
        return None

    except (NoSuchElementException, IndexError, WebDriverException) as e:
        print(f"❌ Ошибка при получении страницы пользователя: {e}")
        traceback.print_exc()
        driver.quit()
        del drivers[session_id]
        return None
    # finally:
        # driver.close()

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
    studentName = None
    studentsInstitution = None
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

def getMainMarksStatistics(stats, lang = "en", goodMarkBorder = 5, formatted = True):
    answer = ''
    for subject in stats:
        if(subject.mainMarks):
            if formatted:
                value = subject.getAverageMarks()
                answer += (
                    f'📚 {get_translation("grades_for", lang)} <b>{subject.name}</b>: {", ".join(map(str, subject.mainMarks))}\n'
                    f'⭐ {get_translation("average_grade", lang)}: <b>{value:.2f}</b> {"✅" if value >= goodMarkBorder else "❌"}\n\n')
            else:
                value = subject.getAverageMarks()
                answer += (
                    f'{get_translation("grades_for", lang)} {subject.name}: {", ".join(map(str, subject.mainMarks))}\n'
                    f'{"✅" if value >= goodMarkBorder else "❌"} {get_translation("average_grade", lang)}: {value:.2f}\n')
    return answer

def getPercentsStatistics(stats, lang = "en", goodPercentBorder = 50, formatted = True):
    answer = ''
    for subject in stats:
        value = subject.getAveragePercentMarks()
        if (subject.percentMarks):
            if formatted:
                answer += (
                    f'📝 {get_translation("percentage_works_for", lang)} <b>{subject.name}</b>: {", ".join(f"{x}%" for x in subject.percentMarks)}\n'
                    f'📊 {get_translation("average_percentage", lang)}: <b>{value:.2f}%</b> {"✅" if value >= goodPercentBorder else "❌"}\n\n')
            else:
                answer += (
                    f'{get_translation("percentage_works_for", lang)} {subject.name}: \n'
                    f'{"✅" if value >= goodPercentBorder else "❌"} {get_translation("average_percentage", lang)}: {value:.2f}%\n')
    return answer

def getAbsenceStatistics(stats, lang = "en", absenceBorder = 2, formatted = True):
    answer = ''
    flag = True
    for subject in stats:
        if (subject.areThereAnyAbsences()):
            flag = False
        if formatted:
            answer += (f'⏱️ {get_translation("absences_for", lang)} <b>{subject.name}</b>:\n'
                       f'{"✅" if subject.absences["n"] <= absenceBorder else "❌"} <i>n:</i> <b>{subject.absences["n"]}</b>'
                       f' || <i>ns:</i> <b>{subject.absences["ns"]}</b> || <i>nc:</i> <b>{subject.absences["nc"]}</b>\n\n')
        else:
            answer += (f'---{get_translation("absences_for", lang)} {subject.name}:\n'
                       f'{"✅" if subject.absences["n"] <= absenceBorder else "❌"} n: {subject.absences["n"]}'
                       f' || ns: {subject.absences["ns"]} || nc: {subject.absences["nc"]}\n')
    if flag:
        return get_translation('no_absences_achievement', lang)
    return answer

def getAverageMainScore(stats, dataOnly = False, lang = "en", formatted = True):
    sum_marks = sum(stat.getAverageMarks() for stat in stats if stat.mainMarks)
    new_stats = [i for i in stats if i.mainMarks]
    avg = round(sum_marks / len(new_stats), 2) if new_stats else 0
    if formatted:
        return avg if dataOnly else f"⭐ <i>{get_translation('overall_avg_grade', lang)}:</i> <b>{avg}</b>"
    else:
        return f"{get_translation('overall_avg_grade', lang)}: {avg}"

def getAveragePercentScore(stats, dataOnly = False, lang = "en", formatted = True):
    sum_percents = sum(stat.getAveragePercentMarks() for stat in stats if stat.percentMarks)
    new_stats = [i for i in stats if i.percentMarks]
    avg = round(sum_percents / len(new_stats), 2) if new_stats else 0
    if formatted:
        return avg if dataOnly else f"📈 <i>{get_translation('overall_avg_percentage', lang)}:</i> <b>{avg}%</b>"
    else:
        return f"{get_translation('overall_avg_percentage', lang)}: {avg}%"

def getNvStatistics(stats, lang = "en", formatted = True):
    answer = ''
    has_nv = False
    for subject in stats:
        if subject.nvCount:
            has_nv = True
            if formatted:
                answer += f"⚠️ {get_translation('nv_count_for', lang)} <b>{subject.name}</b>: {subject.nvCount}\n\n"
            else:
                answer += f"{get_translation('nv_count_for', lang)} {subject.name}: {subject.nvCount}\n"
    return answer if has_nv else f"🎉 <b>{get_translation('no_nv', lang)}</b>"

def getPassesStatistics(stats, lang = "en", formatted = True):
    answer = ''
    flag = True
    for subject in stats:
        if subject.passes or subject.notPasses:
            flag = False
            if formatted:
                answer += (f"{get_translation('pass_fail_header', lang)} <b>{subject.name}</b>:\n"
                            f"✅<b>{get_translation('passed', lang)}</b>: {subject.passes}\n"
                            f"❌<b>{get_translation('failed', lang)}</b>: {subject.notPasses}\n\n")
            else:
                answer += (f"{get_translation('pass_fail_header', lang)} {subject.name}:\n"
                           f"✅{get_translation('passed', lang)}: {subject.passes}\n"
                           f"❌{get_translation('failed', lang)}: {subject.notPasses}\n")
    if flag:
        return False
    return answer

# print(getPassesStatistics(statistics))
