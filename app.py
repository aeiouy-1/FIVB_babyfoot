from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from config import Config
from models import db, Player, Match, BeltHistory
from utils import calc_elo
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
with app.app_context():
    db.create_all()

# --- Routes publiques ---

@app.route('/')
def accueil():
    actif = request.args.get('actifs', '1') == '1'
    joueurs_query = Player.query.filter_by(active=True) if actif else Player.query
    joueurs = joueurs_query.order_by(Player.elo.desc()).all()
    last_belt = BeltHistory.query.order_by(BeltHistory.date.desc()).first()
    champion_id = last_belt.player_id if last_belt else None
    return render_template('accueil.html', joueurs=joueurs, actifs=actif, champion_id=champion_id)

@app.route('/joueur/<int:player_id>')
def profil_joueur(player_id):
    joueur = Player.query.get_or_404(player_id)
    matchs = Match.query.filter(
        (Match.winner_id==player_id) | (Match.loser_id==player_id)
    ).order_by(Match.date.asc()).all()

    # 1. Statistiques de base
    total_matches = joueur.wins + joueur.losses
    win_pct = (joueur.wins / total_matches * 100) if total_matches else 0

    # 2. Moyenne buts encaissés
    total_goals_conceded = sum(
        m.score_loser if m.winner_id==player_id else m.score_winner for m in matchs
    )
    avg_goals_conceded = (total_goals_conceded / total_matches) if total_matches else 0

    # 3. Win % par couleur
    plays_red = plays_blue = wins_red = wins_blue = 0
    for m in matchs:
        if m.winner_id == player_id:
            if m.winner_color == 'rouge':
                wins_red += 1; plays_red += 1
            else:
                wins_blue += 1; plays_blue += 1
        else:
            # joueur est perdant
            if m.loser_color == 'rouge': plays_red += 1
            else: plays_blue += 1
    win_pct_red = (wins_red / plays_red * 100) if plays_red else 0
    win_pct_blue = (wins_blue / plays_blue * 100) if plays_blue else 0

    # 4. Moyenne ELO adversaires
    elo_wins = [Player.query.get(m.loser_id).elo for m in matchs if m.winner_id==player_id]
    elo_losses = [Player.query.get(m.winner_id).elo for m in matchs if m.loser_id==player_id]
    avg_elo_win = sum(elo_wins)/len(elo_wins) if elo_wins else 0
    avg_elo_loss = sum(elo_losses)/len(elo_losses) if elo_losses else 0

    # 5. Rivalités
    from collections import Counter
    opponents = [ (m.loser_id if m.winner_id==player_id else m.winner_id) for m in matchs ]
    freq = Counter(opponents)
    rival_id, rival_count = freq.most_common(1)[0] if freq else (None, 0)
    rival_name = Player.query.get(rival_id).nom if rival_id else ''

    # 6. Adversaire le plus difficile
    losses = [m.winner_id for m in matchs if m.loser_id==player_id]
    loss_freq = Counter(losses)
    hard_id, hard_losses = loss_freq.most_common(1)[0] if loss_freq else (None, 0)
    hard_wins = Counter([m.loser_id for m in matchs if m.winner_id==player_id]).get(hard_id, 0)
    hard_name = Player.query.get(hard_id).nom if hard_id else ''

    # 7. Adversaire favori
    wins = [m.loser_id for m in matchs if m.winner_id==player_id]
    win_freq = Counter(wins)
    fav_id, fav_wins = win_freq.most_common(1)[0] if win_freq else (None, 0)
    fav_losses = Counter([m.winner_id for m in matchs if m.loser_id==player_id]).get(fav_id, 0)
    fav_name = Player.query.get(fav_id).nom if fav_id else ''

    # Préparer historique ELO pour Chart.js
    from utils import expected_score
    labels, data = [], []
    elo = 800
    for idx, m in enumerate(matchs, start=1):
        if m.winner_id == player_id:
            elo = calc_elo(elo, 0, m.score_winner, m.score_loser)[0]
        else:
            elo = calc_elo(0, elo, m.score_winner, m.score_loser)[1]
        labels.append(idx); data.append(elo)

    return render_template('joueur.html',
        joueur=joueur,
        win_pct=win_pct,
        win_pct_red=win_pct_red,
        win_pct_blue=win_pct_blue,
        avg_goals_conceded=avg_goals_conceded,
        avg_elo_win=avg_elo_win,
        avg_elo_loss=avg_elo_loss,
        rival_name=rival_name,
        rival_count=rival_count,
        hard_name=hard_name,
        hard_wins=hard_wins,
        hard_losses=hard_losses,
        fav_name=fav_name,
        fav_wins=fav_wins,
        fav_losses=fav_losses,
        elo_labels=labels,
        elo_data=data
    )
