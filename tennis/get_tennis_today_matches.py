from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import re

#функция возвращает два массива
#matches_finished - идентификаторы матчей, завершившихся за последние 5 дней
#matches_forecast - идентификаторы матчей для прогноза

def get_last_matches():
    
    url = "https://www.flashscore.com/tennis/"
    
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument('--ignore-ssl-errors')
    options.add_argument('disable-dev-shm-usage')
    options.add_argument('no-sandbox')
        
    driver = webdriver.Chrome(chrome_options = options)
    driver.implicitly_wait(40)
    driver.get(url)
    
    matches_finished = []
    matches_forecast = []
    
    for dt in ['-5', '-4', '-3', '-2', '-1', '0', '1']:
            driver.execute_script('set_calendar_date(' + dt + ');')
            WebDriverWait(driver, 40).until(EC.invisibility_of_element_located((By.ID, "preload")))
    
            for tbl in BeautifulSoup(driver.page_source, "html.parser").find_all('table', {'class': 'tennis'}):
                lg = tbl.find('span', {'class': 'country_part'}).text
                
                #пропускаем парные матчи и юношеский теннис
                if lg.find('BOYS') >= 0 or lg.find('GIRLS') >= 0 or lg.find('DOUBLES') >= 0:
                    continue
                
                for mtch in tbl.find_all('tr', {'id': re.compile('^g_2')}):
                    #print(mtch.get('id')[4:], lg, mtch.find('td', {'class': 'cell_aa'}).text)
                    status = mtch.find('td', {'class': 'cell_aa'}).text
                    
                    if status.find('Cancelled') >= 0:
                        continue
                    elif re.sub(r"\s+", "", status, flags=re.UNICODE) == '':
                        matches_forecast.append(mtch.get('id')[4:])
                    elif status.find('Finished') >= 0:
                        matches_finished.append(mtch.get('id')[4:])
    driver.close()
    
    return matches_finished, matches_forecast
    
    

