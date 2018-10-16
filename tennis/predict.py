#from sklearn import cross_validation
from sklearn.metrics import accuracy_score
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
import datetime
import xgboost as xgb

from scipy.stats import gamma
import numpy as np

import pandas as pd

from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM, Embedding


dateparse_sec = lambda x: pd.datetime.strptime(x, '%Y-%m-%d %H:%M:%S')
dateparse = lambda x: pd.datetime.strptime(x, '%d.%m.%Y %H:%M')

cin = pd.read_csv('data/cin_elo_.csv', sep=';', parse_dates=['date'], date_parser=dateparse_sec, index_col = 0, decimal=",")
cin_st_atp = pd.read_csv('data/match_stats_atp.csv', sep=';', index_col = 0)
cin_st_wta = pd.read_csv('data/match_stats_wta.csv', sep=';', index_col = 0)
cin_st = pd.concat([cin_st_atp, cin_st_wta], ignore_index=True)

pl_atp = pd.read_csv('data/players_atp.csv', sep=';', parse_dates=['dob'], date_parser=dateparse_sec, index_col = 0)
pl_wta = pd.read_csv('data/players_wta.csv', sep=';', parse_dates=['dob'], date_parser=dateparse_sec, index_col = 0)
players = pd.concat([pl_atp, pl_wta], ignore_index=True)

cin_st = cin_st.loc[(cin_st['set_num'] == 0.)]
cin_st['result_1st_set'] = cin_st.apply(lambda x: 1 if x['game_home'] > x['game_away'] else 0, axis = 1)    

cin = pd.merge(cin, cin_st[['id_match', 'result_1st_set']], left_on = ['id_match'], right_on= ['id_match'], how = 'left').sort_values('date', ascending=True)

cin = pd.merge(cin, players[['id_player', 'dob']], left_on = ['id_player_home'], right_on= ['id_player'], how = 'left')
cin['dob'] = cin['dob'].fillna(dateparse('01.01.1990 00:00'))
cin.rename(columns = {'dob':'dob_home'}, inplace=True)

cin = pd.merge(cin, players[['id_player', 'dob']], left_on = ['id_player_away'], right_on= ['id_player'], how = 'left')
cin['dob'] = cin['dob'].fillna(dateparse('01.01.1990 00:00'))
cin.rename(columns = {'dob':'dob_away'}, inplace=True)

cin['age_dif'] = cin.apply(lambda x: (x['date'] - x['dob_home']).total_seconds() / (x['date'] - x['dob_away']).total_seconds(), axis = 1)

cin.to_csv('gamma.csv', sep = ';', decimal=",")

for col in ['win_1st_set_lose_home', 'lose_1st_set_win_home', 'win_1st_set_lose_away', 'lose_1st_set_win_away', 'win_matches_home', 'win_games_home', 'win_sets_home', 'win_matches_away', 'win_games_away', 'win_sets_away', 'p_gamma', 'p_gamma_rec', 'p_gamma_surf', 'p_gamma_rec_surf', 'p_gamma_time', 'p_gamma_rec_p5', 'p_gamma_rec_m5', 'win_perc', 'set_perc', 'game_perc']:
    cin[col] = 0.

cin['elo'] = 1 / (1 + 10 ** ((cin['elo_away'] - cin['elo_home']) / 400))
cin['elo_recent'] = 1 / (1 + 10 ** ((cin['elo_rec_away'] - cin['elo_rec_home']) / 400))
cin['elo_surf'] = 1 / (1 + 10 ** ((cin['elo_surf_away'] - cin['elo_surf_home']) / 400))

cin['str12'] = cin['str_home'] - cin['str_away']
cin['str12_rec'] = cin['str_home_rec'] - cin['str_away_rec']
cin['lose12'] = cin['l_home'] - cin['l_away']
cin['win12'] = cin['w_home'] - cin['w_away']
cin['freq'] = cin['freq_home'] / cin['freq_away']
cin['fat'] = cin['fatigue_home'] - cin['fatigue_away']

cin['str_w'] = cin['str_home_w'] - cin['str_away_w']

cin['str_w'] = cin['str_home_w'] - cin['str_away_w']

cin['set_score'] = cin['set_score_h'] - cin['set_score_a']
cin['match_score'] = cin['match_score_h'] - cin['match_score_a']


