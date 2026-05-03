import requests
import random
from collections import Counter

DEFAULT_GENRES = [
    "fiction",
    "history",
    "fantasy",
    "mystery",
    "science_fiction",
    "romance",
    "classic",
    "horror",
]


def get_recommendations(user_books=None):
    target_genre = None
    if user_books and len(user_books) > 0:
        genres = [b.genre for b in user_books if b.genre]
        if genres:
            count_genre = Counter(genres)
            target_genre = count_genre.most_common(1)[0][0]
        else:
            target_genre = random.choice(DEFAULT_GENRES)
    else:
        target_genre = random.choice(DEFAULT_GENRES)
    url = f"https://openlibrary.org/subjects/{target_genre.lower().replace(' ', '_')}.json?limit=12"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            works = data.get("works", [])
            user_titles = [b.title for b in user_books] if user_books else []
            filtered_works = [w for w in works if w.get("title") not in user_titles]
            final_list = []
            for work in filtered_works[:6]:
                final_list.append(
                    {
                        "title": work.get("title"),
                        "author": work.get("authors")[0].get("name")
                        if work.get("authors")
                        else "Неизвестен",
                        "key": work.get("key").lstrip("/"),
                        "cover_id": work.get("cover_id"),
                    }
                )
            return {"genre_display": target_genre.capitalize(), "books": final_list}
    except Exception as e:
        print(f"Recommendation Error: {e}")

    return None
