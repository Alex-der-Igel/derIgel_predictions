import math, datetime
import arc
from arc import printProgressBar
import numpy as np
from scipy.stats import gamma

k_factor = lambda x: (20 + 120 / (1 + 1.7 ** ((x - 1500) / 130)))

k_factor_example = lambda x: (1 + 18 / (1 + 2 ** ((x - 1500) / 63)))

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
        w = 1 / (1 + 10 ** ((matches.iloc[i]['elo_away'] - elo) / 800))
        if w > 0.5:
            w = 1 - w
        sum_w += w
        ar_w.append(w)
        
    for i in range(0, min(len(matches), n)):
        str_w += arc.arc_n(matches.iloc[i]['game_home'] - matches.iloc[i]['game_away']) * ar_w[i] / sum_w
    
    return str_w

def calc_weghted_discount(matches, elo, dt, n = 20, disc = 0.98):
    
    sum_w = 0
    ar_w = []
    str_w = 0
    for i in range(0, min(len(matches), 20)):
        w = 1 / (1 + 10 ** ((matches.iloc[i]['elo_away'] - elo) / 800))
        if w > 0.5:
            w = 1 - w
        sum_w += w * (disc ** ((dt - matches.iloc[i]['date']).total_seconds() / 60. / 60. / 24.))
        ar_w.append(w * (disc ** ((dt - matches.iloc[i]['date']).total_seconds() / 60. / 60. / 24.)))
        
    for i in range(0, min(len(matches), n)):
        str_w += arc.arc_n(matches.iloc[i]['game_home'] - matches.iloc[i]['game_away']) * ar_w[i] / sum_w
    
    return str_w

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
    prev = cin.loc[((cin['id_player_home'] == p_id) | (cin['id_player_away'] == p_id)) & (cin['date'] < dt) , ['id_match', 'id_player_home', 'id_player_away', 'date', 'game_home', 'game_away', 'elo_home', 'elo_away', 'set_home_arc', 'set_away_arc', 'set_home_arc_s', 'set_away_arc_s', 'surf']].sort_values(by='date', ascending=False)
    prev = prev[0 : min(n, len(prev))]
    
    return prev


def get_last_matches_surf(cin, p_id, dt, surf, n):
    prev = cin.loc[((cin['id_player_home'] == p_id) | (cin['id_player_away'] == p_id)) & (cin['date'] < dt) & (cin['surf'] == surf) , ['id_match', 'id_player_home', 'id_player_away', 'date', 'game_home', 'game_away', 'elo_home', 'elo_away', 'set_home_arc', 'set_away_arc', 'set_home_arc_s', 'set_away_arc_s', 'surf']].sort_values(by='date', ascending=False)
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
        st_h = row['set_home_arc']
        st_a = row['set_away_arc']
        a_h = row['set_home_arc_s']
        a_a = row['set_away_arc_s']
        
        row['id_player_home'] = p_a
        row['id_player_away'] = p_h
        row['game_home'] = g_a
        row['game_away'] = g_h
        row['elo_home'] = e_a
        row['elo_away'] = e_h
        row['set_home_arc'] = st_a
        row['set_away_arc'] = st_h
        row['set_home_arc_s'] = a_a  
        row['set_away_arc_s'] = a_h         

        return row
    
