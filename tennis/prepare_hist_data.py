import pandas as pd
import math

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
    if trnm.find(',') > 0:
        trnm = trnm[trnm.find(',') + 2 : len(trnm)]
        if trnm.find('-') > 0:
            stage = trnm[trnm.find('-') + 2 : len(trnm)]
    #else:
        #trnm = trnm[8 : trnm[8: len(trnm)].find('/')]
    if stage == '':
        stage = trnm_l[8 : trnm_l[8: len(trnm_l)].find('/') + 8]
               
    if trnm.find('Qualification') > 0:
        stage = 'Qualification ' + stage
        
    if trnm_l.find('boys-singles') > 0:
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
        return row['id_player_home'], row['id_player_away']
    else:
        return row['id_player_away'], row['id_player_home']


def calc_player_elo_all_time(cin, cin_st, player_id, dt):
    matches = get_last_matches(cin, player_id, dt, 20)
    
    matches = pd.merge(matches, cin_st, left_on=  ['id_match'], right_on= ['id_match'], how = 'left')
    matches.to_csv('matches_elo_prev.csv', sep = ';')
 
    
    matches['id_player_home'], matches['id_player_away']  = zip(*matches.apply(lambda x: swap(x, player_id), axis = 1))
    
    matches.to_csv('matches_elo.csv', sep = ';')
    
    
    return 0

dateparse = lambda x: pd.datetime.strptime(x, '%d.%m.%Y %H:%M')

cin = pd.read_csv('data/matches.csv',  # Это то, куда вы скачали файл
                       sep=';', 
                       parse_dates=['date'], date_parser=dateparse, index_col='Unnamed: 0')

cin_st = pd.read_csv('data/match_stats.csv',  # Это то, куда вы скачали файл
                       sep=';', 
                       index_col='Unnamed: 0')

cin_st['set_home'] = cin_st.apply(lambda x: 1 if x['game_home'] > x['game_away'] else 0, axis = 1)
cin_st['set_away'] = cin_st.apply(lambda x: 0 if x['game_home'] > x['game_away'] else 1, axis = 1)

cin_st_wl = cin_st[['id_match', 'game_home','game_away', 'set_home', 'set_away', 'set_duration']].groupby(['id_match']).sum()
cin_st_wl['result'] = cin_st_wl.apply(lambda x: 1 if x['set_home'] > x['set_away'] else 0, axis = 1)


cin['surf'] = cin.apply(lambda x: get_surf(x['tournament']), axis = 1)
cin['stage'] = cin.apply(lambda x: get_stage(x['tournament'], x['tournament_link']), axis = 1)


cin.to_csv('cin_n.csv', sep = ';')


calc_player_elo_all_time(cin, cin_st_wl, '/player/nadal-rafael/xUwlUnRK', dateparse('10.09.2018  10:15'))


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




print(prev_h)
prev_h.to_csv('prev_h.csv', sep = ';')
