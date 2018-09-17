#from sklearn import cross_validation
from sklearn.metrics import accuracy_score
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

import xgboost

from scipy.stats import gamma
import numpy as np

import pandas as pd


dateparse_sec = lambda x: pd.datetime.strptime(x, '%Y-%m-%d %H:%M:%S')

cin = pd.read_csv('cin_elo_.csv', sep=';', parse_dates=['date'], date_parser=dateparse_sec, index_col = 0, decimal=",")



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


def prob_g(cin):

    if cin['str_home'] == 0. or cin['str_away'] == 0.:
        return 0.
        
    bbx = cin['str_home'] - cin['str_home_d']
    bby = cin['str_away'] - cin['str_away_d']
    
    if bbx - bby > 0:
        ax = cin['str_home'] - cin['str_home_d']
        ay = cin['str_away'] + cin['str_away_d']
        bx = cin['str_home'] - cin['str_home_d']
        by = bx
        
    elif bbx - bby < 0:
        ax = cin['str_home'] + cin['str_home_d']
        ay = cin['str_away'] - cin['str_away_d']
        bx = cin['str_away'] - cin['str_away_d']
        by = bx
        
    else:
        return 0.
    
    cx = ((cin['str_away'] + cin['str_away_d']) + (cin['str_home'] - cin['str_home_d'])*cin['str_away_d']/cin['str_home_d'])/(cin['str_away_d']/cin['str_home_d']+1)
    cy = cx    
    a = ((bx - cx) ** 2 + (by - cy) ** 2) ** 0.5
    b = ((ax - cx) ** 2 + (ay - cy) ** 2) ** 0.5
    c = ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5
    p_2 = (a + b + c) / 2
    s = (p_2 * (p_2 - a) * (p_2 - b) * (p_2 - c)) ** 0.5
    h = cin['str_home_d'] * cin['str_away_d'] * 2 - s
    
    if (bbx - bby )> 0:
        return h / (h + s)
    else:
        return s / (h + s)
  
#cin = cin.loc[(cin['gamma_a_h_surf'] > 0.)  & (cin['gamma_a_a_surf'] > 0.) & (cin['str_away_w'].notnull()) & (cin['str_home_w'].notnull()) & (cin['str_home'].notnull()) & (cin['str_away'].notnull()) & (cin['str_away'] > 0) & (cin['str_away'] > 0) & (cin['result'].notnull()) & (cin['match_status'].isnull()) & (cin['odd_home'] > 1.0) & (cin['odd_away'] > 1.0)]
cin = cin.loc[(cin['result'].notnull()) & (cin['match_status'].isnull()) & (cin['gamma_a_h_surf'] > 0.)  & (cin['gamma_a_a_surf'] > 0.)]


cin['prob_g'] = cin.apply(lambda x: prob_g(x), axis = 1)

def prob_gamma(cin, upd_list):
    if cin['id_match'] in upd_list:
        
        if cin['gamma_a_h'] == 0. or cin['gamma_scale_h'] == 0. or cin['gamma_loc_h'] == 0. or cin['gamma_a_a'] == 0. or cin['gamma_scale_a'] == 0. or cin['gamma_loc_a'] == 0.:
            return 0.
        
        s = np.random.gamma(cin['gamma_a_h'], cin['gamma_scale_h'], 2000) + cin['gamma_loc_h'] - np.random.gamma(cin['gamma_a_a'], cin['gamma_scale_a'], 2000) - cin['gamma_loc_a']
        r_a, r_loc, r_scale = gamma.fit(s, floc = -2)
        
        return 1 - gamma.cdf(0.0, r_a, r_loc, r_scale)
    else:
        return cin['p_gamma']

