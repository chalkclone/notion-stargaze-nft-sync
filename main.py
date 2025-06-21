import os
import requests
import json
from notion_client import Client

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
    print("\n🔗 GraphQL: https://graphql.mainnet.stargaze-apis.com/graphql → owner=", STARGAZE_ADDRESS)
    url = "https://graphql.mainnet.stargaze-apis.com/graphql"
    headers = {"Content-Type": "application/json"}
    query = {
        "query": """
        query GetNFTs($owner: String!) {
            nfts(owner: $owner) {
                tokens {
                    id
                    tokenId
                    name
                    image
                }
            }
        }
        """,
        "variables": {"owner": STARGAZE_ADDRESS}
    }
    try:
        r = requests.post(url, headers=headers, data=json.dumps(query))
        r.raise_for_status()
        data = r.json()
        return data.get("data", {}).get("nfts", {}).get("tokens", [])
    except Exception as e:
        print(f"❌ Ошибка получения NFT: {e}")
        return []

def get_prices():
    ids = ",".join(COINGECKO_IDS.values())
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd"
    try:
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        prices = {sym.upper(): data.get(api_id, {}).get("usd", 0) for sym, api_id in COINGECKO_IDS.items()}
        print("💱 Курсы получены:", prices)
        return prices
    except Exception as e:
        print(f"❌ Ошибка получения курсов: {e}")
        return {}

def upsert_nfts(nfts, prices):
    if not nfts:
        print("⚠️ Нет данных для синхронизации")
        return

    print(f"📥 Обработка {len(nfts)} NFT...")
    for nft in nfts:
        name = nft.get("name") or f"NFT #{nft.get('tokenId')}"
        token_id = nft.get("tokenId")
        image = nft.get("image")

        currency = "STARS"
        amount = 100.0  # Мокаем, так как цену с маркетплейса не получить
        sender = STARGAZE_ADDRESS
        price_usd = amount * prices.get(currency, 0)

        try:
            notion.pages.create(
                parent={"database_id": NOTION_DB_ID},
                properties={
                    "Name": {"title": [{"text": {"content": name}}]},
                    "Currency": {"select": {"name": currency}},
                    "Price (token)": {"number": amount},
                    "Price (USD)": {"number": price_usd},
                    "Sender": {"rich_text": [{"text": {"content": sender}}]},
                },
                cover={"external": {"url": image}} if image else None,
            )
            print(f"✅ Добавлен: {name}")
        except Exception as e:
            print(f"❌ Ошибка добавления {name}: {e}")

def main():
    print("\n🚀 Запуск синхронизации Stargaze → Notion")
    nfts = get_nfts()
    prices = get_prices()
    upsert_nfts(nfts, prices)
    print("🌟 Синхронизация завершена")

if __name__ == "__main__":
    main()

