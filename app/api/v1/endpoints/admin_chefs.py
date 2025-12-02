# # app/api/v1/endpoints/chef_auth.py

# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.ext.asyncio import AsyncSession

# from app.db.session import get_db
# from app.services.chef_service import chef_login_service
# from app.core.security import create_access_token,verify_password,decode_token
# from app.api.deps import chef_required
# from app.schemas.auth import ChefLoginRequest
# from fastapi.security import OAuth2PasswordRequestForm
# from app.models.chef import Chef
# from sqlalchemy import select

# router = APIRouter(prefix="/chef/auth", tags=["Chef Authentication"])


# # ============================================================
# # CHEF LOGIN
# # ============================================================

# @router.post("/login")
# async def chef_login(
#     form_data: OAuth2PasswordRequestForm = Depends(),
#     db: AsyncSession = Depends(get_db)
# ):
#     phone_number = form_data.username

#     result = await db.execute(
#         select(Chef).where(Chef.phone_number == phone_number)
#     )
#     chef = result.scalar_one_or_none()

#     if not chef:
#         raise HTTPException(401, "Invalid phone number or password")

#     if not verify_password(form_data.password, chef.password):
#         raise HTTPException(401, "Invalid phone number or password")

#     token = create_access_token({"chef_id": chef.id})

#     return {"access_token": token, "token_type": "bearer"}


# # ============================================================
# # LOGOUT (Stateless JWT)
# # ============================================================
# @router.post("/logout")
# async def chef_logout(current_chef = Depends(chef_required)):
#     """
#     Stateless logout. 
#     Client simply deletes token. Server confirms success.
#     """
#     return {"message": "Logged out successfully"}
