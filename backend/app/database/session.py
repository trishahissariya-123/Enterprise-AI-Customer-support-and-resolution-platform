from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker,create_async_engine
from backend.app.config import  get_settings
settings=get_settings()

engine=create_async_engine(settings.ASYNC_DATABASE_URL, pool_pre_ping=True)
AsyncSessionLocal=async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async  def get_db():
    async with AsyncSessionLocal() as session:
        yield session