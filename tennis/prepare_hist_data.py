import pandas as pd
import math

k_factor = lambda x: (20 + 120 / (1 + 1.7 ** ((x - 1500) / 130)))

k_factor_example = lambda x: (1 + 18 / (1 + 2 ** ((x - 1500) / 63)))

dateparse = lambda x: pd.datetime.strptime(x, '%d.%m.%Y %H:%M')

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
    if stage.find('boys-singles') >= 0:
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
     
    return stage


def get_last_matches(cin, p_id, dt, n):
    prev = cin.loc[((cin['id_player_home'] == p_id) | (cin['id_player_away'] == p_id)) & (cin['date'] < dt) , ['id_match', 'id_player_home', 'id_player_away', 'date']].sort_values(by='date', ascending=False)
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
    
    print(exp_val, ' ', disp)
       
    return [exp_val, disp]


def swap(row, p_id):
    if row['id_player_home'] == p_id:
        return row['id_player_home'], row['id_player_away'], row['game_home'], row['game_away'], row['set_home'], row['set_away'], row['result']
    else:
        return row['id_player_away'], row['id_player_home'], row['game_away'], row['game_home'], row['set_away'], row['set_home'], 1 - row['result']


def calc_player_elo_all_time(cin, cin_st, cin_tour_type):
    #matches = get_last_matches(cin, player_id, dt, 20)
    
    matches = pd.merge(cin, cin_st, left_on=  ['id_match'], right_on= ['id_match'], how = 'left').sort_values('date', ascending=True)
    matches = pd.merge(matches, cin_tour_type, left_on = ['tournament_link'], right_on = ['tournament_link'], how = 'left')
    matches['elo_home'] = 0
    matches['elo_away'] = 0
    matches['trnm_adj'] = 0.
    matches['stage_adj'] = 0.
    
    
    for i in range(0, len(matches)):#len(matches)
        print(i)
        #определение индекса строки с предидущим матчем для игрока 1   
        p_h = matches.iloc[i]['id_player_home']
        p_a = matches.iloc[i]['id_player_away']
        dt  = matches.iloc[i]['date']
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
        else:     
            if p_h == matches.at[prev_match_index_player_home, 'id_player_home']:            
                matches.at[m_id, 'elo_home'] = matches.at[prev_match_index_player_home, 'elo_home'] + stage_adj(matches.at[prev_match_index_player_home, 'stage']) * tour_adj(matches.at[prev_match_index_player_home, 'tournament_type']) * k_factor(matches.at[prev_match_index_player_home, 'elo_home']) * (matches.at[prev_match_index_player_home, 'result'] - 1 / (1 + 10 ** ((matches.at[prev_match_index_player_home, 'elo_away'] - matches.at[prev_match_index_player_home, 'elo_home']) / 400))) 
                matches.at[prev_match_index_player_home, 'stage_adj'] = stage_adj(matches.at[prev_match_index_player_home, 'stage'])
                matches.at[prev_match_index_player_home, 'trnm_adj'] = tour_adj(matches.at[prev_match_index_player_home, 'tournament_type'])               
            else:
                matches.at[m_id, 'elo_home'] = matches.at[prev_match_index_player_home, 'elo_away'] + stage_adj(matches.at[prev_match_index_player_home, 'stage']) * tour_adj(matches.at[prev_match_index_player_home, 'tournament_type']) * k_factor(matches.at[prev_match_index_player_home, 'elo_away']) * (1 - matches.at[prev_match_index_player_home, 'result'] - 1 / (1 + 10 ** ((matches.at[prev_match_index_player_home, 'elo_home'] - matches.at[prev_match_index_player_home, 'elo_away']) / 400))) 
                matches.at[prev_match_index_player_home, 'stage_adj'] = stage_adj(matches.at[prev_match_index_player_home, 'stage'])
                matches.at[prev_match_index_player_home, 'trnm_adj'] = tour_adj(matches.at[prev_match_index_player_home, 'tournament_type'])
            
        if prev_match_index_player_away == -1:
            matches.at[m_id, 'elo_away'] = 1500
        else:
            if p_a == matches.at[prev_match_index_player_away, 'id_player_away']:
                matches.at[m_id, 'elo_away'] = matches.at[prev_match_index_player_away, 'elo_away'] + stage_adj(matches.at[prev_match_index_player_away, 'stage']) * tour_adj(matches.at[prev_match_index_player_away, 'tournament_type']) * k_factor(matches.at[prev_match_index_player_away, 'elo_away']) * (1 - matches.at[prev_match_index_player_away, 'result'] - 1 / (1 + 10 ** ((matches.at[prev_match_index_player_away, 'elo_home'] - matches.at[prev_match_index_player_away, 'elo_away']) / 400))) 
                matches.at[prev_match_index_player_away, 'stage_adj'] = stage_adj(matches.at[prev_match_index_player_away, 'stage'])
                matches.at[prev_match_index_player_away, 'trnm_adj'] = tour_adj(matches.at[prev_match_index_player_away, 'tournament_type'])
            else:
                matches.at[m_id, 'elo_away'] = matches.at[prev_match_index_player_away, 'elo_home'] + stage_adj(matches.at[prev_match_index_player_away, 'stage']) * tour_adj(matches.at[prev_match_index_player_away, 'tournament_type']) * k_factor(matches.at[prev_match_index_player_away, 'elo_home']) * (matches.at[prev_match_index_player_away, 'result'] - 1 / (1 + 10 ** ((matches.at[prev_match_index_player_away, 'elo_away'] - matches.at[prev_match_index_player_away, 'elo_home']) / 400))) 
                matches.at[prev_match_index_player_away, 'stage_adj'] = stage_adj(matches.at[prev_match_index_player_away, 'stage'])
                matches.at[prev_match_index_player_away, 'trnm_adj'] = tour_adj(matches.at[prev_match_index_player_away, 'tournament_type'])
