from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models import Flight, FlightDay

class Aggregator:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def aggregate_daily_data(self):
        yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Выбираем и группируем данные за вчерашний день
        query = select(
            Flight.departure_from,
            Flight.departure_to,
            Flight.date_from,
            Flight.date_to,
            Flight.one_way,
            Flight.days_between,
            func.min(Flight.price).label('min_price')
        ).where(
            func.date(Flight.timestamp) == yesterday
        ).group_by(
            Flight.departure_from,
            Flight.departure_to,
            Flight.date_from,
            Flight.date_to,
            Flight.one_way,
            Flight.days_between
        )
        
        result = await self.session.execute(query)
        
        # Сохраняем агрегированные данные
        for row in result:
            flight_day = FlightDay(
                aggregation_date=yesterday,
                departure_from=row.departure_from,
                departure_to=row.departure_to,
                date_from=row.date_from,
                date_to=row.date_to,
                one_way=row.one_way,
                days_between=row.days_between,
                min_price=row.min_price
            )
            self.session.add(flight_day)
        
        await self.session.commit() 