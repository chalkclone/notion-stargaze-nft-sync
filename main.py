import os
import requests
import json
from notion_client import Client

# Получение переменных окружения
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
    url = "https://graphql.mainnet.stargaze-apis.com/graphql"
    query = {
        "query": """
        query($owner: String!) {
          tokens(owner: $owner) {
            collectionAddr
            tokenId
            tokenURI
            owner { address }
          }
        }
        """,
        "variables": {"owner": STARGAZE_ADDRESS}
    }
    print(f"🔗 GraphQL: {url} → owner={STARGAZE_ADDRESS}")
    r = requests.post(url, json=query)
    r.raise_for_status()
    data = r.json().get("data", {}).get("tokens", [])
    print(f"📦 Получено NFT: {len(data)}")
    return data

def get_prices():
    ids = ",".join(COINGECKO_IDS.values())
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd"
    print(f"🔗 Запрос курсов CoinGecko: {url}")
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    prices = {sym.upper(): data.get(api_id, {}).get("usd", 0) for sym, api_id in COINGECKO_IDS.items()}
    print(f"💱 Курсы получены: {prices}")
    return prices

def upsert_nfts(nfts, prices):
    for nft in nfts:
        token_id = nft.get("tokenId")
        token_uri = nft.get("tokenURI")
        if not token_uri:
            continue

        try:
            meta = requests.get(token_uri)
            meta.raise_for_status()
            meta = meta.json()
        except Exception as e:
            print(f"❌ Ошибка при загрузке метаданных: {e}")
            continue

        name = meta.get("name", "NFT") + f" #{token_id}"
        image = meta.get("image", "")

        # MOCK цены, можно заменить позже на real
        currency = "STARS"
        amount = 100.0
        sender = nft.get("owner", {}).get("address", "unknown")
        price_usd = round(amount * prices.get(currency, 0), 2)

        print(f"➕ Добавление {name}")

        try:
            notion.pages.create(
                parent={"database_id": NOTION_DB_ID},
                properties={
                    "Name": {"title": [{"text": {"content": name}}]},
                    "Currency": {"select": {"name": currency}},
                    "Price (token)": {"number": amount},
                    "Price (USD)": {"number": price_usd},
                    "Sender": {"rich_text": [{"text": {"content": sender}}]}
                },
                cover={"external": {"url": image}} if image else None
            )
        except Exception as e:
            print(f"⚠️ Ошибка Notion: {e}")


def main():
    print("\n🚀 Запуск синхронизации Stargaze → Notion")
    try:
        nfts = get_nfts()
    except Exception as e:
        print(f"❌ Ошибка получения NFT: {e}")
        nfts = []

    prices = get_prices()

    if not nfts:
        print("⚠️ Нет данных для синхронизации")
    else:
        upsert_nfts(nfts, prices)

    print("🌟 Синхронизация завершена")

if __name__ == "__main__":
    main()

