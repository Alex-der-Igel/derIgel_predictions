import pandas as pd
import math
import arc
from pathlib import Path 
import numpy as np
from datetime import datetime
from scipy.stats import gamma


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
        

k_factor = lambda x: (20 + 120 / (1 + 1.7 ** ((x - 1500) / 130)))

k_factor_example = lambda x: (1 + 18 / (1 + 2 ** ((x - 1500) / 63)))

dateparse = lambda x: pd.datetime.strptime(x, '%d.%m.%Y %H:%M')
dateparse_sec = lambda x: pd.datetime.strptime(x, '%Y-%m-%d %H:%M:%S')

def tour_adj(tour):
    if tour == 'GS':
        return 1
    elif tour == 'TF':
        return 0.9
    elif tour == 'MA':
        return 0.85
    elif tour == 'OL':
        return 0.8
    elif tour == 'A5':
        return .75
    else:
        return 0.7

def stage_adj(stage):
    if stage.find('boys-singles') >= 0 or stage.find('girls-singles') >= 0:
        return 0.6
    elif stage.find('Qualification') >= 0:
        return 0.8
    elif stage == '1/16-finals' or stage == '1/32-finals' or stage == '1/64-finals':
        return 0.9
    elif stage == '1/8-finals' or stage == 'Quarter-finals':
        return 0.95
    elif stage == 'Semi-finals' or stage == 'Final':
        return 1
    
    else:
        return 0.85

def get_surf(trnm):
    if trnm.find(',') > 0:
        trnm = trnm[trnm.find(',') + 2 : len(trnm)]   
        
        if trnm.find('-') * trnm.find('(') < 0:
            trnm = trnm[0 : max(trnm.find('('), trnm.find('-')) - 1]
        elif trnm.find('-') > 0:
            trnm = trnm[0 : min(trnm.find('('), trnm.find('-')) - 1]
            
    #elif trnm.find('Davis') >= 0:
    #    trnm = 'clay'
    else:
        trnm = 'none'
        
    return trnm


def get_stage(trnm, trnm_l):
    stage = ''
    tr = trnm
    if trnm.find(',') > 0:
        trnm = trnm[trnm.find(',') + 2 : len(trnm)]
        if trnm.find('-') > 0:
            stage = trnm[trnm.find('-') + 2 : len(trnm)]
    #else:
        #trnm = trnm[8 : trnm[8: len(trnm)].find('/')]
    if stage == '':
        stage = trnm_l[8 : trnm_l[8: len(trnm_l)].find('/') + 8]
               
    if tr.find('Qualification') >= 0:
        stage = 'Qualification ' + stage
        
    if trnm_l.find('boys-singles') >= 0:
        stage = 'boys-singles ' + stage
    
    if trnm_l.find('girls-singles') >= 0:
        stage = 'girls-singles ' + stage
    
    return stage


def get_last_matches(cin, p_id, dt, n):
    prev = cin.loc[((cin['id_player_home'] == p_id) | (cin['id_player_away'] == p_id)) & (cin['date'] < dt) , ['id_match', 'id_player_home', 'id_player_away', 'date', 'game_home', 'game_away', 'elo_home', 'elo_away', 'str_home', 'str_away', 'surf']].sort_values(by='date', ascending=False)
    prev = prev[0 : min(n, len(prev))]
    
    return prev


def get_last_matches_surf(cin, p_id, dt, surf, n):
    prev = cin.loc[((cin['id_player_home'] == p_id) | (cin['id_player_away'] == p_id)) & (cin['date'] < dt) & (cin['surf'] == surf) , ['id_match', 'id_player_home', 'id_player_away', 'date', 'game_home', 'game_away', 'elo_home', 'elo_away', 'str_home', 'str_away', 'surf']].sort_values(by='date', ascending=False)
    prev = prev[0 : min(n, len(prev))]
    
    return prev

#return list of expected value and dispersion for list contains 8 elements
def calc_exp_val_8(scores):
    exp_val = 0
    disp = 0
    
    if len(scores) != 8:
        return -1
    
    for i in range(0, len(scores)):
        if  i < 2:
            disp += scores[i] * scores[i] * 8
            exp_val += scores[i] * 8
        
        elif i < 4:
            disp += scores[i] * scores[i] * 4
            exp_val += scores[i] * 4
        
        elif i < 6:
            disp += scores[i] * scores[i] * 2
            exp_val += scores[i] * 2
        
        else:
            disp += scores[i] * scores[i]
            exp_val += scores[i]
        
        i += 1
   
    exp_val = exp_val / 30
    disp = math.sqrt(math.fabs(exp_val * exp_val - disp / 30))
    
    
       
    return [exp_val, disp]

