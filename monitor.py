from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models import Flight, FlightDay
from config import Config
from aiogram import Bot

class AnomalyMonitor:
    def __init__(self, session: AsyncSession, config: Config):
        self.session = session
        self.config = config
        self.bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    
    async def check_anomaly(self, flight: Flight):
        # Получаем исторические данные за последние 30 дней
        thirty_days_ago = datetime.utcnow() - timedelta(days=self.config.HISTORY_DAYS)
        
        query = select(func.avg(FlightDay.min_price)).where(
            FlightDay.departure_from == flight.departure_from,
            FlightDay.departure_to == flight.departure_to,
            FlightDay.one_way == flight.one_way,
            FlightDay.days_between == flight.days_between,
            FlightDay.aggregation_date >= thirty_days_ago.strftime("%Y-%m-%d")
        )
        
        result = await self.session.execute(query)
        avg_price = result.scalar_one_or_none()
        
        if avg_price and flight.price < avg_price * self.config.ANOMALY_THRESHOLD:
            await self.send_alert(flight, avg_price)
    
    async def send_alert(self, flight: Flight, avg_price: float):
        message = (
            f"🔥 Найдена аномально низкая цена!\n\n"
            f"Направление: {flight.departure_from} ➡️ {flight.departure_to}\n"
            f"Дата вылета: {flight.date_from}\n"
            f"{f'Дата возврата: {flight.date_to}' if not flight.one_way else ''}\n"
            f"Тип: {'В одну сторону' if flight.one_way else 'Туда-обратно'}\n"
            f"Дней между рейсами: {flight.days_between or 'N/A'}\n"
            f"Цена: {flight.price} RUB (обычная цена: {int(avg_price)} RUB)\n"
            f"Экономия: {int(avg_price - flight.price)} RUB ({int((1 - flight.price/avg_price) * 100)}%)"
        )
        
        await self.bot.send_message(
            chat_id=self.config.TELEGRAM_CHANNEL_ID,
            text=message
        ) 