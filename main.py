from fastapi import FastAPI
from pydantic import BaseModel
import requests
import uvicorn

app = FastAPI()

db = []

class City(BaseModel):
    name: str
    timezone: str


@app.get('/')
def get_cities():
    return db


@app.get('/cities/{city_id}')
def get_city(city_id: int):
    return db[city_id]


@app.post('/post')
def post(city: City):
    db.append(city.dict())
    return 200


@app.delete('/delete')
def delete(city: int):
    db.remove(db[city])


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
