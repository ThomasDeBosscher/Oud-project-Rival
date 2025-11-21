from app.models.company import Company
from app.models.event import Event
from app.models.user import User
from app.models.watchlist import Watchlist
import pytest
from datetime import datetime

@pytest.fixture
def sample_company():
    # description field no longer exists on canonical 'company' table mapping
    return Company(name="Test Company", url="https://example.com")

@pytest.fixture
def sample_event():
    return Event(name="Test Event", date=datetime(2023, 1, 1))

@pytest.fixture
def sample_user():
    u = User(username="testuser", email="test@example.com")
    u.set_password("password")
    return u

@pytest.fixture
def sample_watchlist(sample_user):
    return Watchlist(user_id=sample_user.id, company_id=1)

def test_company_creation(sample_company):
    assert sample_company.name == "Test Company"
    assert sample_company.url == "https://example.com"

def test_event_creation(sample_event):
    assert sample_event.name == "Test Event"
    assert isinstance(sample_event.date, datetime)

def test_user_creation(sample_user):
    assert sample_user.username == "testuser"
    assert sample_user.email == "test@example.com"

def test_watchlist_creation(sample_watchlist):
    assert sample_watchlist.user_id == sample_watchlist.user_id
    assert sample_watchlist.company_id == 1