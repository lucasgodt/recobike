from flask import Flask, request
from flask_restful import Resource, Api
from json import dumps
from flask.ext.jsonpify import jsonify
import pandas as pd
import numpy as np

app = Flask(__name__)
api = Api(app)

#carrega os csvs do dataset
csv = pd.read_csv('go_track_tracks.csv')

ratings = csv[['id_android','id','rating']]

csvt = pd.read_csv('go_track_trackspoints.csv')

tracks = csvt[['track_id','latitude','longitude']]

#carrega o csv gerado por update.py
R_df = pd.read_csv('matrix.csv',header=0,index_col=0)
#Transforma o dataframe do pandas em uma matriz numpy para se realizar os cálculos e a normalização
R = R_df.as_matrix().astype(np.int64)

user_ratings_mean = np.mean(R, axis = 1)

R_demeaned = R - user_ratings_mean.reshape(-1, 1)

from scipy.sparse.linalg import svds
U, sigma, Vt = svds(R_demeaned, k = 25)

sigma = np.diag(sigma)

all_user_predicted_ratings = np.dot(np.dot(U, sigma), Vt) + user_ratings_mean.reshape(-1, 1)
preds_df = pd.DataFrame(all_user_predicted_ratings, columns = R_df.columns.astype(np.int64))

def recommend_tracks(predictions_df, userID, tracks, original_ratings_df, num_recommendations=5):
    
    # Pego as previsões e as ordena
    sorted_user_predictions = predictions_df.iloc[userID].sort_values(userID,ascending=False)
    
    # Pega os dados do usuário
    user_data = original_ratings_df[original_ratings_df.id_android == (userID)]

    # Recomenda as trajetorias com as avaliações mais altas e que ainda não foram previstas
    User = pd.DataFrame(sorted_user_predictions).reset_index()
    UserResult = User.rename(columns={'index': 'id'})
    recommendations = (original_ratings_df[~original_ratings_df['id'].isin(user_data['id'])].merge(UserResult, how = 'left',
               left_on = 'id', right_on = 'id').sort_values(userID, ascending = False).iloc[:num_recommendations, :-1])

    return user_data, recommendations

#inicio da api

class UserTracks(Resource):
    #retorna os trajetos realizados por um usuario
    def get(self, user_id):
        ident = [int(user_id)]
        usertrajs = ratings[ratings['id_android']==ident]
        trajetorias = []
        for trajeto in usertrajs['id']:
            trajetoria = tracks[tracks['track_id']==trajeto]
            traj = trajetoria[['latitude','longitude']].values.tolist()
            trajetorias.append(traj)
        
        return jsonify(trajetorias)
    
    def post(self, user_id):
        #realiza post de novas trajetorias de usuarios
        return 1

class Track_Recommendation(Resource):
    #Faz a previsão de uma trajetoria para um usuario
    def get(self, user_id):
        ident = [int(user_id)]
        already_rated, previsoes = recommend_tracks(preds_df, ident, tracks, ratings, 1)
        trajetoria = tracks[tracks['track_id']==previsoes['id'].values[0]]
        traj = trajetoria[['latitude','longitude']].values.tolist()
        return jsonify(traj)
    

api.add_resource(UserTracks, '/usertracks/<user_id>') # Rota_1
api.add_resource(Track_Recommendation, '/recommend/<user_id>') # Rota_2

if __name__ == '__main__':
     app.run(port='5002')
