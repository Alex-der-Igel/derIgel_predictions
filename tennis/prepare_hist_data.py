import pandas as pd


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


print(get_stage('French Open (France), clay - 1/16-finals', ''))
print(get_stage('Basel (Switzerland), hard (indoor) - Quarter-finals', ''))
print(get_stage('Hurlingham (United Kingdom), grass', ''))
print(get_stage('Davis Cup - World Group (World)', ''))

dateparse = lambda x: pd.datetime.strptime(x, '%d.%m.%Y %H:%M')

cin = pd.read_csv('data/matches.csv',  # Это то, куда вы скачали файл
                       sep=';', 
                       parse_dates=['date'], date_parser=dateparse, index_col='Unnamed: 0')

cin_st = pd.read_csv('data/match_stats.csv',  # Это то, куда вы скачали файл
                       sep=';', 
                       index_col='Unnamed: 0')
cin_st['set_home'] = cin_st.apply(lambda x: 1 if x['game_home'] > x['game_away'] else 0, axis = 1)
cin_st['set_away'] = cin_st.apply(lambda x: 0 if x['game_home'] > x['game_away'] else 1, axis = 1)

cin['surf'] = cin.apply(lambda x: get_surf(x['tournament']), axis = 1)
cin['stage'] = cin.apply(lambda x: get_stage(x['tournament'], x['tournament_link']), axis = 1)


cin.to_csv('cin_n.csv', sep = ';')


cin_st = cin_st[['id_match', 'game_home','game_away', 'set_home', 'set_away', 'set_duration']].groupby(['id_match']).sum()



t_h = cin.loc[cin['id_match'] == 'by8oXmyh'].iloc[0]['id_player_home']
t_a = cin.loc[cin['id_match'] == 'by8oXmyh'].iloc[0]['id_player_away']
t_m = cin.loc[cin['id_match'] == 'by8oXmyh'].iloc[0]['date']

print(t_h, ' ', t_a, ' ', t_m)


prev_h = cin.loc[((cin['id_player_home'] == t_a) | (cin['id_player_away'] == t_a)) & (cin['date'] < t_m) , ['id_match', 'id_player_home', 'id_player_away', 'date']].sort_values(by='date', ascending=False)[0:8]

#print(prev_h[['id_player_home', 'id_player_away', 'date']])

prev_h = pd.merge(prev_h, cin_st, left_on=  ['id_match'],
                                  right_on= ['id_match'],
                                  how = 'left')


prev_h['game_t_a'] = prev_h.apply(lambda x: x['game_home'] if x['id_player_home'] == t_a else x['game_away'], axis = 1)


print(prev_h)
prev_h.to_csv('prev_h.csv', sep = ';')
