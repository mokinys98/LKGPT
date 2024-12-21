from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from APImodels import User
from sql.sqldb import initialize_supabase, connect_to_supabase

router = APIRouter()
supabase = initialize_supabase()
# Initialize templates
templates = Jinja2Templates(directory="HTMLtemplates")


@router.get("/get-users/", response_class=HTMLResponse)
async def get_users(request: Request):
    try:
        # Fetch all users from the Supabase 'users' table
        response = supabase.table("sender_statistics").select("sender_email").execute()
        users = response.data

        # Extract columns and rows
        if users:
            columns = users[0].keys()
            data = [list(user.values()) for user in users]
        else:
            columns = ["No Data"]
            data = [["No records available"]]

        # Render the table template
        return templates.TemplateResponse("table.html", {
            "request": request,
            "columns": columns,
            "data": data
        })
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error: {str(e)}</h1>", status_code=500)