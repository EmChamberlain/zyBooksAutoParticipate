import time
import threading
import sys
import getopt

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

valueList = ['1048614','38','1048611','35','32']
phantomjs_path = 'phantomjs.exe'
chrome_path = "chromedriver.exe"
timetowait = 5


def findelementby(element, by, selector):
    try:
        return element.find_element(by, selector)
    except NoSuchElementException:
        return None


def getparentelement(element):
    try:
        return element.find_element_by_xpath('..')
    except NoSuchElementException:
        return None


def handlelistactivity(element, browser):
    choicecontainer = element.find_element_by_css_selector('div.term-bank')
    definitiontable = element.find_element_by_css_selector('table.definition-table')
    definitionrows = definitiontable.find_elements_by_css_selector('tr')
    choices = choicecontainer.find_elements_by_css_selector('li.unselected-term')
    for definitionrow in reversed(definitionrows):
        for choice in choices:
            td = definitionrow.find_element_by_css_selector('td.definition-row')
            ul = td.find_element_by_css_selector('ul.term-bucket')
            if 'term-correct' in td.get_attribute('class'):
                break
            ActionChains(browser).drag_and_drop(choice, ul).perform()
            li = td.find_element_by_css_selector('li')
            if 'term-correct' in li.get_attribute('class'):
                break
        choices = choicecontainer.find_elements_by_css_selector('li.unselected-term')


def handlestartactivity(element):
    startbutton = element.find_element_by_css_selector('div.startButton')
    startbutton.click()
    playbutton = element.find_element_by_css_selector('div.playButton')
    while playbutton.value_of_css_property('transform') == 'matrix(1, 0, 0, 1, 0, 0)':
        playbutton.click()
        time.sleep(1)


def handlequestionactivity(element):
    tablediv = element.find_element_by_css_selector('div.question-set')
    table = tablediv.find_element_by_css_selector('table')
    trs = table.find_elements_by_css_selector('tr')
    trs.pop(0)  # first row is the header with # | Question | Your answer
    for tr in trs:
        choices = tr.find_elements_by_css_selector('div.question-choice')
        for choice in choices:
            choice.click()
            if 'button-selected-correct' in choice.get_attribute("class"):
                break


def handlesimulateactivity(element):
    simulatebutton = element.find_element_by_css_selector('button.simulate')
    simulatebutton.click()


def main(argv):
    username = ''
    password = ''
    starturl = ''
    pathtodriver = ''
    try:
        opts, args = getopt.getopt(argv, "hu:p:s:d:", ["username=", "password=", "starturl=", "pathtodriver="])
    except getopt.GetoptError:
        print('test.py -u <username> -p <password> -s <starturl> optional: -d <pathtodriver>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('test.py -u <username> -p <password> -s <starturl> optional: -d <pathtodriver>')
            sys.exit()
        elif opt in ("-u", "--username"):
            username = arg
        elif opt in ("-p", "--password"):
            password = arg
        elif opt in ("-s", "--starturl"):
            starturl = arg
        elif opt in ("-d", "--pathtodriver"):
            pathtodriver = arg
        else:
            print('unknown option, pass -h for help')
            sys.exit(2)
    if username == '' or password == '' or starturl == '':
        print('test.py -u <username> -p <password> -s <starturl> optional: -d <pathtodriver>')
        sys.exit(2)

    if 'phantomjs.exe' in pathtodriver:
        browser = webdriver.PhantomJS(pathtodriver)
    elif 'chromedriver.exe' in pathtodriver:
        browser = webdriver.Chrome(pathtodriver)
    else:
        browser = webdriver.Firefox()

    browser.set_window_size(1400, 1000)
    wait = WebDriverWait(browser, 10)
    browser.get('https://zybooks.zyante.com/#/signin')

    usernamefield = browser.find_element_by_css_selector('input.ember-text-field')
    passwordfield = browser.find_element_by_css_selector('input.password-input')
    signinbutton = browser.find_element_by_css_selector('input.sign-in-button')
    usernamefield.send_keys(username)
    passwordfield.send_keys(password)
    signinbutton.click()

    browser.get(starturl)

    def quitthread():
        inputstr = 'not q'
        while inputstr != 'q':
            inputstr = input("Type 'q' to quit\n")
        print('*' + inputstr + '*')
        return
    t = threading.Thread(target=quitthread)
    t.start()

    # time.sleep(timetowait)
    while ('zybooks' in browser.current_url) and t.isAlive():
        try:
            browser.save_screenshot('out.png')
            completionelemlist = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.centered-activity div div div span'
                                                                    '.uncompleted-label')))
            elemlist = []
            for completionelem in completionelemlist:
                tempelem = completionelem.find_element_by_xpath('..')
                for i in range(0, 2):
                    tempelem = tempelem.find_element_by_xpath('..')
                elemlist.append(tempelem)

            for element in elemlist:
                browser.execute_script("return arguments[0].scrollIntoView();", element)  # may not need to do this
                if findelementby(element, By.CSS_SELECTOR, 'ul.sortable-container') is not None:
                    print("Handling a List activity")
                    handlelistactivity(element, browser)
                elif findelementby(element, By.CSS_SELECTOR, 'div.startButton') is not None:
                    print("Handling a Watch activity")
                    handlestartactivity(element)
                elif findelementby(element, By.CSS_SELECTOR, 'table th.content-resource-question') is not None:
                    print("Handling a Question activity")
                    handlequestionactivity(element)
                elif findelementby(element, By.CSS_SELECTOR, 'div.InstructionSetSimulator'):
                    print("Handling a Simulate activity")
                    handlesimulateactivity(element)
            print('Finished: ' + browser.current_url)
        except TimeoutException:
            print('Nothing to do on this page.')

        nextpagebutton = browser.find_element_by_css_selector('a div.navigation-button div.navigation-menu-arrow-down')
        nextpagebutton.click()
        # time.sleep(timetowait)

    print('Closing now!')
    file = open('last_url.txt', 'w')
    file.write(browser.current_url)
    file.close()
    browser.close()

if __name__ == "__main__":
    main(sys.argv[1:])