def prob_gamma_rec(cin, upd_list):
    
    if cin['id_match'] in upd_list:
        
        if cin['gamma_a_h_rec'] == 0. or cin['gamma_scale_h_rec'] == 0. or cin['gamma_loc_h_rec'] == 0. or cin['gamma_a_a_rec'] == 0. or cin['gamma_scale_a_rec'] == 0. or cin['gamma_loc_a_rec'] == 0.:
            return 0.
        
        s = np.random.gamma(cin['gamma_a_h_rec'], cin['gamma_scale_h_rec'], 2000) + cin['gamma_loc_h_rec'] - np.random.gamma(cin['gamma_a_a_rec'], cin['gamma_scale_a_rec'], 2000) - cin['gamma_loc_a_rec']
        r_a, r_loc, r_scale = gamma.fit(s, floc = -2)
        
        return 1 - gamma.cdf(0.0, r_a, r_loc, r_scale)
    else:
        return cin['p_gamma_rec']

def prob_gamma_surf(cin, upd_list):
    
    if cin['id_match'] in upd_list:
    
        if cin['gamma_a_h_surf'] == 0. or cin['gamma_scale_h_surf'] == 0. or cin['gamma_loc_h_surf'] == 0. or cin['gamma_a_a_surf'] == 0. or cin['gamma_scale_a_surf'] == 0. or cin['gamma_loc_a_surf'] == 0.:
            return 0.
        
        s = np.random.gamma(cin['gamma_a_h_surf'], cin['gamma_scale_h_surf'], 2000) + cin['gamma_loc_h_surf'] - np.random.gamma(cin['gamma_a_a_surf'], cin['gamma_scale_a_surf'], 2000) - cin['gamma_loc_a_surf']
        r_a, r_loc, r_scale = gamma.fit(s, floc = -2)
        
        return 1 - gamma.cdf(0.0, r_a, r_loc, r_scale)
    else:
        return cin['p_gamma_surf']
    
def prob_gamma_rec_surf(cin, upd_list):
    
    if cin['id_match'] in upd_list:
    
        if cin['gamma_a_h_rec_surf'] == 0. or cin['gamma_scale_h_rec_surf'] == 0. or cin['gamma_loc_h_rec_surf'] == 0. or cin['gamma_a_a_rec_surf'] == 0. or cin['gamma_scale_a_rec_surf'] == 0. or cin['gamma_loc_a_rec_surf'] == 0.:
            return 0.
        
        s = np.random.gamma(cin['gamma_a_h_rec_surf'], cin['gamma_scale_h_rec_surf'], 2000) + cin['gamma_loc_h_rec_surf'] - np.random.gamma(cin['gamma_a_a_rec_surf'], cin['gamma_scale_a_rec_surf'], 2000) - cin['gamma_loc_a_rec_surf']
        r_a, r_loc, r_scale = gamma.fit(s, floc = -2)
        
        return 1 - gamma.cdf(0.0, r_a, r_loc, r_scale)
    else:
        return cin['p_gamma_rec_surf']    
    
def prob_gamma_time(cin, upd_list):
    
    if cin['id_match'] in upd_list:
    
        if cin['gamma_a_h_time'] == 0. or cin['gamma_scale_h_time'] == 0. or cin['gamma_loc_h_time'] == 0. or cin['gamma_a_a_time'] == 0. or cin['gamma_scale_a_time'] == 0. or cin['gamma_loc_a_time'] == 0.:
            return 0.
        
        s = np.random.gamma(cin['gamma_a_h_time'], cin['gamma_scale_h_time'], 2000) + cin['gamma_loc_h_time'] - np.random.gamma(cin['gamma_a_a_time'], cin['gamma_scale_a_time'], 2000) - cin['gamma_loc_a_time']
       
        r_a, r_loc, r_scale = gamma.fit(s, floc = -2.01)
        
        return 1 - gamma.cdf(0.0, r_a, r_loc, r_scale)
    else:
        return cin['p_gamma_time']  
    
upd_list = cin['id_match'].tolist()    

for col in ['p_gamma', 'p_gamma_rec', 'p_gamma_surf', 'p_gamma_rec_surf', 'p_gamma_time']:
    cin[col] = 0.

