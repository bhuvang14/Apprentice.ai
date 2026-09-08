from fastapi import APIRouter

from app.api import chat, templates, policies, generations, files, auth

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(templates.router, prefix="/admin/templates", tags=["admin-templates"])
api_router.include_router(policies.router, prefix="/admin/policy-docs", tags=["admin-policies"])
api_router.include_router(generations.router, prefix="/generations", tags=["generations"])
api_router.include_router(files.router, prefix="/files", tags=["files"])