from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), unique=True, nullable=False)
    elo = db.Column(db.Integer, default=800)
    n_games = db.Column(db.Integer, default=0)
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)
    win_streak = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)
    goals_conceded = db.Column(db.Integer, default=0)
    wins_as_red = db.Column(db.Integer, default=0)
    wins_as_blue = db.Column(db.Integer, default=0)

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    winner_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    loser_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    score_winner = db.Column(db.Integer, nullable=False)
    score_loser = db.Column(db.Integer, nullable=False)
    winner_color = db.Column(db.String(10), nullable=False)
    loser_color = db.Column(db.String(10), nullable=False)

class BeltHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    match_id_ref = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=True)