# --- Route Hall of Fame ---
@app.route('/hall-of-fame')
def hall_of_fame():
    return render_template('hall_of_fame.html')


# --- Route Règles ---
@app.route('/regles')
def page_regles():
    return render_template('regles.html')

# --- Route Tournoi Annuel ---
@app.route('/tournoi-annuel')
def page_tournoi():
    return render_template('tournoi_annuel.html')

# --- Route Ceinture ---
@app.route('/ceinture')
def page_ceinture():
    return render_template('ceinture.html')


# --- Auth Admin ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        mdp = request.form.get('password')
        if mdp == app.config['ADMIN_PASSWORD']:
            session['admin'] = True
            flash('Connecté en tant qu\'admin', 'success')
            return redirect(url_for('accueil'))
        flash('Mot de passe incorrect', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    flash('Déconnecté', 'info')
    return redirect(url_for('accueil'))

# Décorateur pour protéger les routes sensibles

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin'):
            flash('Accès réservé aux administrateurs', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Routes Admin ---
@app.route('/admin/ajouter_joueur', methods=['GET', 'POST'])
@admin_required
def admin_add_player():
    if request.method == 'POST':
        nom = request.form.get('nom', '').strip()
        if nom:
            if Player.query.filter_by(nom=nom).first():
                flash('Ce joueur existe déjà', 'warning')
            else:
                db.session.add(Player(nom=nom))
                db.session.commit()
                flash(f'Joueur « {nom} » ajouté', 'success')
                return redirect(url_for('accueil'))
    return render_template('admin_add_player.html')

@app.route('/admin/ajouter_match', methods=['GET', 'POST'])
@admin_required
def admin_add_match():
    joueurs = Player.query.order_by(Player.nom).all()
    if request.method == 'POST':
        j1 = int(request.form.get('player1'))
        j2 = int(request.form.get('player2'))
        s1 = int(request.form.get('score1', 0))
        s2 = int(request.form.get('score2', 0))
        c1 = request.form.get('color1')
        # Validation
        if j1 == j2 or max(s1, s2) != 10:
            flash('Données de match invalides', 'danger')
        else:
            p1 = Player.query.get(j1)
            p2 = Player.query.get(j2)
            # Calcul ELO
            new_elo1, new_elo2 = calc_elo(p1.elo, p2.elo, s1, s2)
            p1.elo, p2.elo = new_elo1, new_elo2
            p1.n_games += 1; p2.n_games += 1
            # Stats victoires/défaites & couleurs
            if s1 > s2:
                p1.wins += 1; p2.losses += 1; p1.win_streak += 1; p2.win_streak = 0
            else:
                p2.wins += 1; p1.losses += 1; p2.win_streak += 1; p1.win_streak = 0
            if c1 == 'rouge': p1.wins_as_red += 1
            else: p1.wins_as_blue += 1
            # Buts encaissés
            p1.goals_conceded += s2; p2.goals_conceded += s1
            # Enregistrement du match
            match = Match(
                date=datetime.utcnow(),
                winner_id=j1 if s1>s2 else j2,
                loser_id=j2 if s1>s2 else j1,
                score_winner=max(s1,s2), score_loser=min(s1,s2),
                winner_color=c1,
                loser_color=('bleu' if c1=='rouge' else 'rouge')
            )
            db.session.add(match)
            db.session.commit()
            flash('Match enregistré et ELO mis à jour', 'success')
            return redirect(url_for('accueil'))
    return render_template('admin_add_match.html', joueurs=joueurs)