def calc_exp_val_simple(scores, n):
    exp_val = 0
    disp = 0
    if n == 0:
        return [exp_val, disp]
    
    for i in range(0, n):
        disp += scores[i] * scores[i]
        exp_val += scores[i]
          
    exp_val = exp_val / n
    disp = math.sqrt(math.fabs(exp_val * exp_val - disp / n))

    return [exp_val, disp]



def swap(row, p_id):
    if row['id_player_home'] == p_id:
        return row
    else:
        p_h = row['id_player_home']
        p_a = row['id_player_away']
        g_h = row['game_home']
        g_a = row['game_away']
        e_h = row['elo_home']
        e_a = row['elo_away']
        st_h = row['str_home']
        st_a = row['str_away']
        
        row['id_player_home'] = p_a
        row['id_player_away'] = p_h
        row['game_home'] = g_a
        row['game_away'] = g_h
        row['elo_home'] = e_a
        row['elo_away'] = e_h
        row['str_home'] = st_a
        row['str_away'] = st_h        

        return row

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

def calc(matches):
    
    matches.loc[:,'str_home'] = 0.
    matches.loc[:,'str_home_d'] = 0.
    matches.loc[:,'str_home_rec'] = 0.
    matches.loc[:,'str_home_rec_d'] = 0.
    matches.loc[:,'l_home'] = 0.
    matches.loc[:,'l_home_d'] = 0.
    matches.loc[:,'w_home'] = 0.
    matches.loc[:,'w_home_d'] = 0.
    matches.loc[:,'freq_home'] = 0.
    matches.loc[:,'elo_home_played'] = 0
    matches.loc[:,'elo_home_win'] = 0
    matches.loc[:,'elo_home_lose'] = 0
    matches.loc[:,'fatigue_home'] = 0.
    matches.loc[:,'str_home_w'] = 0.
    
    matches.loc[:,'str_away'] = 0.
    matches.loc[:,'str_away_d'] = 0.
    matches.loc[:,'str_away_rec'] = 0.
    matches.loc[:,'str_away_rec_d'] = 0.
    matches.loc[:,'l_away'] = 0.
    matches.loc[:,'l_away_d'] = 0.
    matches.loc[:,'w_away'] = 0.
    matches.loc[:,'w_away_d'] = 0.
    matches.loc[:,'freq_away'] = 0.
    matches.loc[:,'elo_away_played'] = 0
    matches.loc[:,'elo_away_win'] = 0
    matches.loc[:,'elo_away_lose'] = 0
    matches.loc[:,'fatigue_away'] = 0.
    matches.loc[:,'str_away_w'] = 0.
    
    matches.loc[:,'str_home_wd'] = 0.
    matches.loc[:,'str_away_wd'] = 0.
    
    matches.loc[:,'gamma_a_h'] = 0.
    matches.loc[:,'gamma_loc_h'] = 0.
    matches.loc[:,'gamma_scale_h'] = 0.
    
    matches.loc[:,'gamma_a_h_rec'] = 0.
    matches.loc[:,'gamma_loc_h_rec'] = 0.
    matches.loc[:,'gamma_scale_h_rec'] = 0.
    
    matches.loc[:,'gamma_a_h_surf'] = 0.
    matches.loc[:,'gamma_loc_h_surf'] = 0.
    matches.loc[:,'gamma_scale_h_surf'] = 0.
    
    matches.loc[:,'gamma_a_h_rec_surf'] = 0.
    matches.loc[:,'gamma_loc_h_rec_surf'] = 0.
    matches.loc[:,'gamma_scale_h_rec_surf'] = 0.
    
    matches.loc[:,'gamma_a_a'] = 0.
    matches.loc[:,'gamma_loc_a'] = 0.
    matches.loc[:,'gamma_scale_a'] = 0.
    
    matches.loc[:,'gamma_a_a_rec'] = 0.
    matches.loc[:,'gamma_loc_a_rec'] = 0.
    matches.loc[:,'gamma_scale_a_rec'] = 0.
    
    matches.loc[:,'gamma_a_a_surf'] = 0.
    matches.loc[:,'gamma_loc_a_surf'] = 0.
    matches.loc[:,'gamma_scale_a_surf'] = 0.
    
    matches.loc[:,'gamma_a_a_rec_surf'] = 0.
    matches.loc[:,'gamma_loc_a_rec_surf'] = 0.
    matches.loc[:,'gamma_scale_a_rec_surf'] = 0.
    
    
    
    
    for i in range(0, len(matches)):#len(matches) 61176
        
        printProgressBar(i, len(matches), prefix = 'Progress:', suffix = 'Complete ' + str(i) + ' from ' + str(len(matches)), length = 20)
        #print(len(matches))
        #print(i)
      
        p_h = matches.iloc[i]['id_player_home']
        p_a = matches.iloc[i]['id_player_away']
        dt  = matches.iloc[i]['date']
        m_id = matches.index[i]
        
        match = get_last_matches(matches, p_h, dt, 40)
        
        if(len(match) < 8):
            continue
        
        p1_str = 0.
        p1_str_d = 0.
        p1_str_rec = 0.
        p1_str_rec_d = 0.
        p1_freq = 0.
        p1_elo_pl = 0
        p1_elo_w = 0
        p1_elo_l = 0
        p1_fat = 0.
        p1_str_w = 0.
        
        p2_str = 0.
        p2_str_d = 0.
        p2_str_rec = 0.
        p2_str_rec_d = 0.
        p2_freq = 0.
        p2_elo_pl = 0
        p2_elo_w = 0
        p2_elo_l = 0
        p2_fat = 0.
        p2_str_w = 0.
        
        p1_w = 0.
        p1_l = 0.
        p1_l_d = 0.
        
        p2_w = 0.
        p2_l = 0.
        p2_l_d = 0.
        p1_str_wd = 0.
        p2_str_wd = 0.
        
        a_h = loc_h = scale_h = 0.
        a_h_rec = loc_h_rec = scale_h_rec = 0.
        a_h_surf = loc_h_surf = scale_h_surf = 0.
        a_h_rec_surf = loc_h_rec_surf = scale_h_rec_surf = 0.
        
        a_a = loc_a = scale_a = 0.
        a_a_rec = loc_a_rec = scale_a_rec = 0.
        a_a_surf = loc_a_surf = scale_a_surf = 0.
        a_a_rec_surf = loc_a_rec_surf = scale_a_rec_surf = 0.
        
        match = match.apply(lambda x: swap(x, p_h), axis = 1)
        
        p1_str, p1_str_d = calc_exp_val_8((match['game_home'] - match['game_away']).iloc[:8].apply(lambda x: arc.arc_n(x)).values)
        p1_str_rec, p1_str_rec_d = calc_exp_val_simple((match['game_home'] - match['game_away']).apply(lambda x: arc.arc_n(x)).values, 5)
        p1_freq = (match.iloc[0]['date'] - match.iloc[7]['date']) / np.timedelta64(1, 'D')
        p1_l, p1_l_d  = calc_exp_val_simple((match.iloc[:8].loc[match['game_home'] < match['game_away'], 'game_home']-match.iloc[:8].loc[match['game_home'] < match['game_away'], 'game_away']).values, len(match.iloc[:8].loc[match['game_home'] < match['game_away']]))
        p1_w, p1_w_d  = calc_exp_val_simple((match.iloc[:8].loc[match['game_home'] > match['game_away'], 'game_home']-match.iloc[:8].loc[match['game_home'] > match['game_away'], 'game_away']).values, len(match.iloc[:8].loc[match['game_home'] > match['game_away']]))
        p1_elo_pl = calc_exp_val_simple(match['elo_away'].values, 8)[0]
        p1_elo_w = calc_exp_val_simple(match.iloc[:8].loc[match['game_home'] > match['game_away'], 'elo_away'].values, len(match.iloc[:8].loc[match['game_home'] > match['game_away']]))[0]
        p1_elo_l = calc_exp_val_simple(match.iloc[:8].loc[match['game_home'] < match['game_away'], 'elo_away'].values, len(match.iloc[:8].loc[match['game_home'] < match['game_away']]))[0]
        p1_fat = (match.iloc[0]['game_home'] + match.iloc[0]['game_away']) * (0.7 ** ((dt - match.iloc[0]['date']).total_seconds() / 60. / 60. / 24.)) + \
                 (match.iloc[1]['game_home'] + match.iloc[1]['game_away']) * (0.7 ** ((dt - match.iloc[1]['date']).total_seconds() / 60. / 60. / 24.)) + \
                 (match.iloc[2]['game_home'] + match.iloc[2]['game_away']) * (0.7 ** ((dt - match.iloc[2]['date']).total_seconds() / 60. / 60. / 24.)) + \
                 (match.iloc[3]['game_home'] + match.iloc[3]['game_away']) * (0.7 ** ((dt - match.iloc[3]['date']).total_seconds() / 60. / 60. / 24.))
        p1_str_w = calc_weghted(match, matches.iloc[i]['elo_away'], n = 20)
        p1_str_wd = calc_weghted_discount(match, matches.iloc[i]['elo_away'], matches.iloc[i]['date'], n = 20)
        
        #calculate gamma distribution for last 20 matches
        #calculate number of match to build ditribution
        gamma_len = len(match.loc[(match['str_home'] > 0.)])
        gamma_str = []
              
        
        if(gamma_len >= 8):
            #if enough to calculate distribution
            elo = matches.iloc[i]['elo_away']
            for gamma_cnt in range(0, min(20, gamma_len)):
                matches_for_gamma = get_last_matches(match, p_h, match.iloc[gamma_cnt]['date'], 20)
                #matches_for_gamma = matches_for_gamma.apply(lambda x: swap(x, p_h), axis = 1)
                gamma_str.append(calc_weghted(matches_for_gamma, elo, n = 8))
                
            a_h, loc_h, scale_h = gamma.fit(gamma_str)
            a_h_rec, loc_h_rec, scale_h_rec = gamma.fit(gamma_str[:8])
        
        
        #get last matches by surface
        match = get_last_matches_surf(matches, p_h, dt, matches.iloc[i]['surf'], 40)
        
        match = match.apply(lambda x: swap(x, p_h), axis = 1)        
        gamma_len = len(match.loc[match['str_home'] > 0.])
        gamma_str = []
        
        if(gamma_len >= 8):
            #if enough to calculate distribution
            elo = matches.iloc[i]['elo_away']
            for gamma_cnt in range(0, min(20, gamma_len)):
                matches_for_gamma = get_last_matches_surf(match, p_h, match.iloc[gamma_cnt]['date'], matches.iloc[i]['surf'], 20)
                #matches_for_gamma = matches_for_gamma.apply(lambda x: swap(x, p_h), axis = 1)
                gamma_str.append(calc_weghted(matches_for_gamma, elo, n = 8))
        
            a_h_surf, loc_h_surf, scale_h_surf = gamma.fit(gamma_str)
            a_h_rec_surf, loc_h_rec_surf, scale_h_rec_surf = gamma.fit(gamma_str[:8])
            
        matches.at[m_id, 'str_home'] = p1_str
        matches.at[m_id, 'str_home_d'] = p1_str_d
        matches.at[m_id, 'str_home_rec'] = p1_str_rec
        matches.at[m_id, 'str_home_rec_d'] = p1_str_rec_d
        matches.at[m_id, 'l_home'] = p1_l
        matches.at[m_id, 'l_home_d'] = p1_l_d
        matches.at[m_id, 'w_home'] = p1_w
        matches.at[m_id, 'w_home_d'] = p1_w_d
        matches.at[m_id, 'freq_home'] = p1_freq
        matches.at[m_id, 'elo_home_played'] = p1_elo_pl
        matches.at[m_id, 'elo_home_win'] = p1_elo_w
        matches.at[m_id, 'elo_home_lose'] = p1_elo_l
        matches.at[m_id, 'fatigue_home'] = p1_fat    
        
        matches.at[m_id, 'str_home_w'] = p1_str_w  
        matches.at[m_id, 'str_home_wd'] = p1_str_wd
        
        matches.at[m_id, 'gamma_a_h'] = a_h
        matches.at[m_id, 'gamma_loc_h'] = loc_h
        matches.at[m_id, 'gamma_scale_h'] = scale_h
        
        matches.at[m_id, 'gamma_a_h_rec'] = a_h_rec
        matches.at[m_id, 'gamma_loc_h_rec'] = loc_h_rec
        matches.at[m_id, 'gamma_scale_h_rec'] = scale_h_rec
        
        matches.at[m_id, 'gamma_a_h_surf'] = a_h_surf
        matches.at[m_id, 'gamma_loc_h_surf'] = loc_h_surf
        matches.at[m_id, 'gamma_scale_h_surf'] = scale_h_surf
        
        matches.at[m_id, 'gamma_a_h_rec_surf'] = a_h_rec_surf
        matches.at[m_id, 'gamma_loc_h_rec_surf'] = loc_h_rec_surf
        matches.at[m_id, 'gamma_scale_h_rec_surf'] = scale_h_rec_surf
        
        
          
        match = get_last_matches(matches, p_a, dt, 40)
        
        if(len(match) < 8):
            continue
        
        match = match.apply(lambda x: swap(x, p_a), axis = 1)
        
        p2_str, p2_str_d = calc_exp_val_8((match['game_home'] - match['game_away']).iloc[:8].apply(lambda x: arc.arc_n(x)).values)
        p2_str_rec, p2_str_rec_d = calc_exp_val_simple((match['game_home'] - match['game_away']).apply(lambda x: arc.arc_n(x)).values, 5)
        p2_freq = (match.iloc[0]['date'] - match.iloc[7]['date']) / np.timedelta64(1, 'D')
        p2_l, p2_l_d = calc_exp_val_simple((match.iloc[:8].loc[match['game_home'] < match['game_away'], 'game_home']-match.iloc[:8].loc[match['game_home'] < match['game_away'], 'game_away']).values, len(match.iloc[:8].loc[match['game_home'] < match['game_away']]))
        p2_w, p2_w_d = calc_exp_val_simple((match.iloc[:8].loc[match['game_home'] > match['game_away'], 'game_home']-match.iloc[:8].loc[match['game_home'] > match['game_away'], 'game_away']).values, len(match.iloc[:8].loc[match['game_home'] > match['game_away']]))
        p2_elo_pl = calc_exp_val_simple(match['elo_away'].values, 8)[0]
        p2_elo_w = calc_exp_val_simple(match.iloc[:8].loc[match['game_home'] > match['game_away'], 'elo_away'].values, len(match.iloc[:8].loc[match['game_home'] > match['game_away']]))[0]
        p2_elo_l = calc_exp_val_simple(match.iloc[:8].loc[match['game_home'] < match['game_away'], 'elo_away'].values, len(match.iloc[:8].loc[match['game_home'] < match['game_away']]))[0]
        p2_fat = (match.iloc[0]['game_home'] + match.iloc[0]['game_away']) * (0.7 ** ((dt - match.iloc[0]['date']).total_seconds() / 60. / 60. / 24.)) + \
                 (match.iloc[1]['game_home'] + match.iloc[1]['game_away']) * (0.7 ** ((dt - match.iloc[1]['date']).total_seconds() / 60. / 60. / 24.)) + \
                 (match.iloc[2]['game_home'] + match.iloc[2]['game_away']) * (0.7 ** ((dt - match.iloc[2]['date']).total_seconds() / 60. / 60. / 24.)) + \
                 (match.iloc[3]['game_home'] + match.iloc[3]['game_away']) * (0.7 ** ((dt - match.iloc[3]['date']).total_seconds() / 60. / 60. / 24.))
        p2_str_w = calc_weghted(match, matches.iloc[i]['elo_away'], n = 20)
        p2_str_wd = calc_weghted_discount(match, matches.iloc[i]['elo_away'], matches.iloc[i]['date'], n = 20)

  
        #calculate gamma distribution for last 20 matches
        #calculate number of match to build ditribution
        gamma_len = len(match.loc[match['str_home'] > 0.])
        gamma_str = []
        
        if(gamma_len >= 8):
            #if enough to calculate distribution
            elo = matches.iloc[i]['elo_home']
            for gamma_cnt in range(0, min(20, gamma_len)):
                matches_for_gamma = get_last_matches(match, p_a, match.iloc[gamma_cnt]['date'], 20)
                #matches_for_gamma = matches_for_gamma.apply(lambda x: swap(x, p_a), axis = 1)
                gamma_str.append(calc_weghted(matches_for_gamma, elo, n = 8))
        
            a_a, loc_a, scale_a = gamma.fit(gamma_str)
            a_a_rec, loc_a_rec, scale_a_rec = gamma.fit(gamma_str[:8])
        
        
        #get last matches by surface
        match = get_last_matches_surf(matches, p_a, dt, matches.iloc[i]['surf'], 40)
        
        match = match.apply(lambda x: swap(x, p_a), axis = 1)        
        gamma_len = len(match.loc[match['str_home'] > 0.])
        gamma_str = []
        
        if(gamma_len >= 8):
            #if enough to calculate distribution
            elo = matches.iloc[i]['elo_home']
            for gamma_cnt in range(0, min(20, gamma_len)):
                matches_for_gamma = get_last_matches_surf(match, p_a, match.iloc[gamma_cnt]['date'], matches.iloc[i]['surf'], 20)
                #matches_for_gamma = matches_for_gamma.apply(lambda x: swap(x, p_a), axis = 1)
                gamma_str.append(calc_weghted(matches_for_gamma, elo, n = 8))
        
            a_a_surf, loc_a_surf, scale_a_surf = gamma.fit(gamma_str)
            a_a_rec_surf, loc_a_rec_surf, scale_a_rec_surf = gamma.fit(gamma_str[:8])
          

        matches.at[m_id, 'str_home_w'] = p1_str_w  
        matches.at[m_id, 'str_home_wd'] = p1_str_wd
        
        matches.at[m_id, 'gamma_a_h'] = a_h
        matches.at[m_id, 'gamma_loc_h'] = loc_h
        matches.at[m_id, 'gamma_scale_h'] = scale_h
        
        matches.at[m_id, 'gamma_a_h_rec'] = a_h_rec
        matches.at[m_id, 'gamma_loc_h_rec'] = loc_h_rec
        matches.at[m_id, 'gamma_scale_h_rec'] = scale_h_rec
        
        matches.at[m_id, 'gamma_a_h_surf'] = a_h_surf
        matches.at[m_id, 'gamma_loc_h_surf'] = loc_h_surf
        matches.at[m_id, 'gamma_scale_h_surf'] = scale_h_surf
        
        matches.at[m_id, 'gamma_a_h_rec_surf'] = a_h_rec_surf
        matches.at[m_id, 'gamma_loc_h_rec_surf'] = loc_h_rec_surf
        matches.at[m_id, 'gamma_scale_h_rec_surf'] = scale_h_rec_surf
        
        matches.at[m_id, 'str_away'] = p2_str
        matches.at[m_id, 'str_away_d'] = p2_str_d
        matches.at[m_id, 'str_away_rec'] = p2_str_rec
        matches.at[m_id, 'str_away_rec_d'] = p2_str_rec_d
        matches.at[m_id, 'l_away'] = p2_l
        matches.at[m_id, 'l_away_d'] = p2_l_d
        matches.at[m_id, 'w_away'] = p2_w
        matches.at[m_id, 'w_away_d'] = p2_w_d
        matches.at[m_id, 'freq_away'] = p2_freq
        matches.at[m_id, 'elo_away_played'] = p2_elo_pl
        matches.at[m_id, 'elo_away_win'] = p2_elo_w
        matches.at[m_id, 'elo_away_lose'] = p2_elo_l
        matches.at[m_id, 'fatigue_away'] = p2_fat        
        
        matches.at[m_id, 'str_away_w'] = p2_str_w
        matches.at[m_id, 'str_away_wd'] = p2_str_wd
        
        matches.at[m_id, 'gamma_a_a'] = a_a
        matches.at[m_id, 'gamma_loc_a'] = loc_a
        matches.at[m_id, 'gamma_scale_a'] = scale_a
        
        matches.at[m_id, 'gamma_a_a_rec'] = a_a_rec
        matches.at[m_id, 'gamma_loc_a_rec'] = loc_a_rec
        matches.at[m_id, 'gamma_scale_a_rec'] = scale_a_rec
        
        matches.at[m_id, 'gamma_a_a_surf'] = a_a_surf
        matches.at[m_id, 'gamma_loc_a_surf'] = loc_a_surf
        matches.at[m_id, 'gamma_scale_a_surf'] = scale_a_surf
        
        matches.at[m_id, 'gamma_a_a_rec_surf'] = a_a_rec_surf
        matches.at[m_id, 'gamma_loc_a_rec_surf'] = loc_a_rec_surf
        matches.at[m_id, 'gamma_scale_a_rec_surf'] = scale_a_rec_surf
        
    return 0



if Path('data/matches_elo.csv').exists():
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
#
#cin_elo = pd.merge(cin_elo, atp, left_on =  ['id_player_home', 'year'], right_on= ['id_player', 'year'], how = 'left')
 
#cin_elo = cin_elo.loc[(cin_elo['date'] > dateparse('01.01.2018 00:00'))]    

#cin_elo = cin_elo.loc[(cin_elo['game_home'].notnull()) & (cin_elo['date'] > dateparse('01.01.2018 00:00'))]    

cin_elo = cin_elo.loc[(cin_elo['game_home'].notnull())]    

calc(cin_elo)

cin_elo.to_csv('cin_elo_.csv', sep = ';', decimal=",")


