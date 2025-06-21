import os
import requests
from notion_client import Client

# Константы из переменных окружения
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DB_ID = os.getenv("NOTION_DB_ID")
STARGAZE_ADDRESS = os.getenv("STARGAZE_ADDRESS")

notion = Client(auth=NOTION_TOKEN)

COINGECKO_IDS = {
    "stars": "stargaze",
    "atom": "cosmos",
    "osmo": "osmosis",
    "tia": "celestia",
    "usdc": "usd-coin",
    "btc": "bitcoin",
}

def get_nfts():
    # MOCK: Возвращаем фиктивный NFT
    return [{
        "token_id": "123",
        "token_uri": "https://ipfs.io/ipfs/Qm.../metadata.json"
    }]


def get_prices():
    ids = ",".join(COINGECKO_IDS.values())
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd"
    print(f"🔗 Запрос курсов CoinGecko: {url}")
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        prices = {sym.upper(): data.get(api_id, {}).get("usd", 0) for sym, api_id in COINGECKO_IDS.items()}
        print(f"💱 Курсы получены: {prices}")
        return prices
    except Exception as e:
        print(f"❌ Ошибка получения курсов: {e}")
        return {}

def upsert_nfts(nfts, prices):
    for nft in nfts:
        token_id = nft.get("token_id")
        token_uri = nft.get("token_uri")
        print(f"🧙‍♂️ Обрабатываем NFT {token_id}")

        if not token_uri:
            print("⚠️ Пропущен NFT без token_uri")
            continue

        try:
            meta = requests.get(token_uri).json()
            name = meta.get("name", "NFT") + f" #{token_id}"
            image = meta.get("image", "")

            # MOCK: фиктивные данные, пока нет маркетплейса
            currency = "STARS"
            amount = 100.0
            sender = "unknown"
            price_usd = amount * prices.get(currency, 0)

            response = notion.pages.create(
                parent={"database_id": NOTION_DB_ID},
                properties={
                    "Name": {"title": [{"text": {"content": name}}]},
                    "Currency": {"select": {"name": currency}},
                    "Price (token)": {"number": amount},
                    "Price (USD)": {"number": price_usd},
                    "Sender": {"rich_text": [{"text": {"content": sender}}]}
                },
                cover={"external": {"url": image}}
            )
            print(f"✅ Добавлено в Notion: {name}")
        except Exception as e:
            print(f"❌ Ошибка добавления NFT {token_id} в Notion: {e}")

def main():
    print("🚀 Запуск синхронизации Stargaze → Notion")

    if not NOTION_TOKEN or not NOTION_DB_ID or not STARGAZE_ADDRESS:
        print("❌ Не заданы переменные окружения! Проверь NOTION_TOKEN, NOTION_DB_ID, STARGAZE_ADDRESS")
        return

    nfts = get_nfts()
    prices = get_prices()

    if nfts and prices:
        upsert_nfts(nfts, prices)
    else:
        print("⚠️ Нет данных для синхронизации")

    print("🌟 Синхронизация завершена")

if __name__ == "__main__":
    main()

