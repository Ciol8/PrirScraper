import time
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from multiprocessing import Pool, cpu_count
import re

def scrape_book_details(book_url):
    response = requests.get(book_url)
    book_soup = BeautifulSoup(response.text, "html.parser")

    stock_info = book_soup.select_one('p.instock.availability').get_text(strip=True)
    match = re.search(r'\((\d+) available\)', stock_info)
    quantity = match.group(1) if match else "Brak danych"
    stock_text_clean = match.group(0) if match else stock_info

    return {
        'book_url': book_url,
        'stock_info': stock_text_clean,
        'quantity': quantity
    }

def process_category(category, num_books):
    print(f"Scraping category: {category} ({num_books} books)")
    client = MongoClient("mongodb://mongo:27017/")
    db = client["books_project"]
    collection = db["fantasy_books"]

    url = f"https://books.toscrape.com/catalogue/category/books/{category}/index.html"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    books = soup.select("article.product_pod")[:num_books]

    stars_map = {
        'One': '⭐',
        'Two': '⭐⭐',
        'Three': '⭐⭐⭐',
        'Four': '⭐⭐⭐⭐',
        'Five': '⭐⭐⭐⭐⭐'
    }

    book_links = []
    book_meta = []

    for book in books:
        title = book.h3.a.get('title', '').encode('latin1').decode('utf-8', errors='ignore')
        price = book.select_one('p.price_color').get_text(strip=True).replace('Â', '')
        star_rating = book.select_one('p.star-rating')['class'][1]
        star_rating_emote = stars_map.get(star_rating, '')

        book_link = book.h3.a['href']
        book_url = "https://books.toscrape.com/catalogue/" + book_link.replace('../../../', '')

        book_links.append(book_url)

    

        book_meta.append({
            'title': title,
            'price': price,
            'stars': star_rating_emote,
            'book_url': book_url,
            'category': category
        })

    print(f"\nFound {len(book_links)} book links. Starting multiprocessing...\n")

    with Pool(processes=min(cpu_count(), len(book_links))) as pool:
        details_results = pool.map(scrape_book_details, book_links)

    inserted_count = 0
    for meta, details in zip(book_meta, details_results):
        meta.update(details)
        exists = collection.find_one({'title': meta['title'], 'category': meta['category']})
        if not exists:
            collection.insert_one(meta)
            inserted_count += 1
            print(f"Inserted: {meta['title']}")
        else:
            print(f"Skipped duplicate: {meta['title']}")

    print(f"\nInserted {inserted_count} new books.")

if __name__ == "__main__":
    client = MongoClient("mongodb://mongo:27017/")
    db = client["books_project"]
    tasks_collection = db["scrape_tasks"]

    while True:
        task = tasks_collection.find_one({"status": "pending"})
        if task:
            category = task["category"]
            num_books = task.get("num_books", 3)
            tasks_collection.update_one({"_id": task["_id"]}, {"$set": {"status": "processing"}})
            try:
                process_category(category, num_books)
                tasks_collection.update_one({"_id": task["_id"]}, {"$set": {"status": "done"}})
            except Exception as e:
                print(f"Error: {e}")
                tasks_collection.update_one({"_id": task["_id"]}, {"$set": {"status": "error"}})
        time.sleep(1)
