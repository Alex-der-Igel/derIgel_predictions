import pandas as pd
import arc
from player_performance_calc import calc, get_stage, get_surf, tour_adj, stage_adj, k_factor
from pathlib import Path 
from datetime import datetime


def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = '\r')
    # Print New Line on Complete
    if iteration == total: 
        print()

dateparse = lambda x: pd.datetime.strptime(x, '%d.%m.%Y %H:%M')
dateparse_sec = lambda x: pd.datetime.strptime(x, '%Y-%m-%d %H:%M:%S')


def calc_player_elo_all_time(cin, cin_st, cin_tour_type):
 
    matches = pd.merge(cin, cin_st, left_on=  ['id_match'], right_on= ['id_match'], how = 'left').sort_values('date', ascending=True)
    matches = pd.merge(matches, cin_tour_type, left_on = ['tournament_link'], right_on = ['tournament_link'], how = 'left')
    matches['elo_home'] = 0
    matches['elo_away'] = 0
    
    matches['elo_rec_home'] = 0
    matches['elo_rec_away'] = 0
    
    matches['elo_surf_home'] = 0
    matches['elo_surf_away'] = 0
    
    for i in range(0, len(matches)):#len(matches)
        printProgressBar(i, len(matches), prefix = 'Progress:', suffix = 'Complete ' + str(i) + ' from ' + str(len(matches)), length = 20)
        #определение индекса строки с предидущим матчем для игрока 1   
        p_h = matches.iloc[i]['id_player_home']
        p_a = matches.iloc[i]['id_player_away']
        dt  = matches.iloc[i]['date']
        srf = matches.iloc[i]['surf']
        m_id = matches.index[i]
         
                  
        if not matches.loc[(matches['result'].notnull()) & (matches['date'] < dt) & ((matches['id_player_home'] == p_h)|(matches['id_player_away'] == p_h)) , ['id_match','date']].sort_values(by='date', ascending=False).empty:
            prev_match_index_player_home = matches.loc[(matches['result'].notnull()) & (matches['date'] < dt) & ((matches['id_player_home'] == p_h)|(matches['id_player_away'] == p_h)) , ['id_match','date']].sort_values(by='date', ascending=False)['date'].idxmax()
        else:
            prev_match_index_player_home = -1
            
        if not matches.loc[(matches['result'].notnull()) & (matches['date'] < dt) & ((matches['id_player_home'] == p_a)|(matches['id_player_away'] == p_a)) , ['id_match','date']].sort_values(by='date', ascending=False).empty:
            prev_match_index_player_away = matches.loc[(matches['result'].notnull()) & (matches['date'] < dt) & ((matches['id_player_home'] == p_a)|(matches['id_player_away'] == p_a)) , ['id_match','date']].sort_values(by='date', ascending=False)['date'].idxmax()
        else:
            prev_match_index_player_away = -1        
        
        if prev_match_index_player_home == -1:
            matches.at[m_id, 'elo_home'] = 1500
            matches.at[m_id, 'elo_rec_home'] = 1500
        else:     
            if p_h == matches.at[prev_match_index_player_home, 'id_player_home']:            
                matches.at[m_id, 'elo_home'] = matches.at[prev_match_index_player_home, 'elo_home'] + stage_adj(matches.at[prev_match_index_player_home, 'stage']) * tour_adj(matches.at[prev_match_index_player_home, 'tournament_type']) * k_factor(matches.at[prev_match_index_player_home, 'elo_home']) * (matches.at[prev_match_index_player_home, 'result'] - 1 / (1 + 10 ** ((matches.at[prev_match_index_player_home, 'elo_away'] - matches.at[prev_match_index_player_home, 'elo_home']) / 400))) 
                matches.at[m_id, 'elo_rec_home'] = matches.at[prev_match_index_player_home, 'elo_home'] + elo_time_adj(matches.at[prev_match_index_player_home, 'date']) * stage_adj(matches.at[prev_match_index_player_home, 'stage']) * tour_adj(matches.at[prev_match_index_player_home, 'tournament_type']) * k_factor(matches.at[prev_match_index_player_home, 'elo_home']) * (matches.at[prev_match_index_player_home, 'result'] - 1 / (1 + 10 ** ((matches.at[prev_match_index_player_home, 'elo_away'] - matches.at[prev_match_index_player_home, 'elo_home']) / 400))) 
            else:
                matches.at[m_id, 'elo_home'] = matches.at[prev_match_index_player_home, 'elo_away'] + stage_adj(matches.at[prev_match_index_player_home, 'stage']) * tour_adj(matches.at[prev_match_index_player_home, 'tournament_type']) * k_factor(matches.at[prev_match_index_player_home, 'elo_away']) * (1 - matches.at[prev_match_index_player_home, 'result'] - 1 / (1 + 10 ** ((matches.at[prev_match_index_player_home, 'elo_home'] - matches.at[prev_match_index_player_home, 'elo_away']) / 400))) 
                matches.at[m_id, 'elo_rec_home'] = matches.at[prev_match_index_player_home, 'elo_away'] + elo_time_adj(matches.at[prev_match_index_player_home, 'date']) * stage_adj(matches.at[prev_match_index_player_home, 'stage']) * tour_adj(matches.at[prev_match_index_player_home, 'tournament_type']) * k_factor(matches.at[prev_match_index_player_home, 'elo_away']) * (1 - matches.at[prev_match_index_player_home, 'result'] - 1 / (1 + 10 ** ((matches.at[prev_match_index_player_home, 'elo_home'] - matches.at[prev_match_index_player_home, 'elo_away']) / 400))) 
            
        if prev_match_index_player_away == -1:
            matches.at[m_id, 'elo_away'] = 1500
            matches.at[m_id, 'elo_rec_away'] = 1500
        else:
            if p_a == matches.at[prev_match_index_player_away, 'id_player_away']:
                matches.at[m_id, 'elo_away'] = matches.at[prev_match_index_player_away, 'elo_away'] + stage_adj(matches.at[prev_match_index_player_away, 'stage']) * tour_adj(matches.at[prev_match_index_player_away, 'tournament_type']) * k_factor(matches.at[prev_match_index_player_away, 'elo_away']) * (1 - matches.at[prev_match_index_player_away, 'result'] - 1 / (1 + 10 ** ((matches.at[prev_match_index_player_away, 'elo_home'] - matches.at[prev_match_index_player_away, 'elo_away']) / 400))) 
                matches.at[m_id, 'elo_rec_away'] = matches.at[prev_match_index_player_away, 'elo_away'] + elo_time_adj(matches.at[prev_match_index_player_away, 'date']) * stage_adj(matches.at[prev_match_index_player_away, 'stage']) * tour_adj(matches.at[prev_match_index_player_away, 'tournament_type']) * k_factor(matches.at[prev_match_index_player_away, 'elo_away']) * (1 - matches.at[prev_match_index_player_away, 'result'] - 1 / (1 + 10 ** ((matches.at[prev_match_index_player_away, 'elo_home'] - matches.at[prev_match_index_player_away, 'elo_away']) / 400))) 
            else:
                matches.at[m_id, 'elo_away'] = matches.at[prev_match_index_player_away, 'elo_home'] + stage_adj(matches.at[prev_match_index_player_away, 'stage']) * tour_adj(matches.at[prev_match_index_player_away, 'tournament_type']) * k_factor(matches.at[prev_match_index_player_away, 'elo_home']) * (matches.at[prev_match_index_player_away, 'result'] - 1 / (1 + 10 ** ((matches.at[prev_match_index_player_away, 'elo_away'] - matches.at[prev_match_index_player_away, 'elo_home']) / 400))) 
                matches.at[m_id, 'elo_rec_away'] = matches.at[prev_match_index_player_away, 'elo_home'] + elo_time_adj(matches.at[prev_match_index_player_away, 'date']) * stage_adj(matches.at[prev_match_index_player_away, 'stage']) * tour_adj(matches.at[prev_match_index_player_away, 'tournament_type']) * k_factor(matches.at[prev_match_index_player_away, 'elo_home']) * (matches.at[prev_match_index_player_away, 'result'] - 1 / (1 + 10 ** ((matches.at[prev_match_index_player_away, 'elo_away'] - matches.at[prev_match_index_player_away, 'elo_home']) / 400))) 
             

        #расчет эло для текущей поверхности
        
        if not matches.loc[(matches['surf'] == srf) & (matches['result'].notnull()) & (matches['date'] < dt) & ((matches['id_player_home'] == p_h)|(matches['id_player_away'] == p_h)) , ['id_match','date']].sort_values(by='date', ascending=False).empty:
            prev_match_index_player_home = matches.loc[(matches['surf'] == srf) & (matches['result'].notnull()) & (matches['date'] < dt) & ((matches['id_player_home'] == p_h)|(matches['id_player_away'] == p_h)) , ['id_match','date']].sort_values(by='date', ascending=False)['date'].idxmax()
        else:
            prev_match_index_player_home = -1
            
        if not matches.loc[(matches['surf'] == srf) & (matches['result'].notnull()) & (matches['date'] < dt) & ((matches['id_player_home'] == p_a)|(matches['id_player_away'] == p_a)) , ['id_match','date']].sort_values(by='date', ascending=False).empty:
            prev_match_index_player_away = matches.loc[(matches['surf'] == srf) & (matches['result'].notnull()) & (matches['date'] < dt) & ((matches['id_player_home'] == p_a)|(matches['id_player_away'] == p_a)) , ['id_match','date']].sort_values(by='date', ascending=False)['date'].idxmax()
        else:
            prev_match_index_player_away = -1        
        
        if prev_match_index_player_home == -1:
            matches.at[m_id, 'elo_surf_home'] = 1500
            
        else:     
            if p_h == matches.at[prev_match_index_player_home, 'id_player_home']:            
                matches.at[m_id, 'elo_surf_home'] = matches.at[prev_match_index_player_home, 'elo_surf_home'] + stage_adj(matches.at[prev_match_index_player_home, 'stage']) * tour_adj(matches.at[prev_match_index_player_home, 'tournament_type']) * k_factor(matches.at[prev_match_index_player_home, 'elo_surf_home']) * (matches.at[prev_match_index_player_home, 'result'] - 1 / (1 + 10 ** ((matches.at[prev_match_index_player_home, 'elo_surf_away'] - matches.at[prev_match_index_player_home, 'elo_surf_home']) / 400))) 
                
            else:
                matches.at[m_id, 'elo_surf_home'] = matches.at[prev_match_index_player_home, 'elo_surf_away'] + stage_adj(matches.at[prev_match_index_player_home, 'stage']) * tour_adj(matches.at[prev_match_index_player_home, 'tournament_type']) * k_factor(matches.at[prev_match_index_player_home, 'elo_surf_away']) * (1 - matches.at[prev_match_index_player_home, 'result'] - 1 / (1 + 10 ** ((matches.at[prev_match_index_player_home, 'elo_surf_home'] - matches.at[prev_match_index_player_home, 'elo_surf_away']) / 400))) 
                
            
        if prev_match_index_player_away == -1:
            matches.at[m_id, 'elo_surf_away'] = 1500
            
        else:
            if p_a == matches.at[prev_match_index_player_away, 'id_player_away']:
                matches.at[m_id, 'elo_surf_away'] = matches.at[prev_match_index_player_away, 'elo_surf_away'] + stage_adj(matches.at[prev_match_index_player_away, 'stage']) * tour_adj(matches.at[prev_match_index_player_away, 'tournament_type']) * k_factor(matches.at[prev_match_index_player_away, 'elo_surf_away']) * (1 - matches.at[prev_match_index_player_away, 'result'] - 1 / (1 + 10 ** ((matches.at[prev_match_index_player_away, 'elo_surf_home'] - matches.at[prev_match_index_player_away, 'elo_surf_away']) / 400))) 
            else:
                matches.at[m_id, 'elo_surf_away'] = matches.at[prev_match_index_player_away, 'elo_surf_home'] + stage_adj(matches.at[prev_match_index_player_away, 'stage']) * tour_adj(matches.at[prev_match_index_player_away, 'tournament_type']) * k_factor(matches.at[prev_match_index_player_away, 'elo_surf_home']) * (matches.at[prev_match_index_player_away, 'result'] - 1 / (1 + 10 ** ((matches.at[prev_match_index_player_away, 'elo_surf_away'] - matches.at[prev_match_index_player_away, 'elo_surf_home']) / 400))) 
                
   
    matches.to_csv('data/matches_elo.csv', sep = ';')
   
    return matches

