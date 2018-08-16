#from sklearn import cross_validation
from sklearn.metrics import accuracy_score
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt



dateparse_sec = lambda x: pd.datetime.strptime(x, '%Y-%m-%d %H:%M:%S')

cin = pd.read_csv('data/cin_elo_serv.csv', sep=';', parse_dates=['date'], date_parser=dateparse_sec, index_col = 0)

cin = cin.loc[(cin['str_home'].notnull()) & (cin['str_away'].notnull()) & (cin['str_away'] > 0) & (cin['str_away'] > 0) & (cin['result'].notnull()) & (cin['match_status'].isnull()) & (cin['odd_home'] > 1.19) & (cin['odd_away'] > 1.19)]
print(len(cin))

cin['elo'] = 1 / (1 + 10 ** ((cin['elo_away'] - cin['elo_home']) / 400))
cin['elo_recent'] = 1 / (1 + 10 ** ((cin['elo_rec_away'] - cin['elo_rec_home']) / 400))
cin['elo_surf'] = 1 / (1 + 10 ** ((cin['elo_surf_away'] - cin['elo_surf_home']) / 400))

cin['str12'] = cin['str_home'] - cin['str_away']
cin['str12_rec'] = cin['str_home_rec'] - cin['str_away_rec']
cin['lose12'] = cin['l_home'] - cin['l_away']




def prob_g(cin):

    bbx = cin['str_home'] - cin['str_home_d']
    bby = cin['str_home'] - cin['str_home_d']
    
    if bbx - bby > 0:
        ax = cin['str_home'] - cin['str_home_d']
        ay = cin['str_away'] + cin['str_away_d']
        bx = cin['str_home'] - cin['str_home_d']
        by = bx
        
    else:
        ax = cin['str_home'] + cin['str_home_d']
        ay = cin['str_away'] - cin['str_away_d']
        bx = cin['str_away'] - cin['str_away_d']
        by = bx
        
    
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
    
cin['prob_g'] = cin.apply(lambda x: prob_g(x), axis = 1)

cin = cin[['id_match','odd_home', 'odd_away',  'elo', 'elo_recent', 'elo_surf', 'str12', 'str12_rec', 'lose12', 'result', 'prob_g']]

#y = np.array(cin['result'])
#
#cin = cin.drop('result', axis = 1)
#
#x_list = list(cin.columns)
#x = np.array(cin[['elo', 'elo_recent', 'elo_surf', 'str12', 'str12_rec', 'lose12']])
#

seed = 8
test_size = 0.4

x_train, x_test, y_train, y_test = train_test_split(cin[['id_match','odd_home', 'odd_away', 'elo', 'elo_recent', 'elo_surf', 'str12', 'str12_rec', 'lose12', 'prob_g']], cin['result'], test_size = test_size, random_state = seed)

n_est = [800]
max_d = [8]

predict_columns = ['prob_g', 'elo', 'elo_recent', 'elo_surf', 'str12', 'str12_rec', 'lose12']

for ne in n_est:
    for md in max_d:
        model =  RandomForestRegressor(n_estimators=ne, oob_score=True, random_state=1, max_depth = md, n_jobs = -1)
        model.fit(x_train[predict_columns], y_train)
        y_pred_rf = model.predict(x_test[predict_columns])
        
        
        print ("AUC-ROC (oob) = ", roc_auc_score(y_train, model.oob_prediction_), ' ', ne, ' ', md)
        print ("AUC-ROC (test) = ", roc_auc_score(y_test, y_pred_rf), ' ', ne, ' ', md)
        
        
        
feature_importances = pd.DataFrame(model.feature_importances_, index = list(cin[predict_columns].columns), columns=['importance']).sort_values('importance', ascending=False)

print(feature_importances)
      

x_test['prediction'] = y_pred_rf
x_test['result'] = y_test


x_test.to_csv('x_test.csv', sep = ';')
