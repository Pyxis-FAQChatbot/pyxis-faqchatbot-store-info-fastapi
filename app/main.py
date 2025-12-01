from fastapi import FastAPI
from app.routers.flow import router as flow_router
from app.routers.sales import router as sales_router
from app.routers.shop import router as shop_router

app = FastAPI(title="Pyxis Store Info API")

app.include_router(flow_router, prefix="/api/v1")
app.include_router(sales_router, prefix="/api/v1")
app.include_router(shop_router, prefix="/api/v1")