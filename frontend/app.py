from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

app = Flask(__name__)

client = MongoClient("mongodb://mongo:27017/")
db = client["books_project"]
collection = db["fantasy_books"]
tasks_collection = db["scrape_tasks"]

@app.route("/")
def index():
    selected_category = request.args.get("category")
    if selected_category:
        items = list(collection.find({"category": selected_category}))
    else:
        items = list(collection.find())
    categories = [
        "travel_2", "mystery_3", "historical-fiction_4", "sequential-art_5",
        "classics_6", "philosophy_7", "romance_8", "womens-fiction_9",
        "fiction_10", "childrens_11", "religion_12", "nonfiction_13",
        "music_14", "default_15", "science-fiction_16", "sports-and-games_17",
        "add-a-comment_18", "fantasy_19", "new-adult_20", "young-adult_21",
        "science_22", "poetry_23", "paranormal_24", "art_25", "psychology_26",
        "autobiography_27", "parenting_28", "adult-fiction_29", "humor_30",
        "horror_31", "history_32", "food-and-drink_33", "christian-fiction_34",
        "business_35", "biography_36", "thriller_37", "contemporary_38",
        "spirituality_39", "academic_40", "self-help_41", "historical_42",
        "christian_43", "suspense_44", "short-stories_45", "novels_46",
        "health_47", "politics_48", "cultural_49", "erotica_50", "crime_51"
    ]
    return render_template("index.html", items=items, categories=categories,selected_category=selected_category )

@app.route("/scrape_category", methods=["POST"])
def scrape_category():
    num_books = int(request.form.get("num_books", 3))
    category = request.form.get("category")
    tasks_collection.insert_one({"category": category, "num_books": num_books, "status": "pending"})
    return redirect(url_for("index"))

@app.route("/delete_book", methods=["POST"])
def delete_book():
    book_id = request.form.get("book_id")
    collection.delete_one({"_id": ObjectId(book_id)})
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
