import requests


def search_books(query):
    url = f"https://openlibrary.org/search.json?q={query}&limit=20"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        result = []
        for d in data.get("docs", []):
            book = {
                "title": d.get("title"),
                "author": ", ".join(d.get("author_name", ["Неизвестен"])),
                "isbn": d.get("isbn", [None])[0],
                "first_publish_year": d.get("first_publish_year"),
                "cover_url": f"https://covers.openlibrary.org/b/id/{d.get('cover_i')}-M.jpg"
                if d.get("cover_i")
                else None,
            }
            result.append(book)

        return result
    except Exception as e:
        print(e)
        return []
