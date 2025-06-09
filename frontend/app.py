from flask import Flask, render_template
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient("mongodb://mongo:27017/")
db = client["books_project"]
collection = db["fantasy_books"]

@app.route('/') 
def index(): 
    items = list(collection.find())
    return render_template("index.html", items=items)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