def elo_time_adj(x):
    if (datetime.now() - x).total_seconds() / 60 / 60 / 24 < 180:
        return 4
    elif (datetime.now() - x).total_seconds() / 60 / 60 / 24 < 365:
        return 2
    else:
        return 1


def calc_weghted(matches, elo, n = 20):
    
    sum_w = 0
    ar_w = []
    str_w = 0
    for i in range(0, min(len(matches), n)):
        w = 1 / (1 + 10 ** ((matches.iloc[i]['elo_away'] - elo) / 400))
        if w > 0.5:
            w = 1 - w
        sum_w += w
        ar_w.append(w)
        
    for i in range(0, min(len(matches), n)):
        str_w += arc.arc_n(matches.iloc[i]['game_home'] - matches.iloc[i]['game_away']) * ar_w[i] / sum_w
    
    return str_w

def calc_weghted_discount(matches, elo, dt, n = 20):
    
    sum_w = 0
    ar_w = []
    str_w = 0
    for i in range(0, min(len(matches), 20)):
        w = 1 / (1 + 10 ** ((matches.iloc[i]['elo_away'] - elo) / 400))
        if w > 0.5:
            w = 1 - w
        sum_w += w * (0.8 ** ((dt - matches.iloc[i]['date']).total_seconds() / 60. / 60. / 24.))
        ar_w.append(w * (0.8 ** ((dt - matches.iloc[i]['date']).total_seconds() / 60. / 60. / 24.)))
        
    for i in range(0, min(len(matches), n)):
        str_w += arc.arc_n(matches.iloc[i]['game_home'] - matches.iloc[i]['game_away']) * ar_w[i] / sum_w
    
    return str_w



