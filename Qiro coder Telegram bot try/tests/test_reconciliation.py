# feat(test): comprehensive unit tests for reconciliation job
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
from src.core.reconciliation import ReconciliationJob
from src.core.state_manager import StateManager, Order, Position
from src.connectors.bingx_client import BingXClient
from src.utils.audit_logger import AuditLogger
from src.utils.metrics import MetricsCollector

@pytest.fixture
async def state_manager():
    """Create a test state manager."""
    sm = StateManager("sqlite+aiosqlite:///:memory:")
    await sm.init_models()
    return sm

@pytest.fixture
def mock_bingx_client():
    """Create a mock BingX client."""
    return AsyncMock(spec=BingXClient)

@pytest.fixture
def mock_audit_logger():
    """Create a mock audit logger."""
    return AsyncMock(spec=AuditLogger)

@pytest.fixture
def mock_metrics():
    """Create a mock metrics collector."""
    return MagicMock(spec=MetricsCollector)

@pytest.fixture
async def reconciliation_job(state_manager, mock_bingx_client, mock_audit_logger, mock_metrics):
    """Create a reconciliation job for testing."""
    return ReconciliationJob(state_manager, mock_bingx_client, mock_audit_logger, mock_metrics)

@pytest.fixture
async def submitted_order(state_manager):
    """Create a submitted order in the database."""
    order = Order(
        id="test-order-1",
        symbol="BTCUSDT",
        side="BUY",
        quantity=Decimal("0.1"),
        status="SUBMITTED",
        broker_order_id="broker-123"
    )
    
    async with state_manager.Session() as session:
        session.add(order)
        await session.commit()
    
    return order

@pytest.mark.asyncio
async def test_reconciliation_job_init(reconciliation_job):
    """Test reconciliation job initialization."""
    assert reconciliation_job.state_manager is not None
    assert reconciliation_job.bingx_client is not None
    assert reconciliation_job.audit_logger is not None
    assert reconciliation_job.metrics is not None
    assert reconciliation_job.running is False
    assert reconciliation_job.interval == 30

@pytest.mark.asyncio
async def test_start_and_stop(reconciliation_job):
    """Test starting and stopping the reconciliation job."""
    # Start the job
    start_task = asyncio.create_task(reconciliation_job.start())
    await asyncio.sleep(0.1)  # Let it start
    
    assert reconciliation_job.running is True
    
    # Stop the job
    await reconciliation_job.stop()
    assert reconciliation_job.running is False
    
    # Wait for the task to complete
    start_task.cancel()
    try:
        await start_task
    except asyncio.CancelledError:
        pass

def test_map_exchange_status(reconciliation_job):
    """Test exchange status mapping."""
    assert reconciliation_job._map_exchange_status("NEW") == "SUBMITTED"
    assert reconciliation_job._map_exchange_status("FILLED") == "FILLED"
    assert reconciliation_job._map_exchange_status("CANCELED") == "CANCELLED"
    assert reconciliation_job._map_exchange_status("REJECTED") == "REJECTED"
    assert reconciliation_job._map_exchange_status("EXPIRED") == "EXPIRED"
    assert reconciliation_job._map_exchange_status("PARTIALLY_FILLED") == "PARTIALLY_FILLED"
    assert reconciliation_job._map_exchange_status("UNKNOWN_STATUS") == "UNKNOWN"

@pytest.mark.asyncio
async def test_reconcile_single_order_success(reconciliation_job, submitted_order, mock_bingx_client):
    """Test successful reconciliation of a single order."""
    # Mock successful exchange response
    mock_bingx_client.get_order.return_value = {
        "status": "ok",
        "data": {
            "orderId": "broker-123",
            "status": "FILLED",
            "executedQty": "0.1"
        }
    }
    
    await reconciliation_job._reconcile_single_order(submitted_order)
    
    # Verify exchange was called
    mock_bingx_client.get_order.assert_called_once_with("BTCUSDT", "broker-123")
    
    # Verify audit log was called
    reconciliation_job.audit_logger.log.assert_called()
    
    # Verify metrics were incremented
    reconciliation_job.metrics.increment_counter.assert_called_with("orders_reconciled_total")
    
    # Verify order status was updated in database
    async with reconciliation_job.state_manager.Session() as session:
        order = await session.get(Order, "test-order-1")
        assert order.status == "FILLED"
        assert order.filled_quantity == Decimal("0.1")

@pytest.mark.asyncio
async def test_reconcile_single_order_exchange_error(reconciliation_job, submitted_order, mock_bingx_client):
    """Test reconciliation with exchange error."""
    # Mock exchange error response
    mock_bingx_client.get_order.return_value = {
        "status": "error",
        "data": {"msg": "Order not found"}
    }
    
    await reconciliation_job._reconcile_single_order(submitted_order)
    
    # Verify exchange was called
    mock_bingx_client.get_order.assert_called_once_with("BTCUSDT", "broker-123")
    
    # Verify error was logged
    reconciliation_job.audit_logger.log.assert_called()
    
    # Verify order status was NOT updated
    async with reconciliation_job.state_manager.Session() as session:
        order = await session.get(Order, "test-order-1")
        assert order.status == "SUBMITTED"  # Should remain unchanged

@pytest.mark.asyncio
async def test_reconcile_single_order_no_broker_id(reconciliation_job):
    """Test reconciliation of order without broker ID."""
    order = Order(
        id="test-order-2",
        symbol="BTCUSDT",
        side="BUY",
        quantity=Decimal("0.1"),
        status="SUBMITTED",
        broker_order_id=None
    )
    
    await reconciliation_job._reconcile_single_order(order)
    
    # Should return early without calling exchange
    reconciliation_job.bingx_client.get_order.assert_not_called()

