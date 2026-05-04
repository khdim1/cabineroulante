import os
from flask import Flask, render_template, request, jsonify
from recommander import recommander
from database import init_db

app = Flask(__name__)

# Initialiser la base de données au démarrage
init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/recommander', methods=['POST'])
def recommandation():
    mesures = request.get_json()
    fauteuil = recommander(mesures)
    return jsonify(fauteuil)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