print('start gamma')
cin['p_gamma'] = cin.apply(lambda x: prob_gamma(x, upd_list), axis = 1)
print('done gamma')
cin['p_gamma_rec'] = cin.apply(lambda x: prob_gamma_rec(x, upd_list), axis = 1)
print('done gamma_rec')
cin['p_gamma_surf'] = cin.apply(lambda x: prob_gamma_surf(x, upd_list), axis = 1)
print('done gamma_surf')
cin['p_gamma_rec_surf'] = cin.apply(lambda x: prob_gamma_rec_surf(x, upd_list), axis = 1)
print('done gamma_rec_surf')
cin['p_gamma_time'] = cin.apply(lambda x: prob_gamma_time(x, upd_list), axis = 1)
print('done gamma_surf')






print(len(cin))

cin = cin[['id_match','odd_home', 'odd_away',  'elo', 'elo_recent', 'elo_surf', 'str12', 'str12_rec', 'lose12', 'str_w', 'win12', 'freq_home', 'freq_away', 'fatigue_home', 'fatigue_away', 'prob_g', 'p_gamma', 'p_gamma_rec', 'p_gamma_surf', 'p_gamma_time', 'set_score', 'match_score', 'result']]

cin.to_csv('gamma.csv', sep = ';', decimal=",")

seed = 8
test_size = 0.2

x_train, x_test, y_train, y_test = train_test_split(cin[['id_match','odd_home', 'odd_away', 'elo', 'elo_recent', 'elo_surf', 'str12', 'str12_rec', 'lose12', 'prob_g', 'str_w', 'win12', 'freq_home', 'freq_away', 'fatigue_home', 'fatigue_away', 'p_gamma', 'p_gamma_rec', 'p_gamma_surf', 'p_gamma_time', 'set_score', 'match_score']], cin['result'], test_size = test_size, random_state = seed)

n_est = [800]
max_d = [8]

predict_columns = ['prob_g', 'elo', 'elo_surf', 'lose12', 'str_w', 'win12', 'p_gamma', 'p_gamma_rec', 'p_gamma_surf', 'p_gamma_time', 'set_score', 'match_score']

for ne in n_est:
    for md in max_d:
        model =  RandomForestRegressor(n_estimators=ne, oob_score=True, random_state=1, max_depth = md, n_jobs = -1)
        model.fit(x_train[predict_columns], y_train)
        y_pred_rf = model.predict(x_test[predict_columns])
        
        
        print ("AUC-ROC (oob) = ", roc_auc_score(y_train, model.oob_prediction_), ' ', ne, ' ', md)
        print ("AUC-ROC (test) = ", roc_auc_score(y_test, y_pred_rf), ' ', ne, ' ', md)

    
l_rate = [0.001, 0.005, 0.01, 0.02, 0.04]
n_est = [800, 2000, 4000, 8000]
max_d = [4, 5, 6, 7, 8, 13]

for lr in l_rate:
    for ne in n_est:
        for md in max_d:
            model = xgboost.XGBClassifier(learning_rate = lr, n_estimators = ne, max_depth = md) 
            model.fit(x_train[predict_columns], y_train)        
            y_pred_xgb = model.predict_proba(x_test[predict_columns])
            
            y_pred_xgb = y_pred_xgb[:, 1:2]
            predictions = [np.round(value) for value in y_pred_xgb]
            acc = accuracy_score(y_test, predictions)
            print("%.4f %f %f %f" % (acc, lr, ne, md))
        
        
feature_importances = pd.DataFrame(model.feature_importances_, index = list(cin[predict_columns].columns), columns=['importance']).sort_values('importance', ascending=False)

print(feature_importances)
      

x_test['prediction'] = y_pred_rf
x_test['prediction_xgb'] = y_pred_xgb
x_test['result'] = y_test


x_test.to_csv('x_test.csv', sep = ';', decimal=",")