def get_last_matches(cin, p_id, dt, n):
    prev = cin.loc[((cin['id_player_home'] == p_id) | (cin['id_player_away'] == p_id)) & (cin['date'] < dt) ].sort_values(by='date', ascending=False)
    prev = prev[0 : min(n, len(prev))]
    
    return prev

def prob_g(cin, rec = 0):
    
    if rec == 0:
        str_h = 'str_home'
        str_a = 'str_away'
        str_h_d = 'str_home_d'
        str_a_d = 'str_away_d'
    else:
        str_h = 'str_home_rec'
        str_a = 'str_away_rec'
        str_h_d = 'str_home_rec_d'
        str_a_d = 'str_away_rec_d'

    if cin[str_h] == 0. or cin[str_a] == 0.:
        return 0.
        
    bbx = cin[str_h] - cin[str_h_d]
    bby = cin[str_a] - cin[str_a_d]
    
    if bbx - bby > 0:
        ax = cin[str_h] - cin[str_h_d]
        ay = cin[str_a] + cin[str_a_d]
        bx = cin[str_h] - cin[str_h_d]
        by = bx
        
    elif bbx - bby < 0:
        ax = cin[str_h] + cin[str_h_d]
        ay = cin[str_a] - cin[str_a_d]
        bx = cin[str_a] - cin[str_a_d]
        by = bx
        
    else:
        return 0.5
    
    cx = ((cin[str_a] + cin[str_a_d]) + (cin[str_h] - cin[str_h_d])*cin[str_a_d]/cin[str_h_d])/(cin[str_a_d]/cin[str_h_d]+1)
    cy = cx    
    a = ((bx - cx) ** 2 + (by - cy) ** 2) ** 0.5
    b = ((ax - cx) ** 2 + (ay - cy) ** 2) ** 0.5
    c = ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5
    p_2 = (a + b + c) / 2
    s = (p_2 * (p_2 - a) * (p_2 - b) * (p_2 - c)) ** 0.5
    h = cin[str_h_d] * cin[str_a_d] * 2 - s
    
    if h + s == 0:
        return 0.5
    elif (bbx - bby )> 0:
        return h / (h + s)
    else:
        return s / (h + s)
    
    
def get_last_str(cin, p_id, dt, n):
    
    
    str_ = get_last_matches(cin, p_id, dt, n).sort_values(by='date', ascending=True)
    str_ = str_.apply(lambda x: swap(x, p_id), axis = 1)
    str_ = str_['str_home'].values

    return str_   

def swap(row, p_id):
    if row['id_player_home'] == p_id:
        return row
    else:
       
        st_h = row['str_home']
        st_a = row['str_away']
        g_h = row['game_home']
        g_a = row['game_away']
        s_h = row['set_home']
        s_a = row['set_away']
         
        row['str_home'] = st_a
        row['str_away'] = st_h
        row['game_home'] = g_a
        row['game_away'] = g_h
        row['set_home'] = s_h 
        row['set_away'] = s_a 
        
        row['result'] = 1 - row['result']   
        row['result_1st_set'] = 1 - row['result_1st_set'] 
        
        return row
def percentage_win(row, cin):
    
    mtch = get_last_matches(cin, row['id_player_home'], row['date'], 20)
    
    if len(mtch) > 0:    
        mtch = mtch.apply(lambda x: swap(x, row['id_player_home']), axis = 1)
        
        row['win_matches_home'] = mtch['result'].sum() / len(mtch)
        row['win_games_home'] = mtch['game_home'].sum() / (mtch['game_home'].sum() + mtch['game_away'].sum())
        row['win_sets_home'] = mtch['set_home'].sum() / (mtch['set_home'].sum() + mtch['set_away'].sum())
        
        if len(mtch.loc[(mtch['result_1st_set'] == 1.)]) > 0:
            row['win_1st_set_lose_home'] =  len(mtch.loc[(mtch['result'] == 0.) & (mtch['result_1st_set'] == 1.)]) / len(mtch.loc[(mtch['result_1st_set'] == 1.)])
            
        if len(mtch.loc[(mtch['result_1st_set'] == 0.)]) > 0:
            row['lose_1st_set_win_home'] =  len(mtch.loc[(mtch['result'] == 1.) & (mtch['result_1st_set'] == 0.)]) / len(mtch.loc[(mtch['result_1st_set'] == 0.)])    
    
    mtch = get_last_matches(cin, row['id_player_away'], row['date'], 20)
    
    if len(mtch) > 0:    
        mtch = mtch.apply(lambda x: swap(x, row['id_player_away']), axis = 1)
        
        row['win_matches_away'] = mtch['result'].sum() / len(mtch)
        row['win_games_away'] = mtch['game_home'].sum() / (mtch['game_home'].sum() + mtch['game_away'].sum())
        row['win_sets_away'] = mtch['set_home'].sum() / (mtch['set_home'].sum() + mtch['set_away'].sum())
        
        
        if len(mtch.loc[(mtch['result_1st_set'] == 1.)]) > 0:
            row['win_1st_set_lose_away'] =  len(mtch.loc[(mtch['result'] == 0.) & (mtch['result_1st_set'] == 1.)]) / len(mtch.loc[(mtch['result_1st_set'] == 1.)])
            
        if len(mtch.loc[(mtch['result_1st_set'] == 0.)]) > 0:
            row['lose_1st_set_win_away'] =  len(mtch.loc[(mtch['result'] == 1.) & (mtch['result_1st_set'] == 0.)]) / len(mtch.loc[(mtch['result_1st_set'] == 0.)])    
            
    #cin['win_after_lose_1st_home']
    #cin['win_after_lose_1st_away']

    return row
  
