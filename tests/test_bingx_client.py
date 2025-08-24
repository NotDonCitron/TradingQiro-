# feat(test): comprehensive unit tests for BingX client
import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from src.connectors.bingx_client import BingXClient

@pytest.fixture
def bingx_client():
    """Create a BingX client for testing."""
    with patch.dict('os.environ', {
        'BINGX_API_KEY': 'test_api_key',
        'BINGX_SECRET_KEY': 'test_secret_key',
        'BINGX_TESTNET': 'true'
    }):
        return BingXClient()

@pytest.fixture
def mock_httpx_client():
    """Mock httpx client."""
    return AsyncMock(spec=httpx.AsyncClient)

@pytest.mark.asyncio
async def test_bingx_client_init(bingx_client):
    """Test BingX client initialization."""
    assert bingx_client.api_key == "test_api_key"
    assert bingx_client.secret_key_bytes == b"test_secret_key"
    assert "open-api-vst.bingx.com" in str(bingx_client._client.base_url)

@pytest.mark.asyncio
async def test_bingx_client_init_production():
    """Test BingX client initialization for production."""
    with patch.dict('os.environ', {
        'BINGX_API_KEY': 'test_api_key',
        'BINGX_SECRET_KEY': 'test_secret_key',
        'BINGX_TESTNET': 'false'
    }):
        client = BingXClient()
        assert "open-api.bingx.com" in str(client._client.base_url)

def test_sign_method(bingx_client):
    """Test the signature generation method."""
    params = {'symbol': 'BTCUSDT', 'side': 'BUY', 'quantity': 0.1}
    signature = bingx_client._sign(params)
    
    assert isinstance(signature, str)
    assert len(signature) == 64  # SHA256 hex digest length

def test_sign_method_deterministic(bingx_client):
    """Test that signature generation is deterministic."""
    params = {'symbol': 'BTCUSDT', 'side': 'BUY', 'quantity': 0.1}
    signature1 = bingx_client._sign(params)
    signature2 = bingx_client._sign(params)
    
    assert signature1 == signature2

@pytest.mark.asyncio
async def test_create_order_success(bingx_client):
    """Test successful order creation."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "code": 0,
        "data": {"orderId": "12345", "status": "NEW"}
    }
    mock_response.raise_for_status.return_value = None
    
    with patch.object(bingx_client._client, 'request', return_value=mock_response) as mock_request:
        result = await bingx_client.create_order("BTCUSDT", "buy", "MARKET", 0.1)
        
        assert result["status"] == "ok"
        assert result["data"]["orderId"] == "12345"
        mock_request.assert_called_once()

@pytest.mark.asyncio
async def test_create_order_api_error(bingx_client):
    """Test order creation with API error."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "code": -1,
        "msg": "Invalid symbol"
    }
    mock_response.raise_for_status.return_value = None
    
    with patch.object(bingx_client._client, 'request', return_value=mock_response):
        result = await bingx_client.create_order("INVALID", "buy", "MARKET", 0.1)
        
        assert result["status"] == "error"
        assert "Invalid symbol" in str(result["data"])

@pytest.mark.asyncio
async def test_create_order_http_error(bingx_client):
    """Test order creation with HTTP error."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    
    with patch.object(bingx_client._client, 'request', side_effect=httpx.HTTPStatusError(
        "Server error", request=MagicMock(), response=mock_response
    )):
        result = await bingx_client.create_order("BTCUSDT", "buy", "MARKET", 0.1)
        
        assert result["status"] == "error"
        assert result["data"]["code"] == 500

@pytest.mark.asyncio
async def test_create_order_retry_on_server_error(bingx_client):
    """Test retry logic on server errors."""
    # First 3 calls fail with 500, 4th succeeds
    responses = []
    for i in range(3):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        responses.append(httpx.HTTPStatusError("Server error", request=MagicMock(), response=mock_response))
    
    # Success response
    success_response = MagicMock()
    success_response.json.return_value = {"code": 0, "data": {"orderId": "12345"}}
    success_response.raise_for_status.return_value = None
    responses.append(success_response)
    
    with patch.object(bingx_client._client, 'request', side_effect=responses):
        result = await bingx_client.create_order("BTCUSDT", "buy", "MARKET", 0.1)
        
        assert result["status"] == "ok"
        assert result["data"]["orderId"] == "12345"

@pytest.mark.asyncio
async def test_create_order_max_retries_exceeded(bingx_client):
    """Test max retries exceeded scenario."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Server Error"
    
    with patch.object(bingx_client._client, 'request', side_effect=httpx.HTTPStatusError(
        "Server error", request=MagicMock(), response=mock_response
    )):
        result = await bingx_client.create_order("BTCUSDT", "buy", "MARKET", 0.1)
        
        assert result["status"] == "error"
        assert "max_retries_exceeded" in result["data"]["msg"]

@pytest.mark.asyncio
async def test_get_order_success(bingx_client):
    """Test successful order retrieval."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "code": 0,
        "data": {
            "orderId": "12345",
            "status": "FILLED",
            "executedQty": "0.1"
        }
    }
    mock_response.raise_for_status.return_value = None
    
    with patch.object(bingx_client._client, 'request', return_value=mock_response):
        result = await bingx_client.get_order("BTCUSDT", "12345")
        
        assert result["status"] == "ok"
        assert result["data"]["orderId"] == "12345"
        assert result["data"]["status"] == "FILLED"

@pytest.mark.asyncio
async def test_get_order_not_found(bingx_client):
    """Test get order with not found error."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "code": -2013,
        "msg": "Order does not exist"
    }
    mock_response.raise_for_status.return_value = None
    
    with patch.object(bingx_client._client, 'request', return_value=mock_response):
        result = await bingx_client.get_order("BTCUSDT", "99999")
        
        assert result["status"] == "error"
        assert "Order does not exist" in str(result["data"])

@pytest.mark.asyncio
async def test_client_close(bingx_client):
    """Test client cleanup."""
    with patch.object(bingx_client._client, 'aclose') as mock_close:
        await bingx_client.aclose()
        mock_close.assert_called_once()

@pytest.mark.asyncio
async def test_request_includes_signature_and_timestamp(bingx_client):
    """Test that requests include timestamp and signature."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"code": 0, "data": {}}
    mock_response.raise_for_status.return_value = None
    
    with patch.object(bingx_client._client, 'request', return_value=mock_response) as mock_request:
        await bingx_client.create_order("BTCUSDT", "buy", "MARKET", 0.1)
        
        # Check that the request was made with proper parameters
        call_args = mock_request.call_args
        params = call_args[1]['params']
        
        assert 'timestamp' in params
        assert 'signature' in params
        assert isinstance(params['timestamp'], int)
        assert isinstance(params['signature'], str)
        assert len(params['signature']) == 64

@pytest.mark.asyncio
async def test_request_headers(bingx_client):
    """Test that requests include proper headers."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"code": 0, "data": {}}
    mock_response.raise_for_status.return_value = None
    
    with patch.object(bingx_client._client, 'request', return_value=mock_response) as mock_request:
        await bingx_client.create_order("BTCUSDT", "buy", "MARKET", 0.1)
        
        call_args = mock_request.call_args
        headers = call_args[1]['headers']
        
        assert headers['X-BX-APIKEY'] == 'test_api_key'