from flask import Flask, request, render_template
from flask_restful import Resource, Api
from flask_jsonpify import jsonify
from flask_cors import CORS, cross_origin
import pandas as pd
import numpy as np
#from models import db, Tracks, TrackPoints
from sqlalchemy import create_engine
from sqlalchemy.sql import table, column

### 1 - DESENVOLVER OS POSTS COM A ENGINE NOVAMENTE
### 2 - (FEITO)ATUALIZAR update.py PARA GERAR A MATRIX E A ATUALIZAR NO BANCO DE DADOS À PARTIR DO LOCAL
### 3 - ATUALIZAR o database do heroku PARA NAO DAR PAU NA APRESENTACAO


engine = create_engine("postgres://tncxxisbtfhrno:1fd5d25a7d85e5e9dbdc6b6b3d299d933fb6c25697b563a2caa2dc9a93757c35@ec2-54-83-49-44.compute-1.amazonaws.com:5432/da608cod3ci82f")
conn = engine.connect()
pointstable = table('trackspointstable', column('track_id'), column('latitude'), column('longitude'))
trackstable = table('trackstable', column('id_android'), column('id'), column('rating'))
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
api = Api(app)
 

#Para implementar os posts
#fields_tracks = ['id','latitude','longitude','track_id','time']
#fields_users = ['id','id_android','speed','time','distance','rating','rating_bus','rating_weather','car_or_bus','linha']

#carrega os csvs do dataset
#csv = pd.read_csv('go_track_tracks.csv') nao mais

#ratings = csv[['id_android','id','rating']]nao mais

#carrega os df do database

tracks_df = pd.read_sql_query('select * from "trackstable"',con=engine)

ratings = tracks_df[['id_android','id','rating']]

#csvt = pd.read_csv('go_track_trackspoints.csv')

#tracks = csvt[['track_id','latitude','longitude']]

trackspoints_df = pd.read_sql_query('select * from "trackspointstable"',con=engine)

tracks = trackspoints_df[['track_id','latitude','longitude']]

#carrega o csv gerado por update.py
R_df_primario = pd.read_sql_query('select * from "matrixtable"',con=engine)

R_df = R_df_primario.drop(['id_android'],axis=1)
#R_df = pd.read_csv('matrix.csv',header=0,index_col=0) nao mais
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
        print(coordenada)
        ins = pointstable.insert().values(track_id = input_json["$trackId"], latitude = coordenada['latitude'],longitude = coordenada['longitude'])
        #INSERT INTO users (id, name, fullname) VALUES (:id, :name, :fullname)
        conn.execute(ins)
        #track = trackspointstable(id_track = input_json["$trackId"] ,latitude = coordenada['latitude'], longitude = coordenada['longitude'])
        #INSERT [INTO] table_or_view [(column_list)] data_values
#            db.session.add(track);
#            db.session.commit();
        #colocar no db
        #addLine(argumentos_tracks,'go_track_trackpoints.csv')
        
    # adiciona um novo percurso e avaliacao aos usuários
    ins2 = trackstable.insert().values(id_android = input_json["androidId"], id = input_json["$trackId"], rating = input_json["trackRating"])
    conn.execute(ins2)
    #fields_users = ['id','id_android','speed','time','distance','rating','rating_bus','rating_weather','car_or_bus','linha']
#    user_rides = Tracks(id_android = input_json["userId"],id_track = input_json["$trackId"],rating = input_json["trackRating"]);
#    db.session.add(user_rides);
#    db.session.commit();
    #colocar no db
    #addLine(argumentos_users,'go_track_tracks.csv')
                            
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
