from fastapi import APIRouter, HTTPException
from APImodels import User
from sqldb import initialize_supabase, connect_to_supabase

router = APIRouter()
supabase = initialize_supabase()

@router.post("/add-user/")
async def add_user(user: User):
    try:
        # Insert a user into the 'users' table
        response = supabase.table("users").insert({"email": user.email, "name": user.name}).execute()
        return {"message": "User added successfully", "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/get-users/")
async def get_users():
    try:
        # Fetch all users from the 'sender_statistics' table
        response = supabase.table("sender_statistics").select("sender_email").execute()
        return {"data": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))