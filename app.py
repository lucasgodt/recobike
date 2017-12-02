from flask import Flask, request, render_template
from flask_restful import Resource, Api
from json import dumps
from flask_jsonpify import jsonify
from flask_cors import CORS, cross_origin
import pandas as pd
import numpy as np
from addcsv import addLine

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
api = Api(app)

#Para implementar os posts
#fields_tracks = ['id','latitude','longitude','track_id','time']
#fields_users = ['id','id_android','speed','time','distance','rating','rating_bus','rating_weather','car_or_bus','linha']

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
@app.route('/')
@cross_origin()
def static_page():
    #Pagina principal da api
    return render_template('index.html')

@app.route('/novatrack', methods=['POST'])
def novatrack():
    input_json = request.get_json(force=True); 
    # force=True, above, is necessary if another developer 
    # forgot to set the MIME type to 'application/json'

    # adiciona uma nova track aos dados
    json_coordenadas = input_json["coordenadas"];
    for coordenada in json_coordenadas:
        #print(coordenada)
        #fields_tracks = ['id','latitude','longitude','track_id','time']
        argumentos_tracks = [input_json["$trackId"],coordenada['latitude'],coordenada['longitude']]
        addLine(argumentos_tracks,'/tmp/go_track_trackpoints.csv')
        
    # adiciona um novo percurso e avaliacao aos usuários
    print(input_json["userId"])
    #fields_users = ['id','id_android','speed','time','distance','rating','rating_bus','rating_weather','car_or_bus','linha']
    argumentos_users = [input_json["$trackId"],input_json["userId"],0,0,0,input_json["trackRating"]];
    addLine(argumentos_users,'/tmp/go_track_tracks.csv')
                            
    dictToReturn = {'resposta':'Deu certo'}
    return jsonify(dictToReturn)

#@app.route('/usertracks/<user_id>')
#@cross_origin()
class User_Tracks(Resource):
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
    
#@cross_origin()
class Track_Recommendation(Resource):
    #Faz a previsão de uma trajetoria para um usuario
    def get(self, user_id):
            ident = [int(user_id)]
            already_rated, previsoes = recommend_tracks(preds_df, ident, tracks, ratings, 1)
            trajetoria = tracks[tracks['track_id']==previsoes['id'].values[0]]
            traj = trajetoria[['latitude','longitude']].values.tolist()
            return jsonify(traj)
    

        
api.add_resource(User_Tracks, '/usertracks/<user_id>') # Rota_1
api.add_resource(Track_Recommendation, '/recommend/<user_id>') # Rota_2

if __name__ == '__main__':
     app.run(port='5002')