@pytest.mark.asyncio
async def test_reconcile_orders(reconciliation_job, state_manager, mock_bingx_client):
    """Test reconciling multiple orders."""
    # Create multiple submitted orders
    orders = []
    for i in range(3):
        order = Order(
            id=f"test-order-{i}",
            symbol="BTCUSDT",
            side="BUY",
            quantity=Decimal("0.1"),
            status="SUBMITTED",
            broker_order_id=f"broker-{i}"
        )
        orders.append(order)
    
    async with state_manager.Session() as session:
        for order in orders:
            session.add(order)
        await session.commit()
    
    # Mock exchange responses
    mock_bingx_client.get_order.return_value = {
        "status": "ok",
        "data": {"orderId": "broker-123", "status": "FILLED", "executedQty": "0.1"}
    }
    
    await reconciliation_job._reconcile_orders()
    
    # Should have called exchange for each order
    assert mock_bingx_client.get_order.call_count == 3

@pytest.mark.asyncio
async def test_update_position_for_order_new_position(reconciliation_job, state_manager):
    """Test updating position for a new symbol."""
    order = Order(
        id="test-order-1",
        symbol="ETHUSDT",
        side="BUY",
        quantity=Decimal("1.0"),
        filled_quantity=Decimal("1.0"),
        price=Decimal("2000.0"),
        status="FILLED"
    )
    
    await reconciliation_job._update_position_for_order(order)
    
    # Verify position was created
    async with state_manager.Session() as session:
        from sqlalchemy import select
        result = await session.execute(select(Position).where(Position.symbol == "ETHUSDT"))
        position = result.scalar_one_or_none()
        
        assert position is not None
        assert position.symbol == "ETHUSDT"
        assert position.size == Decimal("1.0")
        assert position.avg_price == Decimal("2000.0")

@pytest.mark.asyncio
async def test_update_position_for_order_existing_position(reconciliation_job, state_manager):
    """Test updating an existing position."""
    # Create existing position
    existing_position = Position(
        symbol="BTCUSDT",
        size=Decimal("1.0"),
        avg_price=Decimal("50000.0")
    )
    
    async with state_manager.Session() as session:
        session.add(existing_position)
        await session.commit()
    
    # Create new order that adds to position
    order = Order(
        id="test-order-1",
        symbol="BTCUSDT",
        side="BUY",
        quantity=Decimal("0.5"),
        filled_quantity=Decimal("0.5"),
        price=Decimal("60000.0"),
        status="FILLED"
    )
    
    await reconciliation_job._update_position_for_order(order)
    
    # Verify position was updated
    async with state_manager.Session() as session:
        from sqlalchemy import select
        result = await session.execute(select(Position).where(Position.symbol == "BTCUSDT"))
        position = result.scalar_one_or_none()
        
        assert position is not None
        assert position.size == Decimal("1.5")  # 1.0 + 0.5
        # Average price should be calculated: (1.0 * 50000 + 0.5 * 60000) / 1.5 = 53333.33...
        assert position.avg_price > Decimal("53000")

@pytest.mark.asyncio
async def test_update_position_for_sell_order(reconciliation_job, state_manager):
    """Test updating position for a sell order."""
    # Create existing position
    existing_position = Position(
        symbol="BTCUSDT",
        size=Decimal("2.0"),
        avg_price=Decimal("50000.0")
    )
    
    async with state_manager.Session() as session:
        session.add(existing_position)
        await session.commit()
    
    # Create sell order
    order = Order(
        id="test-order-1",
        symbol="BTCUSDT",
        side="SELL",
        quantity=Decimal("0.5"),
        filled_quantity=Decimal("0.5"),
        price=Decimal("55000.0"),
        status="FILLED"
    )
    
    await reconciliation_job._update_position_for_order(order)
    
    # Verify position was reduced
    async with state_manager.Session() as session:
        from sqlalchemy import select
        result = await session.execute(select(Position).where(Position.symbol == "BTCUSDT"))
        position = result.scalar_one_or_none()
        
        assert position is not None
        assert position.size == Decimal("1.5")  # 2.0 - 0.5

@pytest.mark.asyncio
async def test_update_positions_metrics(reconciliation_job, state_manager):
    """Test updating position metrics."""
    # Create some positions
    positions = [
        Position(symbol="BTCUSDT", size=Decimal("1.0"), avg_price=Decimal("50000.0")),
        Position(symbol="ETHUSDT", size=Decimal("2.0"), avg_price=Decimal("3000.0"))
    ]
    
    async with state_manager.Session() as session:
        for position in positions:
            session.add(position)
        await session.commit()
    
    await reconciliation_job._update_positions()
    
    # Verify metrics were set
    assert reconciliation_job.metrics.set_gauge.call_count >= 4  # 2 positions * 2 metrics each

@pytest.mark.asyncio
async def test_reconciliation_error_handling(reconciliation_job, submitted_order, mock_bingx_client):
    """Test error handling during reconciliation."""
    # Mock exception from exchange
    mock_bingx_client.get_order.side_effect = Exception("Network error")
    
    await reconciliation_job._reconcile_single_order(submitted_order)
    
    # Verify error was logged
    reconciliation_job.audit_logger.log.assert_called()
    
    # Order status should remain unchanged
    async with reconciliation_job.state_manager.Session() as session:
        order = await session.get(Order, "test-order-1")
        assert order.status == "SUBMITTED"