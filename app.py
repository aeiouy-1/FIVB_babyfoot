from flask import Flask, render_template, request, redirect, url_for, session, flash
from config import Config
from models import db, Player, Match, BeltHistory
from utils import calc_elo
from datetime import datetime
from collections import Counter

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/')
def accueil():
    actif = request.args.get('actifs', '1') == '1'
    joueurs_query = Player.query.filter_by(active=True) if actif else Player.query
    joueurs = joueurs_query.order_by(Player.elo.desc()).all()
    last_belt = BeltHistory.query.order_by(BeltHistory.date.desc()).first()
    champion_id = last_belt.player_id if last_belt else None
    return render_template('accueil.html', joueurs=joueurs, actifs=actif, champion_id=champion_id)

if __name__ == '__main__':
    app.run(debug=True)
