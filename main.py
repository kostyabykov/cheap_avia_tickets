import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from config import Config
from models import Base
from scanner import Scanner
from aggregator import Aggregator
from monitor import AnomalyMonitor

async def init_db(config: Config):
    engine = create_async_engine(config.DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return engine

async def scanning_loop(session: AsyncSession, config: Config):
    scanner = Scanner(session, config)
    monitor = AnomalyMonitor(session, config)
    
    while True:
        try:
            await scanner.scan_routes()
            await asyncio.sleep(60)  # Пауза между циклами сканирования
        except Exception as e:
            print(f"Ошибка в процессе сканирования: {e}")
            await asyncio.sleep(60)

async def daily_summary_loop(session: AsyncSession):
    aggregator = Aggregator(session)
    
    while True:
        try:
            await aggregator.aggregate_daily_data()
            await asyncio.sleep(24 * 60 * 60)  # Ждем 24 часа
        except Exception as e:
            print(f"Ошибка в процессе агрегации: {e}")
            await asyncio.sleep(60)

async def main():
    config = Config()
    engine = await init_db(config)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        # Запускаем все задачи параллельно
        await asyncio.gather(
            scanning_loop(session, config),
            daily_summary_loop(session)
        )

if __name__ == "__main__":
    asyncio.run(main()) 