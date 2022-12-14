import os
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, redirect, render_template, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

app = Flask(__name__)

# Database credentials
username = 'opinion_user'
password = 'opinion'
database = 'opinion_db'

# Configuration Flask application
app.secret_key = os.urandom(32)
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{username}:{password}@localhost:5432/{database}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

ROWS_PER_PAGE = 20


class Opinion(db.Model):
    __tablename__ = 'tb_opinions'

    id = db.Column(db.Integer, primary_key=True)
    code_article = db.Column(db.String(255), nullable=True)
    titre_article = db.Column(db.String(255), nullable=True)
    auteurs = db.Column(db.String(255), nullable=True)
    commentary = db.Column(db.Text, nullable=True)
    source = db.Column(db.String(255), nullable=True)
    date_extraction = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return "<Opinion(code_article='{}', titre_article='{}', auteurs='{}', commentary='{}', " \
               "date_extraction='{}')>" \
            .format(self.code_article, self.titre_article, self.auteurs, self.commentary, self.date_extraction)


@app.context_processor
def inject_now():
    return {'now': datetime.now()}


@app.route('/')
def index():
    return 'Web App with Python Flask!'


@app.route('/opinions/get')
def opinions_index():
    page = request.args.get('page', 1, type=int)
    opinions = Opinion.query.paginate(page=page, per_page=ROWS_PER_PAGE)
    return render_template('pages/opinions/index.html', opinions=opinions)


@app.route('/opinions/show/<int:id>', methods=['GET'])
def opinions_show(id):
    opinions = Opinion.query.filter_by(id=id).first()
    if opinions:
        return redirect(url_for('opinions_index'))
    return f"Opinion with id ={id} Doesnt exist"


@app.route('/opinions/create', methods=['GET', 'POST'])
def opinions_create():
    if request.method == 'GET':
        return render_template('pages/opinions/add.html')

    if request.method == 'POST':

        df = pd.DataFrame()
        auteurs = []
        commentaires = []
        codes = []
        dates = []
        mes_titres = []

        for i in range(100, 110):
            # requests.get(f"{m_social.lien}{i}")
            c = requests.get(f"https://lefaso.net/spip.php?article115{i}")
            c_soup = BeautifulSoup(c.content, "html.parser")
            auteur = c_soup.find_all("strong", class_="fn n")
            commentaire = c_soup.find_all("div", class_="comment-content description")
            date_article = c_soup.find_all('abbr', class_='dtreviewed')
            titres = c_soup.find_all('h1', class_="entry-title")
            for titr in titres:
                liste_titre = []
                liste_titre.append(titr.text)
            for autor in auteur:
                auteurs.append(autor.text)
            for comment in commentaire:
                commentaires.append(comment.text)
                codes.append(c.url[28:])
                mes_titres.append(liste_titre[0])
            for j in date_article:
                dates.append(j['title'])

        df["Code_Article"] = codes
        df["Auteur"] = auteurs
        df["Commentaire"] = commentaires
        df["Date_Heure"] = dates
        df["Titre"] = mes_titres
        df = df.replace('\n', ' ', regex=True)

        for i in df.index:
            opinions = Opinion(code_article=df["Code_Article"][i], titre_article=df["Titre"][i],
                               auteurs=df["Auteur"][i], commentary=df["Commentaire"][i],
                               date_extraction=df["Date_Heure"][i])
            db.session.add(opinions)
            db.session.commit()
            flash(f"Extraction reussie !", "success")
        return redirect('/opinions/get')

    return render_template('pages/opinions/add.html')


@app.route('/opinions/<int:id>/delete', methods=['GET', 'POST'])
def opinions_delete(id):
    opinion = Opinion.query.filter_by(id=id).first()
    if request.method == 'POST':
        if opinion:
            db.session.delete(opinion)
            db.session.commit()
            return redirect('/opinions/get')
        abort(404)
    return render_template('pages/opinions/index.html')


@app.errorhandler(404)
def page_not_found(error):
    return render_template('errors/404.html'), 404


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