def calc_stats(matches, match, p_id, dt, elo, surf):
    
    player_stats = np.zeros(32)
    
    match = match.apply(lambda x: swap(x, p_id), axis = 1)
        
    player_stats[0], player_stats[1] = calc_exp_val_8((match['game_home'] - match['game_away']).iloc[:8].apply(lambda x: arc.arc_n(x)).values)
    player_stats[2], player_stats[3] = calc_exp_val_simple((match['game_home'] - match['game_away']).apply(lambda x: arc.arc_n(x)).values, 5)
    player_stats[4], player_stats[5]  = calc_exp_val_simple((match.iloc[:8].loc[match['game_home'] < match['game_away'], 'game_home']-match.iloc[:8].loc[match['game_home'] < match['game_away'], 'game_away']).values, len(match.iloc[:8].loc[match['game_home'] < match['game_away']]))
    player_stats[6], player_stats[7]  = calc_exp_val_simple((match.iloc[:8].loc[match['game_home'] > match['game_away'], 'game_home']-match.iloc[:8].loc[match['game_home'] > match['game_away'], 'game_away']).values, len(match.iloc[:8].loc[match['game_home'] > match['game_away']]))
    player_stats[8] = (match.iloc[0]['date'] - match.iloc[7]['date']) / np.timedelta64(1, 'D')
    
    player_stats[9 ] = calc_exp_val_simple(match['elo_away'].values, 8)[0]
    player_stats[10] = calc_exp_val_simple(match.iloc[:8].loc[match['game_home'] > match['game_away'], 'elo_away'].values, len(match.iloc[:8].loc[match['game_home'] > match['game_away']]))[0]
    player_stats[11] = calc_exp_val_simple(match.iloc[:8].loc[match['game_home'] < match['game_away'], 'elo_away'].values, len(match.iloc[:8].loc[match['game_home'] < match['game_away']]))[0]
    player_stats[12] = (match.iloc[0]['game_home'] + match.iloc[0]['game_away']) * (0.7 ** ((dt - match.iloc[0]['date']).total_seconds() / 60. / 60. / 24.)) + \
             (match.iloc[1]['game_home'] + match.iloc[1]['game_away']) * (0.7 ** ((dt - match.iloc[1]['date']).total_seconds() / 60. / 60. / 24.)) + \
             (match.iloc[2]['game_home'] + match.iloc[2]['game_away']) * (0.7 ** ((dt - match.iloc[2]['date']).total_seconds() / 60. / 60. / 24.)) + \
             (match.iloc[3]['game_home'] + match.iloc[3]['game_away']) * (0.7 ** ((dt - match.iloc[3]['date']).total_seconds() / 60. / 60. / 24.))
    player_stats[13] = calc_weghted(match, elo, n = 20)
    player_stats[14] = calc_weghted_discount(match, elo, dt, n = 20)

    #calculate gamma distribution for last 20 matches
    #calculate number of match to build ditribution
    gamma_len = max(0, len(match) - 8)
    gamma_str = []
    gamma_str_time = []
       
    if(gamma_len >= 8):
        
        #if enough to calculate distribution
        for gamma_cnt in range(0, min(20, gamma_len)):
            matches_for_gamma = get_last_matches(match, p_id, match.iloc[gamma_cnt]['date'], 20)
            #matches_for_gamma = matches_for_gamma.apply(lambda x: swap(x, p_h), axis = 1)
            gamma_str.append(calc_weghted_discount(matches_for_gamma, elo, match.iloc[gamma_cnt]['date'], n = 20))
            gamma_str_time.append(calc_weghted_discount(matches_for_gamma, elo, match.iloc[gamma_cnt]['date'], n = 20, disc = 0.8))
            
        player_stats[15], player_stats[16], player_stats[17] = gamma.fit(gamma_str, floc = -1)
        player_stats[18], player_stats[19], player_stats[20] = gamma.fit(gamma_str[:8], floc = -1)
        player_stats[27], player_stats[28], player_stats[29] = gamma.fit(gamma_str_time, floc = -1)
    
    player_stats[30]= calc_exp_val_8((match['set_home_arc']).iloc[:8].values)[0]           
    player_stats[31]= calc_exp_val_8((match['set_home_arc_s']).iloc[:8].values)[0]
    
    #get last matches by surface
    match = get_last_matches_surf(matches, p_id, dt, surf, 40)
    
    match = match.apply(lambda x: swap(x, p_id), axis = 1)        
    gamma_len = max(0, len(match) - 8)
    gamma_str = []
    
    if(gamma_len >= 8):
        #if enough to calculate distribution
        for gamma_cnt in range(0, min(20, gamma_len)):
            matches_for_gamma = get_last_matches_surf(match, p_id, match.iloc[gamma_cnt]['date'], surf, 20)
            #matches_for_gamma = matches_for_gamma.apply(lambda x: swap(x, p_h), axis = 1)
            gamma_str.append(calc_weghted_discount(matches_for_gamma, elo, match.iloc[gamma_cnt]['date'], n = 20))
      
        player_stats[21], player_stats[22], player_stats[23] = gamma.fit(gamma_str, floc = -1)
        player_stats[24], player_stats[25], player_stats[26] = gamma.fit(gamma_str[:8], floc = -1)
    
    
    return player_stats


