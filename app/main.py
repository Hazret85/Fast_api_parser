import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from .database import SessionLocal, engine, Base, get_db
from .models import Movie
import time
import random
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание всех таблиц в базе данных
Base.metadata.create_all(bind=engine)

# Инициализация FastAPI приложения
app = FastAPI()

# Монтирование директории статических файлов
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Настройка шаблонов Jinja2
templates = Jinja2Templates(directory="app/templates")

@app.on_event("startup")
async def startup_event():
    # Автоматическое создание таблиц при запуске приложения
    Base.metadata.create_all(bind=engine)
    logger.info("Таблицы базы данных созданы или уже существуют.")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    try:
        movies = db.query(Movie).all()
        return templates.TemplateResponse("index.html", {"request": request, "movies": movies})
    except Exception as e:
        logger.error(f"Ошибка при получении фильмов из базы данных: {e}")
        raise HTTPException(status_code=500, detail="Не удалось получить фильмы из базы данных.")

@app.get("/parse", response_class=HTMLResponse)
async def parse_and_save_movies(request: Request, db: Session = Depends(get_db)):
    try:
        movies = parser_films(['https://www.kinonews.ru/top100/', 'https://www.kinonews.ru/top100_p2/'])
        for title, info in movies.items():
            description = info.get("description")
            rating = info.get("rating")
            image_url = info.get("image_url")
            existing_movie = db.query(Movie).filter_by(title=title).first()
            if not existing_movie:
                new_movie = Movie(
                    title=title,
                    description=description,
                    rating=rating,
                    image_url=image_url
                )
                db.add(new_movie)
        db.commit()
        logger.info("Фильмы успешно разобраны и сохранены в базу данных.")
        return templates.TemplateResponse("index.html", {"request": request, "movies": db.query(Movie).all(), "message": "Фильмы успешно разобраны и сохранены."})
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка при разборе и сохранении фильмов: {e}")
        raise HTTPException(status_code=500, detail="Не удалось разобрать и сохранить фильмы.")

def parser_films(urls):
    result = {}
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                      ' Chrome/91.0.4472.124 Safari/537.36'
    }

    for url in urls:
        try:
            logger.info(f"Получение данных с {url}")
            res = requests.get(url, headers=headers, timeout=10)
            res.raise_for_status()
            soup = BeautifulSoup(res.content, 'lxml')

            titles = soup.find_all(class_='titlefilm')

            for film_info in titles:
                title = film_info.get_text(strip=True)
                descriptions = film_info.find_next(class_='rating_rightdesc')
                image_tag = film_info.find_previous('img')  # Пример поиска изображения
                image_url = image_tag['src'] if image_tag and 'src' in image_tag.attrs else None

                info_lst = []
                if descriptions:
                    for info in descriptions.stripped_strings:
                        info_lst.append(info)
                description = info_lst[0] if len(info_lst) > 0 else None
                rating = float(info_lst[1].split()[0]) if len(info_lst) > 1 else None

                result[title] = {
                    "description": description,
                    "rating": rating,
                    "image_url": image_url
                }

            # Задержка между запросами для избежания блокировки
            time.sleep(random.uniform(1, 3))
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при запросе к {url}: {e}")
            continue
        except Exception as e:
            logger.error(f"Ошибка при разборе данных из {url}: {e}")
            continue

    return result
