import asyncio
from scraper.telegram_scraper import TelegramScraper


async def main():
    scraper = TelegramScraper()
    try:
        await scraper.connect()
        if scraper.client and scraper.client.is_connected():
            print("CONEXION_OK")
        else:
            print("CONEXION_FALLIDA")
    except Exception:
        print("CONEXION_FALLIDA")
    finally:
        try:
            await scraper.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