if Path('data/cin_elo_.csv').exists():
    cin_elo = pd.read_csv('data/cin_elo_.csv', sep=';', parse_dates=['date'], date_parser=dateparse_sec, index_col = 0, decimal=",")
elif Path('data/matches_elo.csv').exists():
    cin_elo = pd.read_csv('data/matches_elo.csv', sep=';', parse_dates=['date'], date_parser=dateparse_sec, index_col = 0)
else:
    #читаем входные файлы
    cin_atp = pd.read_csv('data/matches_atp.csv', sep=';', parse_dates=['date'], date_parser=dateparse, index_col = 0)
    cin_st_atp = pd.read_csv('data/match_stats_atp.csv', sep=';', index_col = 0)
    tournaments_type_atp = pd.read_csv('data/tourn_men.csv', sep=';') #типы турниров: GF, MA ...
    cin_atp.loc[cin_atp['odd_home'] == '-' , 'odd_home'] = 1
    cin_atp.loc[cin_atp['odd_away'] == '-' , 'odd_away'] = 1 
    cin_atp['odd_home'] = pd.to_numeric(cin_atp['odd_home'])
    cin_atp['odd_away'] = pd.to_numeric(cin_atp['odd_away'])
    
    cin_wta = pd.read_csv('data/matches_wta.csv', sep=';', parse_dates=['date'], date_parser=dateparse, index_col = 0)
    cin_st_wta = pd.read_csv('data/match_stats_wta.csv', sep=';', index_col = 0)
    tournaments_type_wta = pd.read_csv('data/tourn_women.csv', sep=';') #типы турниров: GF, MA ...
    cin_wta.loc[cin_wta['odd_home'] == '-' , 'odd_home'] = 1
    cin_wta.loc[cin_wta['odd_away'] == '-' , 'odd_away'] = 1 
    cin_wta['odd_home'] = pd.to_numeric(cin_wta['odd_home'])
    cin_wta['odd_away'] = pd.to_numeric(cin_wta['odd_away'])
    
    cin = pd.concat([cin_atp, cin_wta], ignore_index=True)
    cin_st = pd.concat([cin_st_atp, cin_st_wta], ignore_index=True)
    tournaments_type = pd.concat([tournaments_type_atp, tournaments_type_wta], ignore_index=True)
    
    cin = cin.loc[(cin['odd_home'] > 0) & (cin['odd_away'] > 0) ]#& (cin['date'] > dateparse('01.01.2018 00:00'))
