
from fastapi import FastAPI
from app.models.entity import Base 
from app.models import site 
from app.database import engine
from app.api.entities import router as entity_router
from fastapi.staticfiles import StaticFiles
from app.api import llms
from app.api.sites import router as site_router
from app.api.site_sync import router as site_sync_router
from app.api.site_jsonld import router as site_jsonld_router
from app.api.squarespace import router as squarespace_router
from app.api.auto_square import router as auto_sq_router
from app.api.get_generated_files import router as get_files_router
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware  #for ngrok

#for ngrok
class NgrokMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["ngrok-skip-browser-warning"] = "true"
        return response


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can replace "*" with your Squarespace site URL(s) for more security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# create tables automatically
Base.metadata.create_all(bind=engine)

# for ngrok
app.add_middleware(NgrokMiddleware)  

# include API routes
app.include_router(entity_router)
app.include_router(site_router)
app.include_router(site_sync_router)
app.include_router(site_jsonld_router)
app.include_router(squarespace_router)
app.include_router(auto_sq_router)
app.include_router(get_files_router)


app.mount("/static", StaticFiles(directory="generated"), name="static")

app.include_router(llms.router, prefix="/llms", tags=["LLMS"])