#cin = cin.loc[(cin['gamma_a_h_surf'] > 0.)  & (cin['gamma_a_a_surf'] > 0.) & (cin['str_away_w'].notnull()) & (cin['str_home_w'].notnull()) & (cin['str_home'].notnull()) & (cin['str_away'].notnull()) & (cin['str_away'] > 0) & (cin['str_away'] > 0) & (cin['result'].notnull()) & (cin['match_status'].isnull()) & (cin['odd_home'] > 1.0) & (cin['odd_away'] > 1.0)]
cin = cin.loc[(cin['result'].notnull()) & (cin['match_status'].isnull()) & (cin['date'] > dateparse('01.09.2015 00:00'))]

#cin = cin.apply(lambda x: percentage_win(x, cin), axis = 1)

cin = cin.loc[(cin['gamma_a_h_surf'] > 0.)  & (cin['gamma_a_a_surf'] > 0.) & (cin['odd_home'] > 1.2) & (cin['odd_away'] > 1.2)]

cin['prob_g'] = cin.apply(lambda x: prob_g(x), axis = 1)
cin['prob_g_rec'] = cin.apply(lambda x: prob_g(x, 1), axis = 1)

cin['d_dif'] = cin['str_home_d'] + cin['str_home_rec_d'] - cin['str_away_d'] - cin['str_away_rec_d'] 

cin['1st_lose_win'] = cin['lose_1st_set_win_home'] - cin['lose_1st_set_win_away']
cin['1st_win_lose'] = cin['win_1st_set_lose_home'] - cin['win_1st_set_lose_away']

def prob_gamma_rec(cin, upd_list, perc = 0.0):
    
    if cin['id_match'] in upd_list:
        
        if cin['gamma_a_h_rec'] == 0. or cin['gamma_scale_h_rec'] == 0. or cin['gamma_a_a_rec'] == 0. or cin['gamma_scale_a_rec'] == 0.:
            return 0.
        
        s = np.random.gamma(cin['gamma_a_h_rec'], cin['gamma_scale_h_rec'], 2000) + cin['gamma_loc_h_rec'] - np.random.gamma(cin['gamma_a_a_rec'], cin['gamma_scale_a_rec'], 2000) - cin['gamma_loc_a_rec']
        r_a, r_loc, r_scale = gamma.fit(s, floc = -4)
        
        return 1 - gamma.cdf(perc, r_a, r_loc, r_scale)
    else:
        return cin['p_gamma_rec']

def prob_gamma_calc(cin, upd_list, pref, suf, res):
    
    if cin['id_match'] in upd_list:
        
        if cin['gamma' + pref + '_a_h' + suf] * cin['gamma' + pref + '_scale_h' + suf] * \
           cin['gamma' + pref + '_a_a' + suf] * cin['gamma' + pref + '_scale_a' + suf] == 0.:
            return 0.
        
        s = np.random.gamma(cin['gamma' + pref + '_a_h' + suf], cin['gamma' + pref + '_scale_h' + suf], 2000) + cin['gamma' + pref + '_loc_h' + suf] - \
            np.random.gamma(cin['gamma' + pref + '_a_a' + suf], cin['gamma' + pref + '_scale_a' + suf], 2000) - cin['gamma' + pref + '_loc_a' + suf]
        r_a, r_loc, r_scale = gamma.fit(s, floc = -8)
        
        return 1 - gamma.cdf(0.0, r_a, r_loc, r_scale)
    else:
        return cin[res]

