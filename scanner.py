import asyncio
from datetime import datetime, timedelta
import aiohttp
from aiolimiter import AsyncLimiter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Flight
from config import Config

class Scanner:
    def __init__(self, session: AsyncSession, config: Config):
        self.session = session
        self.config = config
        self.rate_limiter = AsyncLimiter(config.API_RATE_LIMIT, 60)
        
    async def get_flight_prices(self, origin: str, destination: str, date_from: str, 
                              date_return: str | None = None) -> list:
        async with self.rate_limiter:
            params = {
                "origin": origin,
                "destination": destination,
                "departure_at": date_from,
                "return_at": date_return,
                "token": self.config.AVIASALES_API_TOKEN
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(self.config.AVIASALES_API_URL, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data", [])
        return []

    async def process_flight_data(self, flight_data: dict, one_way: bool, 
                                origin: str, destination: str):
        days_between = None
        if not one_way:
            date_from = datetime.strptime(flight_data["departure_at"], "%Y-%m-%d")
            date_to = datetime.strptime(flight_data["return_at"], "%Y-%m-%d")
            days_between = (date_to - date_from).days

        flight = Flight(
            timestamp=datetime.utcnow(),
            departure_from=origin,
            departure_to=destination,
            date_from=flight_data["departure_at"],
            date_to=flight_data.get("return_at"),
            transfers_cnt=flight_data["transfers"],
            one_way=one_way,
            price=flight_data["price"],
            days_between=days_between
        )
        
        self.session.add(flight)
        await self.session.commit()

    async def scan_routes(self):
        today = datetime.now()
        dates = [(today + timedelta(days=i)).strftime("%Y-%m-%d") 
                for i in range(1, self.config.DAYS_AHEAD + 1)]
        
        # Прямой поиск
        for origin in self.config.ORIGINS:
            for destination in self.config.DESTINATIONS:
                # One-way
                for date in dates:
                    flights = await self.get_flight_prices(origin, destination, date)
                    for flight in flights:
                        await self.process_flight_data(flight, True, origin, destination)
                
                # Round-trip
                for date in dates:
                    for days_between in self.config.ROUND_TRIP_DAYS:
                        return_date = (datetime.strptime(date, "%Y-%m-%d") + 
                                     timedelta(days=days_between)).strftime("%Y-%m-%d")
                        flights = await self.get_flight_prices(
                            origin, destination, date, return_date)
                        for flight in flights:
                            await self.process_flight_data(flight, False, origin, destination) 