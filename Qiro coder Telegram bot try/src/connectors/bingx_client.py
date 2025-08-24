# feat(connector): async BingX HTTP client with retry/backoff
from __future__ import annotations
import os
import time
import asyncio
import hmac
import hashlib
from typing import Any, Dict, Optional
import httpx

class BingXClient:
    """Einfacher Async-Client für BingX REST-Endpunkte mit Retry/Backoff."""
    def __init__(self) -> None:
        self.api_key = os.getenv("BINGX_API_KEY", "")
        secret_key = os.getenv("BINGX_SECRET_KEY", "")
        self.secret_key_bytes = secret_key.encode('utf-8')
        base_url = "https://open-api.bingx.com"
        if os.getenv("BINGX_TESTNET", "false").lower() == "true":
            base_url = "https://open-api-vst.bingx.com"
        
        self._client = httpx.AsyncClient(base_url=base_url, timeout=10.0)

    def _sign(self, params: Dict[str, Any]) -> str:
        sorted_params = sorted(params.items())
        to_sign = "&".join([f"{k}={v}" for k, v in sorted_params])
        return hmac.new(self.secret_key_bytes, to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

    async def _request(self, method: str, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        params['timestamp'] = int(time.time() * 1000)
        params['signature'] = self._sign(params)
        headers = {'X-BX-APIKEY': self.api_key}
        
        backoff = 0.5
        for attempt in range(4):
            try:
                resp = await self._client.request(method, path, params=params, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                if data.get("code") == 0:
                    return {"status": "ok", "data": data.get("data", data)}
                else:
                    return {"status": "error", "data": data}
            except httpx.HTTPStatusError as e:
                if 500 <= e.response.status_code < 600 and attempt < 3:
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                return {"status": "error", "data": {"code": e.response.status_code, "msg": e.response.text}}
            except Exception as e:
                return {"status": "error", "data": {"msg": str(e)}}
        return {"status": "error", "data": {"msg": "max_retries_exceeded"}}

    async def create_order(self, symbol: str, side: str, order_type: str, quantity: float, 
                          leverage: Optional[int] = None, margin_mode: str = "cross") -> Dict[str, Any]:
        """Create a trading order with optional leverage and margin mode settings."""
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': quantity
        }
        
        # Add leverage and margin mode if specified
        if leverage:
            params['leverage'] = leverage
        
        if margin_mode.lower() in ['cross', 'isolated']:
            params['marginMode'] = margin_mode.upper()
        
        return await self._request("POST", "/openApi/spot/v1/trade/order", params)

    async def get_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        return await self._request("GET", "/openApi/spot/v1/trade/order", params={'symbol': symbol, 'orderId': order_id})

    async def aclose(self) -> None:
        await self._client.aclose()