def a_line(x, cin, pl, n):    
    mtch = get_last_str(cin, pl, x['date'], n)
    if len(mtch) > 1:
        return np.polyfit(list(range(len(mtch))), mtch, 1)[0]
    else:
        return 0.
    
upd_list = cin['id_match'].tolist()    

print('start gamma', datetime.datetime.now())

cin['p_gamma'] = cin.apply(lambda x: prob_gamma_calc(x, upd_list, '', '', 'p_gamma'), axis = 1)

print('done gamma', datetime.datetime.now())

cin['p_gamma_rec'] = cin.apply(lambda x: prob_gamma_calc(x, upd_list, '', '_rec', 'p_gamma_rec'), axis = 1)

print('done gamma_rec', datetime.datetime.now())

cin['p_gamma_surf'] = cin.apply(lambda x: prob_gamma_calc(x, upd_list, '', '_surf', 'p_gamma_surf'), axis = 1)

print('done gamma_surf', datetime.datetime.now())

cin['p_gamma_rec_surf'] = cin.apply(lambda x: prob_gamma_calc(x, upd_list, '', '_rec_surf', 'p_gamma_rec_surf'), axis = 1)

print('done gamma_rec_surf', datetime.datetime.now())

cin['p_gamma_time'] = cin.apply(lambda x: prob_gamma_calc(x, upd_list, '', '_time', 'p_gamma_time'), axis = 1)

print('done gamma_time', datetime.datetime.now())

cin['p_gamma_simple'] = cin.apply(lambda x: prob_gamma_calc(x, upd_list, '_simple', '', 'p_gamma_simple'), axis = 1)

print('done gamma_simple', datetime.datetime.now())

cin['p_gamma_simplest'] = cin.apply(lambda x: prob_gamma_calc(x, upd_list, '_simplest', '', 'p_gamma_simplest'), axis = 1)

print('done gamma_simplest', datetime.datetime.now())

cin['p_gamma_simple_surf'] = cin.apply(lambda x: prob_gamma_calc(x, upd_list, '_simple', '_surf', 'p_gamma_simple_surf'), axis = 1)

print('done gamma_simple_surf', datetime.datetime.now())

cin['p_gamma_simplest_surf'] = cin.apply(lambda x: prob_gamma_calc(x, upd_list, '_simplest', '_surf', 'p_gamma_simplest_surf'), axis = 1)

print('done gamma_simplest_surf', datetime.datetime.now())

cin['p_gamma_rec_p5'] = cin.apply(lambda x: prob_gamma_rec(x, upd_list, perc = 0.05), axis = 1)

cin['p_gamma_rec_m5'] = cin.apply(lambda x: prob_gamma_rec(x, upd_list, perc = -0.05), axis = 1)

cin['a_home'] = 0#cin.apply(lambda x: a_line(x, cin, x['id_player_home'], 8), axis = 1)

print('first a', datetime.datetime.now())

cin['a_away'] = 0#cin.apply(lambda x: a_line(x, cin, x['id_player_away'], 8), axis = 1)

print('upd_done', datetime.datetime.now())

cin['win_perc'] = cin.apply(lambda x: x['win_matches_home'] if x['win_matches_away'] == 0 else x['win_matches_home'] / x['win_matches_away'], axis = 1)
cin['set_perc'] = cin.apply(lambda x: x['win_sets_home'] if x['win_sets_away'] == 0 else x['win_sets_home'] / x['win_sets_away'], axis = 1)
cin['game_perc'] = cin.apply(lambda x: x['win_games_home'] if x['win_games_away'] == 0 else x['win_games_home'] / x['win_games_away'], axis = 1)

print(len(cin))

cin = cin[['id_match','odd_home', 'odd_away', 'date', 'elo', 'elo_recent', 'elo_surf', 'str12', 'str12_rec', 'lose12', 'str_w', 'win12', 'freq_home', 'freq_away', 'fatigue_home', 'fatigue_away', 'prob_g', 'prob_g_rec', 'p_gamma', 'p_gamma_rec', 'p_gamma_surf', 'p_gamma_time', 'set_score', 'match_score', 'result', 'p_gamma_rec_p5', 'p_gamma_rec_m5', 'd_dif', 'win_perc', 'set_perc', 'game_perc', '1st_lose_win', '1st_win_lose', 'p_gamma_simple', 'p_gamma_simplest', 'p_gamma_simple_surf', 'p_gamma_simplest_surf', 'age_dif']]

