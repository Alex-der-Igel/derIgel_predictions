import pandas as pd


dateparse = lambda x: pd.datetime.strptime(x, '%d.%m.%Y %H:%M')

cin = pd.read_csv('matches.csv',  # Это то, куда вы скачали файл
                       sep=';', 
                       parse_dates=['date'], date_parser=dateparse, index_col='Unnamed: 0')

cin_st = pd.read_csv('match_stats.csv',  # Это то, куда вы скачали файл
                       sep=';', 
                       index_col='Unnamed: 0')
cin_st['set_home'] = cin_st.apply(lambda x: 1 if x['game_home'] > x['game_away'] else 0, axis = 1)
cin_st['set_away'] = cin_st.apply(lambda x: 0 if x['game_home'] > x['game_away'] else 1, axis = 1)

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