#                matches.at[m_id, 'elo_away'] = matches.at[prev_match_index_player_away, 'elo_home'] + ((-1) ** (matches.at[prev_match_index_player_away, 'result'] + 1)) * 10

           
    '''
    matches['id_player_home'], matches['id_player_away'],\
    matches['game_home'], matches['game_away'], \
    matches['set_home'], matches['set_away'], matches['result'] = zip(*matches.apply(lambda x: swap(x, player_id), axis = 1))
    matches['elo'] = 0
    matches.at[len(matches) - 1, 'elo'] = 1500
    '''
    
    matches.to_csv('matches_elo.csv', sep = ';')
    
    return 0


cin = pd.read_csv('data/matches.csv',  # Это то, куда вы скачали файл
                       sep=';', 
                       parse_dates=['date'], date_parser=dateparse, index_col='Unnamed: 0')

cin_st = pd.read_csv('data/match_stats.csv',  # Это то, куда вы скачали файл
                       sep=';', 
                       index_col='Unnamed: 0')

tournaments_type = pd.read_csv('data/tourn_men.csv', sep=';') #типы турниров: GF, MA ...

cin_st['set_home'] = cin_st.apply(lambda x: 1 if x['game_home'] > x['game_away'] else 0, axis = 1)
cin_st['set_away'] = cin_st.apply(lambda x: 0 if x['game_home'] > x['game_away'] else 1, axis = 1)

cin_st_wl = cin_st[['id_match', 'game_home','game_away', 'set_home', 'set_away', 'set_duration']].groupby(['id_match']).sum()
cin_st_wl['result'] = cin_st_wl.apply(lambda x: 1 if x['set_home'] > x['set_away'] else 0, axis = 1)


cin['surf'] = cin.apply(lambda x: get_surf(x['tournament']), axis = 1)
cin['stage'] = cin.apply(lambda x: get_stage(x['tournament'], x['tournament_link']), axis = 1)


cin.to_csv('cin_n.csv', sep = ';')


calc_player_elo_all_time(cin, cin_st_wl, tournaments_type)


ex_d = calc_exp_val_8([1, 1, 1, 1, 1, 1, 1, 2])

print(ex_d[0], ' ', ex_d[1])


t_h = cin.loc[cin['id_match'] == 'by8oXmyh'].iloc[0]['id_player_home']
t_a = cin.loc[cin['id_match'] == 'by8oXmyh'].iloc[0]['id_player_away']
t_m = cin.loc[cin['id_match'] == 'by8oXmyh'].iloc[0]['date']

print(t_h, ' ', t_a, ' ', t_m)


prev_h = cin.loc[((cin['id_player_home'] == t_a) | (cin['id_player_away'] == t_a)) & (cin['date'] < t_m) , ['id_match', 'id_player_home', 'id_player_away', 'date']].sort_values(by='date', ascending=False)[0:8]

#print(prev_h[['id_player_home', 'id_player_away', 'date']])

prev_h = pd.merge(prev_h, cin_st, left_on=  ['id_match'],
                                  right_on= ['id_match'],
                                  how = 'left')