cin.to_csv('gamma.csv', sep = ';', decimal=",")

seed = 17
test_size = 0.4

x_train, x_test, y_train, y_test = train_test_split(cin[['id_match','odd_home', 'odd_away', 'elo', 'elo_recent', 'elo_surf', 'str12', 'str12_rec', 'lose12', 'prob_g', 'prob_g_rec', 'str_w', 'win12', 'freq_home', 'freq_away', 'fatigue_home', 'fatigue_away', 'p_gamma', 'p_gamma_rec', 'p_gamma_surf', 'p_gamma_time', 'set_score', 'match_score', 'p_gamma_rec_p5', 'p_gamma_rec_m5', 'd_dif', 'win_perc', 'set_perc', 'game_perc', '1st_lose_win', '1st_win_lose', 'p_gamma_simple', 'p_gamma_simplest', 'p_gamma_simple_surf', 'p_gamma_simplest_surf', 'age_dif']], cin['result'], test_size = test_size, random_state = seed)

#x_train = cin.loc[(cin['date'] <  dateparse('01.01.2018 00:00')), ['id_match','odd_home', 'odd_away', 'elo', 'elo_recent', 'elo_surf', 'str12', 'str12_rec', 'lose12', 'prob_g', 'prob_g_rec', 'str_w', 'win12', 'freq_home', 'freq_away', 'fatigue_home', 'fatigue_away', 'p_gamma', 'p_gamma_rec', 'p_gamma_surf', 'p_gamma_time', 'set_score', 'match_score', 'p_gamma_rec_p5', 'p_gamma_rec_m5', 'd_dif', 'win_perc', 'set_perc', 'game_perc', '1st_lose_win', '1st_win_lose', 'p_gamma_simple', 'p_gamma_simplest', 'p_gamma_simple_surf', 'p_gamma_simplest_surf', 'age_dif']]
#x_test  = cin.loc[(cin['date'] >= dateparse('01.01.2018 00:00')), ['id_match','odd_home', 'odd_away', 'elo', 'elo_recent', 'elo_surf', 'str12', 'str12_rec', 'lose12', 'prob_g', 'prob_g_rec', 'str_w', 'win12', 'freq_home', 'freq_away', 'fatigue_home', 'fatigue_away', 'p_gamma', 'p_gamma_rec', 'p_gamma_surf', 'p_gamma_time', 'set_score', 'match_score', 'p_gamma_rec_p5', 'p_gamma_rec_m5', 'd_dif', 'win_perc', 'set_perc', 'game_perc', '1st_lose_win', '1st_win_lose', 'p_gamma_simple', 'p_gamma_simplest', 'p_gamma_simple_surf', 'p_gamma_simplest_surf', 'age_dif']]

#y_train = cin.loc[(cin['date'] <  dateparse('01.01.2018 00:00')), 'result']
#y_test  = cin.loc[(cin['date'] >= dateparse('01.01.2018 00:00')), 'result']


n_est = [2000]
max_d = [8]

predict_columns = ['elo', 'elo_recent', 'elo_surf','prob_g', 'prob_g_rec', 'lose12', 'p_gamma', 'p_gamma_rec', 'p_gamma_surf', 'p_gamma_time', 'set_score', 'match_score', 'p_gamma_rec_p5', 'p_gamma_rec_m5', 'd_dif', 'freq_home', 'freq_away', 'fatigue_home', 'fatigue_away', 'win_perc', 'set_perc', 'game_perc', '1st_lose_win', '1st_win_lose', 'p_gamma_simple', 'p_gamma_simplest', 'p_gamma_simple_surf', 'p_gamma_simplest_surf', 'age_dif']

for ne in n_est:
    for md in max_d:
        model =  RandomForestRegressor(n_estimators=ne, oob_score=True, random_state=1, max_depth = md, n_jobs = -1)
        model.fit(x_train[predict_columns], y_train)
        y_pred_rf = model.predict(x_test[predict_columns])
        
        
        print ("AUC-ROC (oob) = ", roc_auc_score(y_train, model.oob_prediction_), ' ', ne, ' ', md)
        print ("AUC-ROC (test) = ", roc_auc_score(y_test, y_pred_rf), ' ', ne, ' ', md)

    
