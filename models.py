#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec  3 01:59:16 2017

@author: lucas
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)

class Tracks(db.Model):
    id_ride = db.Column(db.Integer, primary_key=True)
    id_android = db.Column(db.String(80), primary_key=False)
    id_track = db.Column(db.String(80), unique=True, nullable=False)
    rating = db.Column(db.Integer, unique=False, nullable=True)

    def __repr__(self):
        return '<User %r>' % self.username
    
class TrackPoints(db.Model):
    id_point = db.Column(db.Integer, primary_key=True)
    id_track = db.Column(db.String(80), primary_key=False)
    latitude = db.Column(db.Integer, unique=False, nullable=False)
    longitude = db.Column(db.Integer, unique=False, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username