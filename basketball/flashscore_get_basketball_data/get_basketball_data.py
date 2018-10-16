from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

#from lxml import html

from bs4 import BeautifulSoup

import re
import datetime, time, os

import pandas as pd

run_time = time.time()

#create dataframes for tables


options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument('--ignore-ssl-errors')
options.add_argument('disable-dev-shm-usage')
options.add_argument('no-sandbox')



def get_basketball_tournaments():
    
    basketball_tournaments = pd.DataFrame(columns=['country', 'tournament', 'link'])
    url = 'https://www.flashscore.com/basketball/'
    driver = webdriver.Chrome(chrome_options = options)
    driver.implicitly_wait(40)
    driver.get(url)
    
    WebDriverWait(driver, 40).until(EC.invisibility_of_element_located((By.ID, "preload")))
    
    #раскрываем список стран
    driver.execute_script("cjs.dic.get('Helper_Tab').showMoreMenu('.tournament-menu');")
    WebDriverWait(driver, 40).until(EC.invisibility_of_element_located((By.CLASS_NAME, "mbox0px hidden-content")))
    
    #для каждой страны раскрываем список с ее турнирами
    for country in BeautifulSoup(driver.page_source, "html.parser").find_all('li', {'id': re.compile('^lmenu_')}):
        driver.execute_script("cjs.dic.get('Helper_Menu').lmenu(" + country.get('id')[6:] + ",req_url,1);")
      
        if country.find('ul', {'class': "submenu  hidden"}) is None:
            WebDriverWait(driver, 40).until(EC.visibility_of_element_located((By.XPATH, "//li[@id='" + country.get('id') + "']/ul[@class='submenu']")))
        else:    
            WebDriverWait(driver, 40).until(EC.invisibility_of_element_located((By.XPATH, "//li[@id='" + country.get('id') + "']/ul[@class='submenu hidden']")))
        
    for country in BeautifulSoup(driver.page_source, "html.parser").find_all('li', {'id': re.compile('^lmenu_')}):
        cntry = country.find('a').text
        for tour in country.find_all('li', {'class': True}):
            basketball_tournaments.loc[len(basketball_tournaments)] =  [cntry, tour.text,  tour.find('a').get('href')]
            
            
    basketball_tournaments.to_csv('basketball_tournaments.csv', sep = ';')            
    driver.close()
    
    return basketball_tournaments

def get_basketball_tournaments_hist(trnm):
    basketball_tournaments_hist = pd.DataFrame(columns=['country', 'tournament', 'link', 'tournament_hist', 'tournament_hist_link'])
    driver = webdriver.Chrome(chrome_options = options)
    driver.implicitly_wait(40)
    
    
    for i, link in enumerate(trnm['link'].values):
        
        print(i, ' ', len(trnm['link'].values))
        url = 'https://www.flashscore.com' + link + 'archive/'
        
        driver.get(url)    
        WebDriverWait(driver, 40).until(EC.visibility_of_element_located((By.ID, "tournament-page-archiv")))
        
        for link in BeautifulSoup(driver.page_source, "html.parser").find('div', {'id': 'tournament-page-archiv'}).find('tbody').find_all('tr'):
            basketball_tournaments_hist.loc[len(basketball_tournaments_hist)] =  [trnm.iloc[i]['country'], trnm.iloc[i]['tournament'], trnm.iloc[i]['link'], re.sub("^\s+|\s+$", "", link.text, flags=re.UNICODE), link.find('a').get('href')]
    
    basketball_tournaments_hist.to_csv('basketball_tournaments_hist.csv', sep = ';')            
    driver.close()
    
    return basketball_tournaments_hist

def get_match_links(trnm_hist, basketball_match_hist):
    

    
    driver = webdriver.Chrome(chrome_options = options)
    driver.implicitly_wait(10)   
    
    #to_dwnld = list(set(trnm_hist['tournament_hist_link'].tolist()) - set(basketball_match_hist['tournament_hist_link'].tolist()))    
    trnm_hist = trnm_hist.loc[~trnm_hist['tournament_hist_link'].isin(basketball_match_hist['tournament_hist_link'].values)]

    for i, link in enumerate(trnm_hist['tournament_hist_link'].values):
        
        print(i, ' ', len(trnm_hist['tournament_hist_link'].values), ' ', trnm_hist.iloc[i]['tournament_hist_link'])
        
        url = 'https://www.flashscore.com' + link + 'results/'
        
        
        try:
            driver.get(url)
            WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.ID, "preload")))
        except:
            driver.close()
            driver = webdriver.Chrome(chrome_options = options)
            driver.implicitly_wait(10) 
            continue
        
        fail = 0
        for cnt in range(0, 15):
            try:
                driver.execute_script("loadMoreGames();")
                WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.ID, "preload")))
            except:
                fail += 1
                driver.close()
                driver = webdriver.Chrome(chrome_options = options)
                driver.implicitly_wait(10)   
                continue
        
        if fail > 0:
            continue
        
        for mtch in BeautifulSoup(driver.page_source, "html.parser").find('div', {'id': 'fs-results'}).find_all('tr', {'id': re.compile('^g_3')}):
            basketball_match_hist.loc[len(basketball_match_hist)] =  [trnm_hist.iloc[i]['country'], trnm_hist.iloc[i]['tournament'], trnm_hist.iloc[i]['tournament_hist'], trnm_hist.iloc[i]['tournament_hist_link'], mtch.get('id')[4:]]
            
        if i % 10 == 0:
            basketball_match_hist.to_csv('basketball_match_hist.csv', sep = ';')
            
        if i % 40 == 0:
          driver.close()
          driver = webdriver.Chrome(chrome_options = options)
          driver.implicitly_wait(10) 
    
    basketball_match_hist.to_csv('basketball_match_hist.csv', sep = ';')
    driver.close()
    return basketball_match_hist

    
if os.path.exists('basketball_tournaments_hist.csv'):
    trnm_hist = pd.read_csv('basketball_tournaments_hist.csv', index_col=0, sep = ';')
elif os.path.exists('basketball_tournaments.csv'):
    trnm = pd.read_csv('basketball_tournaments.csv', index_col=0, sep = ';')
else:
    trnm = get_basketball_tournaments()   
    trnm_hist = get_basketball_tournaments_hist(trnm)
   
if os.path.exists('basketball_match_hist.csv'):
    basketball_match_hist = pd.read_csv('basketball_match_hist.csv', index_col=0, sep = ';') 
else:
    basketball_match_hist = pd.DataFrame(columns=['country', 'tournament', 'tournament_hist', 'tournament_hist_link', 'id_match'])    
    
basketball_match_hist = get_match_links(trnm_hist, basketball_match_hist)    
    

