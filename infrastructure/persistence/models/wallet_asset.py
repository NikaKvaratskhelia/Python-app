from sqlalchemy import Column, Integer, Numeric, String, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base


class WalletAssetModel(Base):
    __tablename__ = "wallet_assets"

    id = Column(Integer, primary_key=True, index=True)
    
    wallet_id = Column(
        Integer, ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False
    )
    
    symbol = Column(String(10), nullable=False)
    amount = Column(Numeric(precision=18, scale=8), default=0.00000000, nullable=False)
    
    average_buy_price = Column(
        Numeric(precision=18, scale=2), default=0.00, nullable=False
    )

    wallet = relationship("WalletModel", back_populates="assets")