l_rate = [0.001]
n_est = [2000]
max_d = [6]
confs = [0.6, 0.7, 0.8]
bets = [1.6, 2]

for lr in l_rate:
    for ne in n_est:
        for md in max_d:
                
            model = xgb.XGBClassifier(learning_rate = lr, n_estimators = ne) 
            model.fit(x_train[predict_columns], y_train)        
            y_pred_xgb = model.predict_proba(x_test[predict_columns])
            
            y_pred_xgb = y_pred_xgb[:, 1:2]
            predictions = [np.round(value) for value in y_pred_xgb]
            acc = accuracy_score(y_test, predictions)
            
            for bet_min in bets:
                for conf in confs:
                    profit = 100
                    cnt = 0
                    
                    for i in range(0, len(x_test)):
                        if y_pred_xgb[i] > conf and x_test.iloc[i]['odd_home'] > bet_min:
                            cnt += 1
                            if y_test.iloc[i] == 1:
                                profit += x_test.iloc[i]['odd_home']
                            profit -= 1
                            
                        if y_pred_xgb[i] < 1 - conf and y_pred_xgb[i] > 0. and x_test.iloc[i]['odd_away'] > bet_min:
                            cnt += 1
                            if y_test.iloc[i] == 0:
                                profit += x_test.iloc[i]['odd_away']
                            profit -= 1
                    
                    print("%.4f %.4f %.4f %4d Conf: %.2f Bet min: %.2f Profit: %.2f made %d bets from %d" % (acc, lr, ne, md, conf, bet_min, profit, cnt, len(x_test)))
        
        
feature_importances = pd.DataFrame(model.feature_importances_, index = list(cin[predict_columns].columns), columns=['importance']).sort_values('importance', ascending=False)

print(feature_importances)
  
from sklearn.externals import joblib

joblib.dump(model, "model_xgb.dat")
    
x_test['prediction'] = y_pred_rf
x_test['prediction_xgb'] = y_pred_xgb
x_test['result'] = y_test

profit = 100

profit = 100

for i in range(0, len(x_test)):
    if x_test.iloc[i]['prediction'] > 0.7 and x_test.iloc[i]['odd_home'] > 1.4:
        if x_test.iloc[i]['result'] == 1:
            profit += x_test.iloc[i]['odd_home']
        profit -= 1
        
    if x_test.iloc[i]['prediction'] < 0.3 and x_test.iloc[i]['prediction'] > 0. and x_test.iloc[i]['odd_away'] > 1.4:
        if x_test.iloc[i]['result'] == 0:
            profit += x_test.iloc[i]['odd_away']
        profit -= 1

print('Profit_rf: ', profit)



predict_columns = ['elo', 'elo_recent', 'elo_surf', 'prob_g', 'prob_g_rec', 'lose12', 'p_gamma', 'p_gamma_rec', 'p_gamma_surf', 'p_gamma_time', 'set_score', 'match_score', 'p_gamma_rec_p5', 'p_gamma_rec_m5', 'd_dif', 'freq_home', 'freq_away', 'fatigue_home', 'fatigue_away', 'win_perc', 'set_perc', 'game_perc', '1st_lose_win', '1st_win_lose', 'p_gamma_simple', 'p_gamma_simplest', 'p_gamma_simple_surf', 'p_gamma_simplest_surf', 'age_dif']
model = Sequential()

model.add(Dense(32, input_dim=29, activation='relu'))
model.add(Dense(32, activation='relu'))

model.add(Dense(1, activation='sigmoid'))
# Compile model
model.compile(loss='binary_crossentropy', optimizer='Adam', metrics=['accuracy'])

model.fit(x_train[predict_columns].values, y_train.values, epochs = 400, batch_size = 10)

scores = model.evaluate(x_train[predict_columns], y_train)

y_pred_keras = model.predict_proba(x_test[predict_columns])

print("\n%s: %.2f%%" % (model.metrics_names[1], scores[1]*100))

x_test['prediction_keras'] = y_pred_keras

x_test.to_csv('x_test.csv', sep = ';', decimal=",")

model_json = model.to_json()
with open("model.json", "w") as json_file:
    json_file.write(model_json)
# serialize weights to HDF5
model.save_weights("model.h5")
print("Saved model to disk")


        
    


