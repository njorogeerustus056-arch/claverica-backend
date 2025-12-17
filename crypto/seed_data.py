from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from crypto_models import CryptoAsset, FiatPlatform
from datetime import datetime

def seed_crypto_assets(db: Session):
    assets_data = [
        {"symbol": "BTC", "name": "Bitcoin", "logo": "₿", "blockchain": "bitcoin", "current_price_usd": 68420.00, "change_24h": 2.5, "market_cap": 1340000000000, "volume_24h": 45000000000},
        {"symbol": "ETH", "name": "Ethereum", "logo": "Ξ", "blockchain": "ethereum", "current_price_usd": 3812.00, "change_24h": 1.2, "market_cap": 458000000000, "volume_24h": 20000000000},
        {"symbol": "USDT", "name": "Tether", "logo": "₮", "blockchain": "ethereum", "current_price_usd": 1.0001, "change_24h": 0.01, "market_cap": 95000000000, "volume_24h": 55000000000},
        {"symbol": "USDC", "name": "USD Coin", "logo": "💵", "blockchain": "ethereum", "current_price_usd": 1.0000, "change_24h": 0.00, "market_cap": 32000000000, "volume_24h": 8000000000},
        {"symbol": "BNB", "name": "Binance Coin", "logo": "🟡", "blockchain": "binance_smart_chain", "current_price_usd": 412.50, "change_24h": 3.2, "market_cap": 63000000000, "volume_24h": 2000000000},
        {"symbol": "SOL", "name": "Solana", "logo": "🔵", "blockchain": "solana", "current_price_usd": 142.50, "change_24h": 3.8, "market_cap": 65000000000, "volume_24h": 4000000000},
        {"symbol": "ADA", "name": "Cardano", "logo": "🟣", "blockchain": "cardano", "current_price_usd": 0.62, "change_24h": -1.5, "market_cap": 22000000000, "volume_24h": 800000000},
        {"symbol": "DOGE", "name": "Dogecoin", "logo": "🐶", "blockchain": "dogecoin", "current_price_usd": 0.18, "change_24h": 5.2, "market_cap": 25000000000, "volume_24h": 1500000000},
        {"symbol": "MATIC", "name": "Polygon", "logo": "🔷", "blockchain": "polygon", "current_price_usd": 0.92, "change_24h": 2.1, "market_cap": 9000000000, "volume_24h": 500000000},
        {"symbol": "SHIB", "name": "Shiba Inu", "logo": "🦴", "blockchain": "ethereum", "current_price_usd": 0.000024, "change_24h": -2.3, "market_cap": 14000000000, "volume_24h": 800000000},
    ]
    
    for asset_data in assets_data:
        existing = db.query(CryptoAsset).filter(CryptoAsset.symbol == asset_data["symbol"]).first()
        if not existing:
            asset = CryptoAsset(**asset_data)
            db.add(asset)
    
    db.commit()
    print("✅ Crypto assets seeded")

def seed_fiat_platforms(db: Session):
    platforms_data = [
        {
            "name": "Monzo",
            "logo": "🏦",
            "platform_type": "bank",
            "supported_currencies": ["GBP", "EUR"],
            "supported_countries": ["UK", "EU"],
            "supports_deposits": True,
            "supports_withdrawals": True,
            "deposit_fee": 0.0,
            "withdrawal_fee": 0.0,
            "deposit_processing_time": "instant",
            "withdrawal_processing_time": "1-3 days"
        },
        {
            "name": "Wise",
            "logo": "💳",
            "platform_type": "payment",
            "supported_currencies": ["USD", "EUR", "GBP"],
            "supported_countries": ["Global"],
            "supports_deposits": True,
            "supports_withdrawals": True,
            "deposit_fee": 0.5,
            "withdrawal_fee": 1.0,
            "deposit_processing_time": "1-2 days",
            "withdrawal_processing_time": "1-3 days"
        },
        {
            "name": "Skrill",
            "logo": "💰",
            "platform_type": "payment",
            "supported_currencies": ["USD", "EUR", "GBP"],
            "supported_countries": ["Global"],
            "supports_deposits": True,
            "supports_withdrawals": True,
            "deposit_fee": 1.0,
            "withdrawal_fee": 2.0,
            "deposit_processing_time": "instant",
            "withdrawal_processing_time": "1-2 days"
        },
        {
            "name": "Revolut",
            "logo": "🔄",
            "platform_type": "bank",
            "supported_currencies": ["USD", "EUR", "GBP"],
            "supported_countries": ["Global"],
            "supports_deposits": True,
            "supports_withdrawals": True,
            "deposit_fee": 0.0,
            "withdrawal_fee": 0.0,
            "deposit_processing_time": "instant",
            "withdrawal_processing_time": "1-2 days"
        },
    ]
    
    for platform_data in platforms_data:
        existing = db.query(FiatPlatform).filter(FiatPlatform.name == platform_data["name"]).first()
        if not existing:
            platform = FiatPlatform(**platform_data)
            db.add(platform)
    
    db.commit()
    print("✅ Fiat platforms seeded")

def seed_all():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_crypto_assets(db)
        seed_fiat_platforms(db)
        print("✅ All data seeded successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    seed_all()
