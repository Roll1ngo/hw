import platform
import aiohttp
import asyncio
from datetime import datetime, timedelta
import argparse
from rich import print


parser = argparse.ArgumentParser(
    description="App for get exchange rate USD and EUR from Privatbank UA"
)
parser.add_argument("-d", "--days", required=True)
args = vars(parser.parse_args())
numbers_of_days = args.get("days")


class TheLimitOfMaximumDay(Exception):
    ...


class NotIntegerArgument(Exception):
    ...


if not numbers_of_days:
    numbers_of_days = 1
try:
    if int(numbers_of_days) > 10:
        raise TheLimitOfMaximumDay("Can show you maximum amount is 10 days")
except ValueError:
    raise NotIntegerArgument("Input integer from 1 to 10")


async def get_request(date: int) -> dict:
    url = f"https://api.privatbank.ua/p24api/exchange_rates?json&date={date}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                else:
                    print(f"Error status: {response.status} for {url}")
                return result
        except aiohttp.ClientConnectorError as err:
            print(f"Connection error: {url}", str(err))


async def create_task(dates: list) -> asyncio.futures:
    tasks = []
    for date in dates:
        tasks.append(asyncio.create_task(get_request(date)))
    result = await asyncio.gather(*tasks)
    return result


def get_dates_range(start_date: str, end_date: str) -> list:
    start_date = datetime.strptime(start_date, "%d.%m.%Y")
    end_date = datetime.strptime(end_date, "%d.%m.%Y")
    delta = timedelta(days=1)
    dates_list = []

    while start_date <= end_date:
        dates_list.append(start_date.strftime("%d.%m.%Y"))
        start_date += delta

    return dates_list


def get_exchange_rate(data: list, currency_code: str) -> str:
    for rate in data["exchangeRate"]:
        if rate["currency"] == currency_code:
            return rate["purchaseRate"], rate["saleRate"]
    return None


def console_output(dates_list: list, responses_list: list):
    for date, rates in zip(dates_list, responses_list):
        if rates:
            eur_buy, eur_sale = get_exchange_rate(rates, "EUR")
            usd_buy, usd_sale = get_exchange_rate(rates, "USD")
            print(
                f"Date: {date}| EUR Buy: {eur_buy},EUR Sale: {eur_sale}| USD Buy: {usd_buy},USD Sale:{usd_sale}|"
            )
        else:
            print(f"Date: {date}, Data not available")


async def main() -> None:
    print(int(numbers_of_days))
    start_date = (datetime.now() - timedelta(days=int(numbers_of_days) - 1)).strftime(
        "%d.%m.%Y"
    )
    end_date = datetime.now().strftime("%d.%m.%Y")

    dates_list = get_dates_range(start_date, end_date)
    responses_list = await create_task(dates_list)

    console_output(dates_list, responses_list)

    return "Finish"


if __name__ == "__main__":
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    r = asyncio.run(main())

    print(r)
