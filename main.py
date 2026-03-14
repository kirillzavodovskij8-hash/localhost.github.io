import os
import shutil
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

# Импортируем твой модуль данных
import data 

app = FastAPI()

# 1. ГАРАНТИРУЕМ НАЛИЧИЕ ПАПКИ ДЛЯ ИЗОБРАЖЕНИЙ
# На Render папки могут не создаться сами, если их нет в Git
UPLOAD_DIR = "users_images"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# 2. ПОДКЛЮЧАЕМ ШАБЛОНЫ И СТАТИКУ
templates = Jinja2Templates(directory="templates")
app.mount("/users_images", StaticFiles(directory=UPLOAD_DIR), name="users_images")

# Секретный ключ лучше вынести в переменные окружения, но для теста оставим так
app.add_middleware(SessionMiddleware, secret_key="supersecretkey")

# Инициализация БД
data.init_db()

# Проверка текущего пользователя
def curent_user(request: Request):
    return request.session.get("user")

# --- МАРШРУТЫ ---

@app.get("/", response_class=HTMLResponse)
async def read_form(request: Request):
    if curent_user(request):
        return RedirectResponse(url="/success", status_code=303)
    return templates.TemplateResponse("dash.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/logins", response_class=HTMLResponse)
async def login_page(request: Request, error: str = None):
    return templates.TemplateResponse("vhod.html", {
        "request": request, 
        "error": error 
    })

@app.post("/add_user")
async def create_user(request: Request, name: str = Form(...), age: str = Form(...)):
    data.add_user(name, age)
    request.session["user"] = name
    return RedirectResponse(url="/success", status_code=303)

@app.get("/success", response_class=HTMLResponse)
async def success_page(request: Request):
    user = curent_user(request)
    if not user:
        return RedirectResponse(url="/logins", status_code=303)
    
    user_folder = os.path.join(UPLOAD_DIR, user)
    photos = []
    
    if os.path.exists(user_folder):
        # Используем правильное формирование путей для вывода в HTML
        photos = [f"/{user_folder}/{f}" for f in os.listdir(user_folder)]
    
    return templates.TemplateResponse("success.html", {
        "request": request, 
        "user": user, 
        "photos": photos
    })

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
    
    # Создаем папку пользователя внутри users_images
    user_folder = os.path.join(UPLOAD_DIR, user)
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
    
    file_path = os.path.join(user_folder, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Сохраняем в БД относительный путь, начинающийся с /
    data.add_photo(user, f"/{file_path}")
    
    return RedirectResponse(url="/success", status_code=303)

@app.post("/delete_photo")
async def delete_photo(request: Request, photo: str = Form(...)):
    user = curent_user(request)
    if not user:
        return RedirectResponse(url="/logins", status_code=303)
    
    # Очищаем путь от ведущего слэша для удаления с диска
    clean_path = photo.lstrip('/')
    
    if f"users_images/{user}/" not in clean_path:
        return HTMLResponse(content="Ошибка доступа", status_code=403)

    if hasattr(data, 'delete_photo'):
        data.delete_photo(photo)
    
    if os.path.exists(clean_path):
        os.remove(clean_path)
    
    return RedirectResponse(url="/success", status_code=303)

@app.get("/message", response_class=HTMLResponse)
async def message_page(request: Request):
    return templates.TemplateResponse("messege.html", {"request": request})