#& (cin['date'] > dateparse('01.01.2018 00:00'))
    #добавляем поля кто выиграл сет
    cin_st['set_home'] = cin_st.apply(lambda x: 1 if x['game_home'] > x['game_away'] else 0, axis = 1)
    cin_st['set_away'] = cin_st.apply(lambda x: 0 if x['game_home'] > x['game_away'] else 1, axis = 1)
    
    #добавляем поле кто выиграл матч, 1 - выиграл первый, 0 - второй
    cin_st_wl = cin_st[['id_match', 'game_home','game_away', 'set_home', 'set_away', 'set_duration']].groupby(['id_match'], as_index=False).sum()
    cin_st_wl['result'] = cin_st_wl.apply(lambda x: 1 if x['set_home'] > x['set_away'] else 0, axis = 1)
    
    #добавляем поля покрытие и раунд
    cin['surf'] = cin.apply(lambda x: get_surf(x['tournament']), axis = 1)
    cin['stage'] = cin.apply(lambda x: get_stage(x['tournament'], x['tournament_link']), axis = 1)
    
    #производим расчет рейтингов эло по всем матчам
  
    cin_elo = calc_player_elo_all_time(cin, cin_st_wl, tournaments_type)

#cin_elo['year'] = cin_elo['date'].apply(lambda x: x.year)
#atp = pd.read_csv('data/ranks_atp.csv', sep=';', index_col='Unnamed: 0')

