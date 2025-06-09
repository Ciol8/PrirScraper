import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient

print("Engine: Start...")

# Connect to MongoDB
client = MongoClient("mongodb://mongo:27017/")

db = client["books_project"]
collection = db["fantasy_books"]

# Czyszczenie kolekcji (opcjonalnie)
collection.delete_many({})

# URL kategorii Fantasy
url = "https://books.toscrape.com/catalogue/category/books/fantasy_19/index.html"
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

# Pobieramy 3 pierwsze książki
books = soup.select("article.product_pod")[:3]

for book in books:
    title = book.h3.a['title']
    price = book.select_one('p.price_color').get_text(strip=True)
    star_rating = book.select_one('p.star-rating')['class'][1]

    # Pobieramy link do strony książki
    book_link = book.h3.a['href']
    book_url = "https://books.toscrape.com/catalogue/" + book_link.replace('../../../', '')

    # Pobieramy szczegóły ze strony książki (czy jest in stock i ile)
    book_response = requests.get(book_url)
    book_soup = BeautifulSoup(book_response.text, "html.parser")

    stock_info = book_soup.select_one('p.instock.availability').get_text(strip=True)

    import re
    match = re.search(r'\((\d+) available\)', stock_info)
    quantity = match.group(1) if match else "Brak danych"

    # Wkładamy do Mongo
    doc = {
        "title": title,
        "price": price,
        "stars": star_rating,
        "stock_info": stock_info,
        "quantity": quantity,
        "book_url": book_url
    }

    collection.insert_one(doc)
    print(f"Inserted: {title}")

print("Engine: DONE ✅")
