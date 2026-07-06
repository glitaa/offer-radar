import pytest
from src.domain.models import Offer, OfferPrice, OfferUrl, OfferStatus, Settings

def test_offer_price_instantiation():
    price = OfferPrice(price_min=100.0, price_max=200.0, currency="PLN", period="month", special_status="negotiable")
    assert price.price_min == 100.0
    assert price.price_max == 200.0
    assert price.currency == "PLN"
    assert price.period == "month"
    assert price.special_status == "negotiable"

def test_compute_fingerprint_normalization():
    price1 = OfferPrice(price_min=100.0, currency="PLN")
    price2 = OfferPrice(price_min=100.0, currency="PLN")
    offer1 = Offer(
        title="Beautiful Apartment! ",
        description="  Very nice, clean.",
        price=price1
    )
    offer2 = Offer(
        title="beautiful apartment",
        description="very nice clean",
        price=price2
    )
    
    assert offer1.fingerprint != ""
    assert offer1.fingerprint == offer2.fingerprint

def test_compute_fingerprint_handles_nones():
    offer = Offer(
        title="Minimal Offer"
    )
    assert offer.description is None
    assert offer.price is None
    assert offer.fingerprint != ""

def test_post_init_fingerprint_generation():
    offer_auto = Offer(title="Auto fingerprint")
    assert offer_auto.fingerprint != ""
    
    offer_manual = Offer(title="Manual fingerprint", fingerprint="12345")
    assert offer_manual.fingerprint == "12345"

def test_settings_default_instantiation():
    settings = Settings()
    assert settings.language == "en"
    assert settings.auto_open_browser is True
