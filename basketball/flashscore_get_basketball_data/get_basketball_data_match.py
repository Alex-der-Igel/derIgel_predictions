from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import re
import pandas as pd
from pathlib import Path 

dateparse = lambda x: pd.datetime.strptime(x, '%d.%m.%Y %H:%M')

def load_basketball_match_info(table, matches, match_stats):

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument('--ignore-ssl-errors')
    options.add_argument('disable-dev-shm-usage')
    options.add_argument('no-sandbox')
        
    driver = webdriver.Chrome(chrome_options = options)
    driver.implicitly_wait(20)
    
    game_home = []
    game_away = []
    
    for i, tab in enumerate(table):
        
            print(i, ' ', len(table))
            m_l = tab
            try_load = 0
            while True:
                try:
                    try_load += 1
                    driver.get('https://www.flashscore.com/match/' + m_l + '/#match-summary/')
                    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.ID, "tab-match-summary")))
                except:
                    
                    soup = BeautifulSoup(driver.page_source, "html.parser")
                    #print(try_load)
                    if soup.find('div', {'id': 'tab-match-summary'}) is None and try_load > 0:
                        break
                    
                    driver.close()
                    driver = webdriver.Chrome(chrome_options = options)
                    driver.implicitly_wait(20)
                    continue
                break
            
                   
            soup = BeautifulSoup(driver.page_source, "html.parser")   
            if soup.find('div', {'id': 'tab-match-summary'}) is None:
                continue
            
            if soup.find('div', {'class': 'info-status mstat'}).text in ['Walkover' ,'Abandoned'] or soup.find('div', {'class': 'nodata-block'}) is not None:
                continue
            elif soup.find('div', {'class': 'info-status mstat'}).text != 'Finished':
                match_status = soup.find('div', {'class': 'info-status mstat'}).text
            else:
                match_status = None
            
            if soup.find('div', {'class': 'info-bubble'}) is not None:
                match_note = soup.find('div', {'class': 'info-bubble'}).find('span', {'class': 'text'}).text
            else:
                match_note = None
                    
            m_t = dateparse(soup.find('div', {'class': 'info-time mstat-date'}).text)
             
            summ = soup.find('div', {'id':'summary-content'})
            
            
            sum_home = summ.find('tr', {'class': 'odd'})
            set_home = 0
            for scor in sum_home.find_all('td', {'class': re.compile('^score')}):
                if scor.get('class') == ['score']:
                    if scor.find('strong') is not None: 
                        if scor.find('strong').text != '':
                            set_home = int(scor.find('strong').text)
                        
                elif scor.find('span') is not None:
                    game_home.append(int(scor.find('span').text))
            
            if len(game_home) == 0:
                game_home.append(set_home)
                    
            sum_away = summ.find('tr', {'class': 'even'})
            set_away = 0
            for scor in sum_away.find_all('td', {'class': re.compile('^score')}):
                if scor.get('class') == ['score']:
                    if scor.find('strong') is not None:
                        if scor.find('strong').text != '':
                            set_away = int(scor.find('strong').text)
                        
                elif scor.find('span') is not None:
                    game_away.append(int(scor.find('span').text))
           
            if len(game_away) == 0:
                game_away.append(set_away)
            
            tour = soup.find('div', {'class': 'header'}).find('a').text
            tour_link = soup.find('div', {'class': 'header'}).find('a').get('onclick')
            tour_link = tour_link[tour_link.find('/'): tour_link.find(')') - 1]
                   
            pl_home = soup.find('div', {'class': 'team-text tname-home'}).find('a').get('onclick')
            pl_home = pl_home[pl_home.find('/'): pl_home.find(')') - 1]
                
            pl_away = soup.find('div', {'class': 'team-text tname-away'}).find('a').get('onclick')
            pl_away = pl_away[pl_away.find('/'): pl_away.find(')') - 1]
            
            odd_home = 0
            odd_away = 0
            
            if soup.find('span', {'class': 'odds value'}) is not None:
                try:
                    odd_home = float(soup.find('td', {'class': re.compile('^kx o_1')}).find('span', {'class': 'odds-wrap'}).text)
                except:
                    odd_home = 1
                try:
                    odd_away = float(soup.find('td', {'class': re.compile('^kx o_2')}).find('span', {'class': 'odds-wrap'}).text)
                except:
                    odd_away = 1
           
            matches.loc[len(matches)] =  [m_l, tour, tour_link, m_t, match_status, match_note, pl_home, pl_away, odd_home, odd_away]
            
            
            #matches.loc[len(matches) - 1].to_frame().T.to_csv(f_matches, sep = ';', mode='a', header=(not os.path.exists(f_matches)))
            
            for s in range(0, len(game_home)):
                match_stats.loc[len(match_stats)] =  [m_l, s, game_home[s], game_away[s]]
           
            game_home = []
            game_away = []
            
            
            if i % 50 == 0:
                matches.to_csv('data/matches.csv', sep=';', decimal=',', date_format='%d.%m.%Y %H:%M')
                match_stats.to_csv('data/match_stats.csv', sep=';')
                driver.close()
                driver = webdriver.Chrome(chrome_options = options)
                driver.implicitly_wait(20)
            
    matches.to_csv('data/matches.csv', sep=';', decimal=',', date_format='%d.%m.%Y %H:%M')
    match_stats.to_csv('data/match_stats.csv', sep=';')
    driver.close()
    
    return 0



if Path('data/matches.csv').exists():    
    matches = pd.read_csv('data/matches.csv', sep=';', decimal=',', parse_dates=['date'], date_parser=dateparse, index_col = 0)
else:    
    matches = pd.DataFrame(columns=['id_match', 'tournament', 'tournament_link', 'date', 'match_status', 'match_note',  'id_team_home', 'id_team_away', 'odd_home', 'odd_away'])
 
if Path('data/match_stats.csv').exists():    
    match_stats = pd.read_csv('data/match_stats.csv', sep=';', index_col = 0)
else:
    match_stats = pd.DataFrame(columns=['id_match', 'quarter_num', 'score_home', 'score_away'])

basketball_match_hist = pd.read_csv('basketball_match_hist.csv', index_col=0, sep = ';')

load_basketball_match_info(basketball_match_hist[~(basketball_match_hist['id_match'].isin(matches['id_match'].values))]['id_match'].values, matches, match_stats)

