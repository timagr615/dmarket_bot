import enum
from datetime import datetime
from typing import List, Union
from pydantic import BaseModel


class Games(enum.Enum):
    CS = 'a8db'
    DOTA = '9a92'
    RUST = 'rust'
    TF2 = 'tf2'


class Balance(BaseModel):
    usd: int


class LastPrice(BaseModel):
    Currency: str
    Amount: float


class LastSale(BaseModel):
    Date: datetime
    Price: LastPrice


class LastSales(BaseModel):
    LastSales: List[LastSale]


class SaleHistory(BaseModel):
    Prices: List[Union[int, str]]
    Items: List[int]
    Labels: List[datetime]


class SalesHistory(BaseModel):
    SalesHistory: SaleHistory


class MarketOfferPrice(BaseModel):
    DMC: Union[int, str]
    USD: Union[int, str]


class MarketOfferExtra(BaseModel):
    categoryPath: str = None
    name: str = None
    title: str = None
    category: str = None
    gameId: Games
    groupId: int = None
    tradeLock: int = None
    rarity: str = None
    exterior: str = None
    type: str = None
    stickers: list = None


class MarketOffer(BaseModel):
    itemId: str
    type: str
    amount: int
    image: str
    classId: str
    gameId: str
    inMarket: bool
    lockStatus: bool
    title: str
    slug: str
    status: str
    discount: int
    price: MarketOfferPrice
    suggestedPrice: MarketOfferPrice
    extra: MarketOfferExtra
    fees: dict


class MarketOffers(BaseModel):
    cursor: str = None
    objects: List[MarketOffer]


class AggregatedOffer(BaseModel):
    BestPrice: float
    Count: int


class AggregatedTitle(BaseModel):
    MarketHashName: str
    Offers: AggregatedOffer
    Orders: AggregatedOffer


class AggregatedPrices(BaseModel):
    AggregatedTitles: List[AggregatedTitle]


class TargetAttributes(BaseModel):
    Name: str = None
    Value: str = None


class Target(BaseModel):
    TargetID: str
    Title: str
    Amount: str
    Status: str
    GameID: Games
    GameType: str = None
    Attributes: List[TargetAttributes]
    Price: LastPrice


class UserTargets(BaseModel):
    Items: List[Target]
    Total: int
    Cursor: str


class ClosedTarget(BaseModel):
    OfferID: str
    TargetID: str
    AssetID: str
    Price: LastPrice
    Amount: int


class ClosedTargets(BaseModel):
    Trades: List[ClosedTarget]
    Total: int


class CreateTarget(BaseModel):
    Amount: str
    Price: LastPrice
    Attributes: List[TargetAttributes]


class CreateTargets(BaseModel):
    Targets: List[CreateTarget]


class Offer(BaseModel):
    OfferID: str
    Price: LastPrice
    Fee: LastPrice = None
    CreatedDate: str


class UserItem(BaseModel):
    AssetID: str
    VariantID: str
    Title: str
    ImageURL: str
    GameID: str
    GameType: str
    Location: str
    Withdrawable: bool
    Depositable: bool
    Tradable: bool
    Attributes: List[TargetAttributes]
    Offer: Offer
    Fee: LastPrice = None
    MarketPrice: LastPrice = None
    ClassID: str


class UserItems(BaseModel):
    Items: List[UserItem]
    Total: str
    Cursor: str = None


class CreateOffer(BaseModel):
    AssetID: str
    Price: LastPrice


class EditOffer(CreateOffer):
    OfferID: str


class CreateOffers(BaseModel):
    Offers: List[CreateOffer]


class CreateOfferResponse(BaseModel):
    CreateOffer: CreateOffer
    OfferID: str
    Successful: bool


class CreateOffersResponse(BaseModel):
    Result: List[CreateOfferResponse]


class EditOffers(BaseModel):
    Offers: List[EditOffer]


class EditOfferResponse(BaseModel):
    EditOffer: CreateOffer
    Successful: bool
    NewOfferID: str


class EditOffersResponse(BaseModel):
    Result: List[EditOfferResponse]


class DeleteOffer(BaseModel):
    itemId: str
    offerId: str
    price: LastPrice


class DeleteOffers(BaseModel):
    force: bool = True
    objects: List[DeleteOffer]


class SkinHistory(LastSales):
    game: str
    title: str
    avg_price: float
    update_time: datetime

    class Config:
        orm_mode = True


class SkinOrder(BaseModel):
    title: str
    game: Games
    bestOrder: int = None
    maxPrice: int = None
    minPrice: int = None
    targetId: str = None


class SellOffer(BaseModel):
    AssetID: str
    title: str = None
    game: str = None
    OfferID: str = None
    sellTime: datetime = None
    buyPrice: float = None
    sellPrice: float = None
    buyTime: datetime = datetime.now()
    fee: int = 7

    class Config:
        orm_mode = True


class CumulativePrice(BaseModel):
    Price: float
    Level: int
    Amount: int


class CumulativePrices(BaseModel):
    Offers: List[CumulativePrice]
    Targets: List[CumulativePrice]
    UpdatedAt: int


class OfferDetails(BaseModel):
    items: List[str]


class OfferDetailPrice(BaseModel):
    amount: int
    currency: str


class OfferDetail(BaseModel):
    itemId: str
    steamMarketPrice: OfferDetailPrice
    minListedPrice: OfferDetailPrice
    offersOnMarketplace: int


class OfferDetailsResponse(BaseModel):
    objects: List[OfferDetail]
