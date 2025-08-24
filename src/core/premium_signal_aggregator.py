"""
Premium Signal Aggregator Module

Aggregates and validates premium trading signals from multiple sources
including Firecrawl, social media, and premium Telegram groups.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass
from enum import Enum

from ..connectors.firecrawl_client import FirecrawlClient
from ..utils.arbitrage_cache import ArbitrageCache
from ..config.arbitrage_config import ArbitrageConfig
from ..core.models import ArbitrageOpportunity

logger = logging.getLogger(__name__)


@dataclass
class PremiumSignal:
    """Data class representing a premium trading signal"""
    source: str
    symbol: str
    direction: str  # 'LONG', 'SHORT'
    entry_price: Optional[float]
    targets: List[float]
    stop_loss: Optional[float]
    confidence: float
    timestamp: datetime
    source_type: str  # 'telegram_premium', 'whale_tracking', 'social_sentiment'
    metadata: Dict[str, Any]
    validation_score: float = 0.0
    market_impact: float = 0.0


@dataclass
class SignalSource:
    """Data class representing a signal source"""
    name: str
    url: str
    source_type: str
    confidence_multiplier: float
    last_scraped: Optional[datetime] = None
    success_rate: float = 0.0


class SignalValidation(Enum):
    """Signal validation levels"""
    UNVALIDATED = "unvalidated"
    BASIC = "basic"
    TECHNICAL = "technical"
    CONFIRMED = "confirmed"
    HIGH_CONFIDENCE = "high_confidence"


class PremiumSignalAggregator:
    """
    Aggregates premium signals from multiple sources and validates them
    using technical analysis and market data.
    """

    def __init__(self, config: ArbitrageConfig):
        self.config = config
        self.firecrawl_client = FirecrawlClient()
        self.cache = ArbitrageCache()
        self.is_running = False

        # Signal tracking
        self.premium_signals: List[PremiumSignal] = []
        self.signal_sources: Dict[str, SignalSource] = {}
        self.validated_signals: List[PremiumSignal] = []

        # Signal filtering settings
        self.min_confidence_threshold = 0.6
        self.min_validation_score = 0.5
        self.max_signal_age_hours = 24

        # Source management
        # Note: premium_sources would come from config if available
        self.premium_sources = getattr(config, 'premium_sources', [])
        self._initialize_signal_sources()

        # Callbacks
        self.signal_callbacks: List[Callable[[PremiumSignal], None]] = []

        logger.info("PremiumSignalAggregator initialized")

    def _initialize_signal_sources(self):
        """Initialize premium signal sources"""
        # Default premium sources
        default_sources = [
            {
                'name': 'premium_telegram_groups',
                'url': 'https://t.me/premium_signals',
                'source_type': 'telegram_premium',
                'confidence_multiplier': 0.8
            },
            {
                'name': 'whale_alerts',
                'url': 'https://whale-alert.io',
                'source_type': 'whale_tracking',
                'confidence_multiplier': 0.9
            },
            {
                'name': 'crypto_news_premium',
                'url': 'https://cointelegraph.com',
                'source_type': 'news_premium',
                'confidence_multiplier': 0.6
            }
        ]

        for source_config in default_sources:
            source = SignalSource(
                name=source_config['name'],
                url=source_config['url'],
                source_type=source_config['source_type'],
                confidence_multiplier=source_config['confidence_multiplier']
            )
            self.signal_sources[source.name] = source

    async def start_aggregation(self):
        """Start premium signal aggregation"""
        if self.is_running:
            logger.warning("Signal aggregator is already running")
            return

        self.is_running = True
        logger.info("Starting premium signal aggregation...")

        try:
            # Start aggregation tasks
            tasks = [
                self._continuous_scraping(),
                self._signal_validation_loop(),
                self._cleanup_old_signals()
            ]

            await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            logger.error("Error in signal aggregation: %s", str(e))
            self.is_running = False

    async def stop_aggregation(self):
        """Stop premium signal aggregation"""
        logger.info("Stopping premium signal aggregation...")
        self.is_running = False

    async def _continuous_scraping(self):
        """Continuously scrape premium sources for signals"""
        logger.info("Starting continuous scraping of premium sources")

        while self.is_running:
            try:
                await self._scrape_all_sources()

                # Wait before next scraping cycle (30 minutes)
                await asyncio.sleep(1800)

            except Exception as e:
                logger.error("Error in continuous scraping: %s", str(e))
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def _scrape_all_sources(self):
        """Scrape all configured premium sources"""
        logger.info("Scraping all premium sources for signals")

        for source_name, source in self.signal_sources.items():
            try:
                await self._scrape_source(source)

                # Small delay between sources to avoid rate limiting
                await asyncio.sleep(1)

            except Exception as e:
                logger.error("Error scraping source %s: %s", source_name, str(e))

    async def _scrape_source(self, source: SignalSource):
        """Scrape a specific premium source"""
        try:
            logger.info("Scraping premium source: %s", source.name)

            # Use Firecrawl to scrape the source
            scrape_options = {
                'onlyMainContent': True,
                'includeTags': ['p', 'div', 'span', 'h1', 'h2', 'h3', 'table'],
                'excludeTags': ['script', 'style', 'nav', 'footer', 'aside'],
                'waitFor': 3000,
                'mobile': False
            }

            scraped_data = await self.firecrawl_client.scrape_premium_content(
                source.url,
                scrape_options
            )

            if scraped_data and scraped_data.get('success'):
                # Extract signals from scraped content
                signals = await self._extract_signals_from_content(
                    scraped_data,
                    source
                )

                # Process extracted signals
                for signal in signals:
                    await self._process_premium_signal(signal)

                # Update source statistics
                source.last_scraped = datetime.now()
                source.success_rate = min(1.0, source.success_rate + 0.1)

                logger.info(
                    "Successfully scraped %d signals from %s",
                    len(signals), source.name
                )

            else:
                # Update failure statistics
                source.success_rate = max(0.0, source.success_rate - 0.1)

        except Exception as e:
            logger.error("Error scraping source %s: %s", source.name, str(e))

    async def _extract_signals_from_content(self, scraped_data: Dict[str, Any],
                                          source: SignalSource) -> List[PremiumSignal]:
        """Extract trading signals from scraped content"""
        signals = []

        try:
            content = scraped_data.get('content', {})
            url = scraped_data.get('url', '')

            # Extract text content
            markdown_content = content.get('markdown', '')
            html_content = content.get('html', '')

            # Look for trading signals in content
            signal_patterns = [
                r'(?:LONG|SHORT|BUY|SELL)\s+(\w+)/(\w+)',
                r'(\w+)/(\w+)\s+(?:LONG|SHORT|BUY|SELL)',
                r'Entry:\s*\$?([0-9.]+)',
                r'Targets?:\s*\$?([0-9.,\s]+)',
                r'Stop Loss:\s*\$?([0-9.]+)'
            ]

            import re
            signal_data = {}

            for pattern in signal_patterns:
                matches = re.findall(pattern, markdown_content, re.IGNORECASE)
                if matches:
                    for match in matches:
                        if len(match) >= 2:
                            if not signal_data.get('symbol'):
                                signal_data['symbol'] = f"{match[0]}/{match[1]}"
                            if len(match) >= 3 and not signal_data.get('entry_price'):
                                signal_data['entry_price'] = float(match[2])

            # Extract direction
            if 'long' in markdown_content.lower() or 'buy' in markdown_content.lower():
                signal_data['direction'] = 'LONG'
            elif 'short' in markdown_content.lower() or 'sell' in markdown_content.lower():
                signal_data['direction'] = 'SHORT'

            # Extract targets and stop loss
            targets = self._extract_targets(markdown_content)
            stop_loss = self._extract_stop_loss(markdown_content)

            if signal_data.get('symbol') and signal_data.get('direction'):
                # Calculate base confidence
                base_confidence = source.confidence_multiplier

                # Create premium signal
                signal = PremiumSignal(
                    source=source.name,
                    symbol=signal_data['symbol'],
                    direction=signal_data['direction'],
                    entry_price=signal_data.get('entry_price'),
                    targets=targets,
                    stop_loss=stop_loss,
                    confidence=base_confidence,
                    timestamp=datetime.now(),
                    source_type=source.source_type,
                    metadata={
                        'scraped_url': url,
                        'raw_content': markdown_content[:500],
                        'source_success_rate': source.success_rate
                    }
                )

                signals.append(signal)

        except Exception as e:
            logger.error("Error extracting signals from content: %s", str(e))

        return signals

    def _extract_targets(self, content: str) -> List[float]:
        """Extract price targets from content"""
        targets = []
        try:
            import re

            # Look for target patterns
            target_patterns = [
                r'Target\s*\d*\s*:\s*\$?([0-9.]+)',
                r'TP\s*\d*\s*:\s*\$?([0-9.]+)',
                r'Target\s*Price\s*\d*\s*:\s*\$?([0-9.]+)'
            ]

            for pattern in target_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    try:
                        targets.append(float(match))
                    except ValueError:
                        continue

            # Remove duplicates and sort
            targets = sorted(list(set(targets)))

        except Exception as e:
            logger.error("Error extracting targets: %s", str(e))

        return targets

    def _extract_stop_loss(self, content: str) -> Optional[float]:
        """Extract stop loss from content"""
        try:
            import re

            # Look for stop loss patterns
            sl_patterns = [
                r'Stop\s*Loss\s*:\s*\$?([0-9.]+)',
                r'SL\s*:\s*\$?([0-9.]+)',
                r'Stop\s*Price\s*:\s*\$?([0-9.]+)'
            ]

            for pattern in sl_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    return float(matches[0])

        except Exception as e:
            logger.error("Error extracting stop loss: %s", str(e))

        return None

    async def _process_premium_signal(self, signal: PremiumSignal):
        """Process a premium signal"""
        try:
            # Add to recent signals
            self.premium_signals.append(signal)

            # Validate the signal
            signal.validation_score = await self._validate_signal(signal)

            # Check if signal meets thresholds
            if (signal.confidence >= self.min_confidence_threshold and
                signal.validation_score >= self.min_validation_score):

                self.validated_signals.append(signal)

                # Cache the validated signal
                await self.cache.set_premium_signal(
                    f"{signal.source}_{signal.symbol}_{int(signal.timestamp.timestamp())}",
                    {
                        'source': signal.source,
                        'symbol': signal.symbol,
                        'direction': signal.direction,
                        'entry_price': signal.entry_price,
                        'targets': signal.targets,
                        'stop_loss': signal.stop_loss,
                        'confidence': signal.confidence,
                        'timestamp': signal.timestamp.isoformat(),
                        'source_type': signal.source_type,
                        'validation_score': signal.validation_score,
                        'market_impact': signal.market_impact
                    }
                )

                # Notify callbacks
                await self._notify_signal_callbacks(signal)

                logger.info(
                    "✅ Validated premium signal: %s %s on %s (conf: %.2f, valid: %.2f)",
                    signal.direction,
                    signal.symbol,
                    signal.source,
                    signal.confidence,
                    signal.validation_score
                )

        except Exception as e:
            logger.error("Error processing premium signal: %s", str(e))

    async def _validate_signal(self, signal: PremiumSignal) -> float:
        """Validate a premium signal using technical analysis"""
        validation_score = 0.0

        try:
            # Factor 1: Source credibility
            validation_score += signal.confidence * 0.3

            # Factor 2: Technical analysis confirmation (placeholder)
            technical_score = await self._check_technical_indicators(signal)
            validation_score += technical_score * 0.4

            # Factor 3: Market sentiment (placeholder)
            sentiment_score = await self._check_market_sentiment(signal)
            validation_score += sentiment_score * 0.2

            # Factor 4: Risk/reward ratio
            risk_reward_score = self._calculate_risk_reward_score(signal)
            validation_score += risk_reward_score * 0.1

            # Ensure score is between 0 and 1
            validation_score = max(0.0, min(1.0, validation_score))

        except Exception as e:
            logger.error("Error validating signal: %s", str(e))
            validation_score = signal.confidence * 0.5  # Fallback

        return validation_score

    async def _check_technical_indicators(self, signal: PremiumSignal) -> float:
        """Check technical indicators for signal confirmation (placeholder)"""
        # In a real implementation, this would:
        # 1. Fetch current price data
        # 2. Calculate RSI, MACD, moving averages
        # 3. Check for support/resistance levels
        # 4. Analyze volume patterns

        # For now, return a neutral score
        return 0.5

    async def _check_market_sentiment(self, signal: PremiumSignal) -> float:
        """Check market sentiment for the symbol (placeholder)"""
        # In a real implementation, this would:
        # 1. Analyze social media sentiment
        # 2. Check news sentiment
        # 3. Monitor whale activities
        # 4. Check on-chain metrics

        # For now, return a neutral score
        return 0.5

    def _calculate_risk_reward_score(self, signal: PremiumSignal) -> float:
        """Calculate risk/reward ratio score"""
        try:
            if not signal.entry_price or not signal.targets or not signal.stop_loss:
                return 0.3  # Neutral score if data missing

            # Calculate potential reward
            max_target = max(signal.targets) if signal.targets else signal.entry_price
            reward = abs(max_target - signal.entry_price) / signal.entry_price

            # Calculate potential risk
            risk = abs(signal.stop_loss - signal.entry_price) / signal.entry_price

            if risk > 0:
                risk_reward_ratio = reward / risk

                # Score based on risk/reward ratio
                if risk_reward_ratio >= 3.0:
                    return 1.0  # Excellent
                elif risk_reward_ratio >= 2.0:
                    return 0.8  # Very good
                elif risk_reward_ratio >= 1.5:
                    return 0.6  # Good
                elif risk_reward_ratio >= 1.0:
                    return 0.4  # Acceptable
                else:
                    return 0.2  # Poor
            else:
                return 0.1  # Invalid stop loss

        except Exception as e:
            logger.error("Error calculating risk/reward score: %s", str(e))
            return 0.3

    async def _signal_validation_loop(self):
        """Periodically validate existing signals"""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Validate every 5 minutes

                await self._revalidate_signals()

            except Exception as e:
                logger.error("Error in signal validation loop: %s", str(e))

    async def _revalidate_signals(self):
        """Re-validate existing signals with updated market data"""
        try:
            current_time = datetime.now()

            for signal in self.validated_signals[:]:
                # Remove signals that are too old
                age_hours = (current_time - signal.timestamp).total_seconds() / 3600
                if age_hours > self.max_signal_age_hours:
                    self.validated_signals.remove(signal)
                    continue

                # Re-validate signal with current market conditions
                new_validation_score = await self._validate_signal(signal)

                if new_validation_score < self.min_validation_score:
                    # Signal no longer valid
                    self.validated_signals.remove(signal)
                    logger.info(
                        "Signal invalidated: %s %s (new score: %.2f)",
                        signal.direction, signal.symbol, new_validation_score
                    )

        except Exception as e:
            logger.error("Error revalidating signals: %s", str(e))

    async def _cleanup_old_signals(self):
        """Clean up old signal data"""
        while self.is_running:
            try:
                await asyncio.sleep(3600)  # Clean every hour

                # Clean old signals (older than 7 days)
                cutoff_time = datetime.now() - timedelta(days=7)
                self.premium_signals = [
                    signal for signal in self.premium_signals
                    if signal.timestamp > cutoff_time
                ]

            except Exception as e:
                logger.error("Error in signal cleanup: %s", str(e))

    # Callback management
    def add_signal_callback(self, callback: Callable[[PremiumSignal], None]):
        """Add callback for premium signals"""
        self.signal_callbacks.append(callback)

    async def _notify_signal_callbacks(self, signal: PremiumSignal):
        """Notify all signal callbacks"""
        for callback in self.signal_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(signal)
                else:
                    callback(signal)
            except Exception as e:
                logger.error("Error in signal callback: %s", str(e))

    # Data access methods
    def get_recent_signals(self, hours: int = 24) -> List[PremiumSignal]:
        """Get recent premium signals"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [signal for signal in self.premium_signals if signal.timestamp > cutoff_time]

    def get_validated_signals(self, hours: int = 24) -> List[PremiumSignal]:
        """Get validated premium signals"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [signal for signal in self.validated_signals if signal.timestamp > cutoff_time]

    def get_signals_by_symbol(self, symbol: str) -> List[PremiumSignal]:
        """Get signals for a specific symbol"""
        return [signal for signal in self.validated_signals if signal.symbol == symbol]

    def get_signal_sources(self) -> Dict[str, SignalSource]:
        """Get all signal sources"""
        return self.signal_sources.copy()

    def get_aggregation_stats(self) -> Dict[str, Any]:
        """Get signal aggregation statistics"""
        recent_signals = self.get_recent_signals(hours=1)
        validated_signals = self.get_validated_signals(hours=1)

        return {
            'is_running': self.is_running,
            'total_sources': len(self.signal_sources),
            'total_signals_24h': len(self.get_recent_signals(hours=24)),
            'validated_signals_24h': len(self.get_validated_signals(hours=24)),
            'signals_last_hour': len(recent_signals),
            'validated_signals_last_hour': len(validated_signals),
            'min_confidence_threshold': self.min_confidence_threshold,
            'min_validation_score': self.min_validation_score,
            'active_sources': sum(1 for s in self.signal_sources.values() if s.last_scraped),
            'sources': {
                name: {
                    'last_scraped': source.last_scraped.isoformat() if source.last_scraped else None,
                    'success_rate': source.success_rate,
                    'confidence_multiplier': source.confidence_multiplier
                }
                for name, source in self.signal_sources.items()
            }
        }

    def add_custom_signal_source(self, name: str, url: str, source_type: str,
                               confidence_multiplier: float = 0.5):
        """Add a custom signal source"""
        source = SignalSource(
            name=name,
            url=url,
            source_type=source_type,
            confidence_multiplier=confidence_multiplier
        )
        self.signal_sources[name] = source
        logger.info("Added custom signal source: %s", name)

    async def test_signal_source(self, source_name: str) -> Dict[str, Any]:
        """Test a signal source and return results"""
        if source_name not in self.signal_sources:
            return {'error': f'Source {source_name} not found'}

        source = self.signal_sources[source_name]

        try:
            # Test scraping the source
            scraped_data = await self.firecrawl_client.scrape_premium_content(source.url)

            if scraped_data and scraped_data.get('success'):
                signals = await self._extract_signals_from_content(scraped_data, source)

                return {
                    'source': source_name,
                    'success': True,
                    'signals_found': len(signals),
                    'content_length': len(scraped_data.get('content', {}).get('markdown', '')),
                    'signals': [
                        {
                            'symbol': signal.symbol,
                            'direction': signal.direction,
                            'confidence': signal.confidence
                        }
                        for signal in signals[:5]  # Show first 5 signals
                    ]
                }
            else:
                return {
                    'source': source_name,
                    'success': False,
                    'error': 'Failed to scrape content'
                }

        except Exception as e:
            return {
                'source': source_name,
                'success': False,
                'error': str(e)
            }
