from urllib import request
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import data
import os
import shutil

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.add_middleware(SessionMiddleware, secret_key="id")
app.mount("/users_images", StaticFiles(directory="users_images"), name="users_images")

# Инициализация БД
data.init_db()
# Проверка текущего пользователя
def curent_user(request: Request):
    return request.session.get("user")
# Проверка авторизации
@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    if curent_user(request):
        return RedirectResponse(url="/success", status_code=303)
    return templates.TemplateResponse("dash.html", {"request": request})
# Страница регистрации
@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
# Страница входа
@app.get("/logins", response_class=HTMLResponse)
async def login_page(request: Request, error: str = None): # Добавляем error
    return templates.TemplateResponse("vhod.html", {
        "request": request, 
        "error": error # Передаем его в HTML
    })
#  Добавление нового пользователя
@app.post("/add_user")
async def create_user(request: Request, name: str = Form(...), age: str = Form(...)):
    data.add_user(name, age)
    request.session["user"] = name
    return RedirectResponse(url="/success", status_code=303)
# Страница успешного входа
@app.get("/success", response_class=HTMLResponse)
async def success_page(request: Request):
    user = curent_user(request)
    if not user:
        return RedirectResponse(url="/logins", status_code=303)
    
    # Путь к папке пользователя
    user_folder = f"users_images/{user}"
    
    photos = []
    # Если папка существует, берем из нее все файлы
    if os.path.exists(user_folder):
        #
        photos = [f"users_images/{user}/{f}" for f in os.listdir(user_folder)]
    
    return templates.TemplateResponse("success.html", {
        "request": request, 
        "user": user, 
        "photos": photos # Передаем список фото в шаблон
    })
# Вход пользователя
@app.post('/login')
async def prover(request: Request, name: str = Form(...), age: str = Form(...)):
    if data.prover(name, age):
        request.session["user"] = name
        return RedirectResponse(url="/success", status_code=303)
    else:
        return RedirectResponse(url="/logins?error=1", status_code=303)
    
@app.get("/logout")
async def logout(request: Request):
    request.session.pop("user", None)
    return RedirectResponse(url="/", status_code=303)

@app.post("/upload_photo")
async def upload_photo(request: Request, file: UploadFile = File(...)):
    user = curent_user(request)
    if not user:
        return RedirectResponse(url="/logins", status_code=303)
    user_folder = f"users_images/{user}"
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
    file_loca = f"{user_folder}/{file.filename}"
    with open(file_loca, "wb") as f:
        shutil.copyfileobj(file.file, f)
    data.add_photo(user, user_folder + "/" + file.filename)
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        return HTMLResponse(content="Неверный формат файла. Пожалуйста, загрузите изображение.", status_code=400)
    if file.filename == "":
        return HTMLResponse(content="Файл не выбран. Пожалуйста, выберите файл для загрузки.", status_code=400)
    return RedirectResponse(url="/success", status_code=303)
@app.post("/delete_photo") # Исправлено с .posrt на .post
async def delete_photo(request: Request, photo: str = Form(...)):
    user = curent_user(request)
    if not user:
        return RedirectResponse(url="/logins", status_code=303)
    
    # ПРОВЕРКА БЕЗОПАСНОСТИ:
    # Проверяем, что путь к фото содержит имя текущего пользователя.
    # Это не даст юзеру "Admin" удалить фото юзера "Ivan".
    if f"users_images/{user}/" not in photo:
        return HTMLResponse(content="Ошибка доступа", status_code=403)

    # 1. Удаляем запись из базы данных
    if hasattr(data, 'delete_photo'): # Проверяем, есть ли такая функция в data.py
        data.delete_photo(photo)
    
    # 2. Удаляем сам файл с диска
    if os.path.exists(photo):
        os.remove(photo)
        print(f"Файл {photo} успешно удален")
    else:
        print(f"Файл {photo} не найден на диске")

    return RedirectResponse(url="/success", status_code=303)
@app.get("/message", response_class=HTMLResponse)
async def message_page(request: Request):
    return templates.TemplateResponse("messege.html", {"request": request})