#cin_elo = pd.merge(cin_elo, atp, left_on =  ['id_player_home', 'year'], right_on= ['id_player', 'year'], how = 'left')
 
#cin_elo = cin_elo.loc[(cin_elo['game_home'].notnull()) & (cin_elo['date'] > dateparse('01.06.2018 00:00'))]

if 'set_home_arc_s' not in cin_elo.columns or 'set_away_arc_s' not in cin_elo.columns:
    
    cin_st_atp = pd.read_csv('data/match_stats_atp.csv', sep=';', index_col = 0)
    cin_st_wta = pd.read_csv('data/match_stats_wta.csv', sep=';', index_col = 0)
    cin_st = pd.concat([cin_st_atp, cin_st_wta], ignore_index=True)
    cin_st['set_home'] = cin_st.apply(lambda x: 1 if x['game_home'] > x['game_away'] else 0, axis = 1)
    cin_st['set_away'] = cin_st.apply(lambda x: 0 if x['game_home'] > x['game_away'] else 1, axis = 1)
    
    cin_st['set_home_arc'] = cin_st.apply(lambda x: arc.arc_n(x['game_home'] - x['game_away']), axis = 1)
    cin_st['set_away_arc'] = cin_st.apply(lambda x: arc.arc_n(x['game_away'] - x['game_home']), axis = 1)
    
    cin_st_wl = cin_st[['id_match', 'game_home','game_away', 'set_home', 'set_away', 'set_duration', 'set_home_arc', 'set_away_arc']].groupby(['id_match'], as_index=False).sum()
    
    cin_st_wl['set_home_arc'] = cin_st_wl['set_home_arc'] / (cin_st_wl['set_home'] + cin_st_wl['set_away'])
    cin_st_wl['set_away_arc'] = cin_st_wl['set_away_arc'] / (cin_st_wl['set_home'] + cin_st_wl['set_away'])
    
    cin_st_wl['set_home_arc_s'] = cin_st_wl.apply(lambda x: arc.arc_f(x['set_home'] , x['set_away']), axis = 1)
    cin_st_wl['set_away_arc_s'] = cin_st_wl.apply(lambda x: arc.arc_f(x['set_away'] , x['set_home']), axis = 1)
    
    cin_elo = pd.merge(cin_elo, cin_st_wl[['id_match', 'set_home_arc', 'set_away_arc', 'set_home_arc_s', 'set_away_arc_s']], left_on=  ['id_match'], right_on= ['id_match'], how = 'left').sort_values('date', ascending=True)

cin_elo = cin_elo.loc[(cin_elo['game_home'].notnull())]

upd_list = cin_elo.loc[(cin_elo['str_home'] == 0) & (cin_elo['game_home'].notnull()) & (cin_elo['date'] > dateparse('01.01.2014 00:00'))].index.tolist()    

cin_elo = calc(cin_elo, cin_elo, upd_list)[0]

cin_elo.to_csv('data/cin_elo_.csv', sep = ';', decimal=",")