def calc(pred, matches, upd_list):
    
    columns_home = ['str_home'
                   , 'str_home_d'
                   , 'str_home_rec'
                   , 'str_home_rec_d'
                   , 'l_home'
                   , 'l_home_d'
                   , 'w_home'
                   , 'w_home_d'
                   , 'freq_home'
                   , 'elo_home_played'
                   , 'elo_home_win'
                   , 'elo_home_lose'
                   , 'fatigue_home'
                   , 'str_home_w'
                   , 'str_home_wd'
                   , 'gamma_a_h'
                   , 'gamma_loc_h'
                   , 'gamma_scale_h'
                   , 'gamma_a_h_rec'
                   , 'gamma_loc_h_rec'
                   , 'gamma_scale_h_rec'
                   , 'gamma_a_h_surf'
                   , 'gamma_loc_h_surf'
                   , 'gamma_scale_h_surf'
                   , 'gamma_a_h_rec_surf'
                   , 'gamma_loc_h_rec_surf'
                   , 'gamma_scale_h_rec_surf'
                   , 'gamma_a_h_time'
                   , 'gamma_loc_h_time'
                   , 'gamma_scale_h_time'
                   , 'set_score_h'
                   , 'match_score_h'
                   ]
        
    columns_away = [  'str_away'
                   , 'str_away_d'
                   , 'str_away_rec'
                   , 'str_away_rec_d'
                   , 'l_away'
                   , 'l_away_d'
                   , 'w_away'
                   , 'w_away_d'
                   , 'freq_away'
                   , 'elo_away_played'
                   , 'elo_away_win'
                   , 'elo_away_lose'
                   , 'fatigue_away'
                   , 'str_away_w'
                   , 'str_away_wd'
                   , 'gamma_a_a'
                   , 'gamma_loc_a'
                   , 'gamma_scale_a'
                   , 'gamma_a_a_rec'
                   , 'gamma_loc_a_rec'
                   , 'gamma_scale_a_rec'
                   , 'gamma_a_a_surf'
                   , 'gamma_loc_a_surf'
                   , 'gamma_scale_a_surf'
                   , 'gamma_a_a_rec_surf'
                   , 'gamma_loc_a_rec_surf'
                   , 'gamma_scale_a_rec_surf'
                   , 'gamma_a_a_time'
                   , 'gamma_loc_a_time'
                   , 'gamma_scale_a_time'
                   , 'set_score_a'
                   , 'match_score_a'
                   ]
        
    '''
        0  - player str
        1  - player str disp
        2  - player str recent
        3  - player str recent disp
        4  - player lose avg
        5  - player lose avg disp
        6  - player win avg
        7  - player win avg disp
        8  - player frequency
        9  - player elo ratio played
        10 - player elo ratio win
        11 - player elo ratio lose
        12 - player fatigue
        13 - player str weight
        14 - player str weight date
        15 - player gamma a
        16 - player gamma loc
        17 - player gamma scale
        18 - player gamma rec a
        19 - player gamma rec loc
        20 - player gamma rec scale
        21 - player gamma surf a
        22 - player gamma surf loc
        23 - player gamma surf scale
        24 - player gamma surf rec a
        25 - player gamma surf rec loc
        26 - player gamma surf rec scale
        27 - player gamma time a
        28 - player gamma time loc
        29 - player gamma time scale
        '''
        
    for col in columns_home:
        pred[col] = 0.
    
    for col in columns_away:
        pred[col] = 0.
        
    ii = 0        
    for i in upd_list:#len(matches)
        
        #print(i, len(pred))
        ii += 1
        printProgressBar(ii, len(upd_list), prefix = 'Progress:', suffix = 'Complete ' + str(ii) + ' from ' + str(len(upd_list)), length = 20)
        
        #определение индекса строки с предидущим матчем для игрока 1   
        
        p_h = pred.at[i, 'id_player_home']
        p_a = pred.at[i, 'id_player_away']
        dt  = pred.at[i ,'date']
        m_id = i        
        
        match = get_last_matches(matches,p_h , dt, 40)
        
        if(len(match) < 8):
            continue
        
        player_stats = calc_stats(matches, match, p_h, dt, pred.at[i, 'elo_away'], pred.at[i, 'surf'])
        
        for ids, col in enumerate(columns_home):
            pred.at[m_id, col] = player_stats[ids]
          
        match = get_last_matches(matches, p_a, dt, 40)
        
        if(len(match) < 8):
            continue
        
        player_stats = calc_stats(matches, match, p_a, dt, pred.at[i, 'elo_home'], pred.at[i, 'surf'])
        
        for ids, col in enumerate(columns_away):
            pred.at[m_id, col] = player_stats[ids]
            
        if ii % 1000 == 0:
            pred.to_csv('cin_elo_.csv', sep = ';', decimal=",")
                  
    return pred