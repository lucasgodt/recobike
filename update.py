import pandas as pd
from fastdtw import fastdtw
from collections import OrderedDict
from scipy.spatial.distance import euclidean
from sqlalchemy import create_engine

engine = create_engine("postgres://tncxxisbtfhrno:1fd5d25a7d85e5e9dbdc6b6b3d299d933fb6c25697b563a2caa2dc9a93757c35@ec2-54-83-49-44.compute-1.amazonaws.com:5432/da608cod3ci82f")

#para transformar o csv em uma tabela
#a=pd.read_csv("go_track_tracks.csv")
#a.to_sql('trackstable',engine,if_exists='replace')
#
tracks_df = pd.read_sql_query('select * from "trackstable"',con=engine)

#csv = pd.read_csv('go_track_tracks.csv') nao mais

#ratings = csv[['id_android','id','rating']] nao mais

ratings = tracks_df[['id_android','id','rating']]

#paraos trackpoints
#b=pd.read_csv("go_track_trackspoints.csv")
#b.to_sql('trackspointstable',engine,if_exists='replace')

#csvt = pd.read_csv('go_track_trackspoints.csv') nao mais

trackspoints_df = pd.read_sql_query('select * from "trackspointstable"',con=engine)

tracks = trackspoints_df[['track_id','latitude','longitude']]

R_df = ratings.pivot(index = 'id_android', columns ='id', values = 'rating').fillna(0)

#calcula a similaridade entre duas trajetórias
def similaridade(traj_1,traj_2):
        
    trau1 = traj_1[['latitude','longitude']]
    trau2 = traj_2[['latitude','longitude']]
    distance, path = fastdtw(trau1, trau2, dist=euclidean)
    return distance

#retorna um dicionario com as trajetórias ordenadas por similaridade à trajetória alvo
def ordenaSimilaridade(trajetoria_alvo):
    
    dict = {}
    
    for trajeto in ratings['id']:
        
        trajetoria2 = tracks[tracks['track_id']==trajeto]
        dict[trajeto] = similaridade(trajetoria_alvo,trajetoria2)
    
    return OrderedDict(sorted(dict.items(), key=lambda t: t[1]))

#Atualiza os ratings de um usuário, os prevendo de acordo com a as trajetórias mais similares às trajetórias avaliadas pelo mesmo
def updateUserRatings(user, R):
    
    series = R.loc[user]
    rated = series[series >= 2]
    for idx,rating in enumerate(rated):
        dicSim = ordenaSimilaridade(tracks[tracks['track_id']==rated.index[idx]])
        for track in dicSim.items():
            if  ((track[1]>0.3) and (R_df.loc[user].loc[track[0]]<5)):
            #Desenvolver método para similaridade das características das rotas
            #A avaliação prevista é a média das avaliações dos trajetos similares
            #if similaridade do trajeto menor que 0.5, então
            #   prevê avaliação pela média das avaliações dos itens similares
                R_df.loc[user].loc[track[0]]+=(1/track[1])

                        
#Prevê ratings para todos os usuários
def updateMatrix():
    for index, row in R_df.iterrows(): 
        updateUserRatings(index, R_df)
        
updateMatrix()

#R_df.to_csv('matrix.csv',header = R_df.columns)
R_df.to_sql('matrixtable',engine,if_exists='replace')


