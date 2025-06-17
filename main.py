import os
import requests
import json
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
    url = f"https://rest.stargaze-apis.com/cosmos/nft/v1beta1/nfts?owner={STARGAZE_ADDRESS}"
    r = requests.get(url)
    return r.json().get("nfts", [])

def get_prices():
    ids = ",".join(COINGECKO_IDS.values())
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd"
    r = requests.get(url)
    data = r.json()
    return {sym.upper(): data.get(api_id, {}).get("usd", 0) for sym, api_id in COINGECKO_IDS.items()}

def upsert_nfts(nfts, prices):
    for nft in nfts:
        token_id = nft.get("token_id")
        token_uri = nft.get("token_uri")
        if not token_uri:
            continue
        meta = requests.get(token_uri).json()
        name = meta.get("name", "NFT") + f" #{token_id}"
        image = meta.get("image", "")

        # MOCK: вставка тестовых данных (так как marketplace API защищён)
        currency = "STARS"
        amount = 100.0
        sender = "unknown"
        price_usd = amount * prices.get(currency, 0)

        notion.pages.create(
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

def main():
    nfts = get_nfts()
    prices = get_prices()
    upsert_nfts(nfts, prices)

if __name__ == "__main__":
    main()
