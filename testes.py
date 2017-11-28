#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 16:28:08 2017

@author: lucas
"""
import graphlab as gl
from scipy.spatial.distance import euclidean
from fastdtw import fastdtw
from collections import OrderedDict
#carrega o dataset
trajetorias = gl.SFrame.read_csv('go_track_trackspoints.csv')
usuarios = gl.SFrame.read_csv('go_track_tracks.csv')
usuarios.rename({'id': 'track_id'})

#dividi o dataset em dados de treino e de validacao utilizando as colunas 0,1 e 2 do dataset
training_data, validation_data = gl.recommender.util.random_split_by_user(usuarios,user_id='id_android', item_id='track_id', max_num_users=100000, item_test_proportion=0.1, random_seed=0)

trajetoria_usuario1 = trajetorias[trajetorias['track_id']==1]
trajetoria_usuario1_2 = trajetorias[trajetorias['track_id']==2]
trajetoria_usuario1_3 = trajetorias[trajetorias['track_id']==8]
trajetoria_usuario2 = trajetorias[trajetorias['track_id']==37989]

#trajetoria_recomendada = training_data[training_data['id'] == recomendacoes['id']]


#calculando a distância entre duas trajetórias utilizando Dynamic Time Warping
def similaridade(traj_1,traj_2):
        
    trau1 = traj_1[['latitude','longitude']].to_numpy()
    trau2 = traj_2[['latitude','longitude']].to_numpy()
    distance, path = fastdtw(trau1, trau2, dist=euclidean)
    return distance
#ADICIONAR A DISTÂNCIA NO DATASET PARA SER UTILIZADA COMO ATRIBUTO
#OPENSTREETMAP?

#cria o modelo treinado
model = gl.recommender.item_similarity_recommender.create(training_data, user_id='id_android', item_id='track_id',user_data=training_data[['id_android','time','distance']], item_data=trajetorias[['latitude','longitude','track_id']], similarity_type='jaccard')
#model = gl.recommender.ranking_factorization_recommender.create(training_data, user_id='id_android', item_id='track_id', user_data=training_data[['id_android','speed','time','distance']], item_data=trajetorias[['latitude','longitude','track_id']])
model.save("modeloRecomendacaoSimilaridade")
users = [6]
recomendacoes = model.recommend(users,k=1)
similar_items = model.get_similar_items(training_data['track_id'], k=20)

print(similaridade(trajetoria_usuario1,trajetoria_usuario2))

#retorna um dicionario com as trajetórias ordenadas por similaridade à trajetória alvo
def ordenaSimilaridade(trajetoria_alvo):
    
    dict = {}
    
    for trajeto in usuarios:
        
        trajetoria2 = trajetorias[trajetorias['track_id']==trajeto['track_id']]
        dict[trajeto['track_id']] = similaridade(trajetoria_alvo,trajetoria2)
    
    return OrderedDict(sorted(dict.items(), key=lambda t: t[1]))
    
#plotando as trajetórias no mapa
import gmplot

gmap = gmplot.GoogleMapPlotter(-10.9395848167205, -37.0597757046112, 16)
gmap.plot(trajetoria_usuario1['latitude'],trajetoria_usuario1['longitude'], 'cornflowerblue', edge_width=5)
gmap.plot(trajetoria_usuario1_2['latitude'],trajetoria_usuario1['longitude'], 'cornflowerblue', edge_width=5)
gmap.plot(trajetoria_usuario1_3['latitude'],trajetoria_usuario1['longitude'], 'cornflowerblue', edge_width=5)
gmap.plot(trajetoria_usuario2['latitude'],trajetoria_usuario2['longitude'], 'red', edge_width=5)
#gmap.plot(trajetoria_recomendada['latitude'],trajetoria_recomendada['longitude'], 'red', edge_width=5)
gmap.draw("meumap.html")

