# feat(test): comprehensive unit tests for state manager
import pytest
import asyncio
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.state_manager import StateManager, Order, Position

@pytest.fixture
async def state_manager():
    """Create a test state manager with in-memory database."""
    sm = StateManager("sqlite+aiosqlite:///:memory:")
    await sm.init_models()
    return sm

@pytest.fixture
async def sample_order():
    """Create a sample order for testing."""
    return Order(
        id="test-order-1",
        symbol="BTCUSDT",
        side="BUY",
        quantity=Decimal("0.1"),
        status="PENDING"
    )

@pytest.mark.asyncio
async def test_state_manager_init(state_manager):
    """Test state manager initialization."""
    assert state_manager.database_url == "sqlite+aiosqlite:///:memory:"
    assert state_manager.engine is not None
    assert state_manager.Session is not None

@pytest.mark.asyncio
async def test_create_order(state_manager, sample_order):
    """Test creating an order in the database."""
    async with state_manager.Session() as session:
        session.add(sample_order)
        await session.commit()
        
        # Retrieve the order
        retrieved_order = await session.get(Order, "test-order-1")
        assert retrieved_order is not None
        assert retrieved_order.symbol == "BTCUSDT"
        assert retrieved_order.side == "BUY"
        assert retrieved_order.quantity == Decimal("0.1")
        assert retrieved_order.status == "PENDING"

@pytest.mark.asyncio
async def test_set_order_status(state_manager, sample_order):
    """Test updating order status."""
    # Create order first
    async with state_manager.Session() as session:
        session.add(sample_order)
        await session.commit()
    
    # Update status
    await state_manager.set_order_status("test-order-1", "SUBMITTED", "broker-123")
    
    # Verify update
    async with state_manager.Session() as session:
        order = await session.get(Order, "test-order-1")
        assert order.status == "SUBMITTED"
        assert order.broker_order_id == "broker-123"

@pytest.mark.asyncio
async def test_set_order_status_not_found(state_manager):
    """Test updating status of non-existent order."""
    with pytest.raises(ValueError, match="Order non-existent not found"):
        await state_manager.set_order_status("non-existent", "SUBMITTED")

@pytest.mark.asyncio
async def test_position_model():
    """Test position model creation and attributes."""
    position = Position(
        symbol="ETHUSDT",
        size=Decimal("2.5"),
        avg_price=Decimal("2000.0")
    )
    
    assert position.symbol == "ETHUSDT"
    assert position.size == Decimal("2.5")
    assert position.avg_price == Decimal("2000.0")
    assert position.id is not None

@pytest.mark.asyncio
async def test_order_model_defaults():
    """Test order model default values."""
    order = Order(
        symbol="BTCUSDT",
        side="BUY",
        quantity=Decimal("1.0")
    )
    
    assert order.status == "PENDING"
    assert order.filled_quantity == Decimal("0")
    assert order.metadata == {}
    assert order.id is not None
    assert order.created_at is not None

@pytest.mark.asyncio
async def test_multiple_orders(state_manager):
    """Test creating multiple orders."""
    orders = [
        Order(id=f"order-{i}", symbol="BTCUSDT", side="BUY", quantity=Decimal("0.1"))
        for i in range(3)
    ]
    
    async with state_manager.Session() as session:
        for order in orders:
            session.add(order)
        await session.commit()
        
        # Verify all orders exist
        for i in range(3):
            order = await session.get(Order, f"order-{i}")
            assert order is not None
            assert order.symbol == "BTCUSDT"

@pytest.mark.asyncio
async def test_position_unique_symbol(state_manager):
    """Test that positions have unique symbols."""
    position1 = Position(symbol="BTCUSDT", size=Decimal("1.0"))
    position2 = Position(symbol="BTCUSDT", size=Decimal("2.0"))
    
    async with state_manager.Session() as session:
        session.add(position1)
        await session.commit()
        
        # Adding second position with same symbol should fail
        session.add(position2)
        with pytest.raises(Exception):  # SQLAlchemy will raise an integrity error
            await session.commit()