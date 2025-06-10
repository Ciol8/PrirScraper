from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
from flask import jsonify

app = Flask(__name__)

client = MongoClient("mongodb://mongo:27017/")
db = client["books_project"]
collection = db["fantasy_books"]
tasks_collection = db["scrape_tasks"]

@app.route("/")
def index():
    selected_category = request.args.get("category")
    sort_by = request.args.get("sort_by", "title")  # nowy parametr

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

    categories_display = []
    for cat in categories:
        name = cat.rsplit("_", 1)[0].replace("-", " ").capitalize()
        categories_display.append((cat, name))

    # Mapa sortowania — pole, kierunek
    sort_mapping = {
        "title": ("title", 1),
        "stars": ("stars_num", -1),
        "price": ("price_num", 1),
        "quantity": ("quantity_num", -1)
    }

    sort_field, sort_order = sort_mapping.get(sort_by, ("title", 1))

    # Budujemy query
    query = {}
    if selected_category:
        query["category"] = selected_category

    # Pobieramy książki + sortowanie
    items = list(collection.find(query).sort(sort_field, sort_order))
    num_books_total = collection.count_documents(query)
    num_books_new = collection.count_documents({**query, "new": True})

    return render_template(
        "index.html",
        items=items,
        categories_display=categories_display,
        selected_category=selected_category,
        sort_by=sort_by,  # dodajemy sort_by do template
        num_books_total=num_books_total,
        num_books_new=num_books_new
    )


@app.route("/scrape_category", methods=["POST"])
def scrape_category():
    num_books = int(request.form.get("num_books", 3))
    category = request.form.get("category")

    # usuwamy wszystkie NEW w tej kategorii
    collection.update_many({"category": category, "new": True}, {"$set": {"new": False}})

    # dodajemy task
    task = {"category": category, "num_books": num_books, "status": "pending"}
    task_id = tasks_collection.insert_one(task).inserted_id

    # przekierowujemy na scrape_status z id taska
    return redirect(url_for("scrape_status", task_id=str(task_id)))


@app.route("/delete_book", methods=["POST"])
def delete_book():
    book_id = request.form.get("book_id")
    collection.delete_one({"_id": ObjectId(book_id)})
    return redirect(url_for("index"))

@app.route("/check_task_status")
def check_task_status():
    task = tasks_collection.find_one(sort=[("_id", -1)])
    return {"status": task["status"]} if task else {"status": "unknown"}

@app.route("/scrape_status/<task_id>")
def scrape_status(task_id):
    return render_template("scrape_status.html", task_id=task_id)

@app.route("/scrape_status_check/<task_id>")
def scrape_status_check(task_id):
    task = tasks_collection.find_one({"_id": ObjectId(task_id)})
    status = task["status"] if task else "unknown"
    return jsonify({"status": status})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
