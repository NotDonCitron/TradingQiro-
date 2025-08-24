"""
Risk Manager Module

Assesses and manages risk for arbitrage opportunities
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from ..config.arbitrage_config import ArbitrageConfig
from ..core.models import ArbitrageOpportunity

logger = logging.getLogger(__name__)


class RiskManager:
    """
    Manages risk assessment and limits for arbitrage opportunities
    """

    def __init__(self, config: ArbitrageConfig):
        self.config = config
        self.daily_loss = 0.0
        self.open_positions = 0
        self.daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        self.position_history: List[Dict[str, Any]] = []

        logger.info("RiskManager initialized with config: max_daily_loss=%.2f, max_positions=%d",
                   config.max_daily_loss_usd, config.max_open_positions)

    def assess_opportunity(self, opportunity: ArbitrageOpportunity) -> float:
        """
        Assess the risk score for an arbitrage opportunity

        Returns a risk score between 0.0 (low risk) and 1.0 (high risk)
        """
        risk_score = 0.0
        risk_factors = []

        try:
            # Factor 1: Profit percentage (lower profit = higher risk)
            if opportunity.profit_percent < 1.0:
                risk_score += 0.3
                risk_factors.append("low_profit_margin")
            elif opportunity.profit_percent > 5.0:
                risk_score += 0.1  # High profit might indicate market inefficiency
                risk_factors.append("high_profit_suspicious")

            # Factor 2: Volume availability
            if opportunity.volume < 1000:
                risk_score += 0.2
                risk_factors.append("low_volume")
            elif opportunity.volume > 100000:
                risk_score -= 0.1  # High volume is good

            # Factor 3: Fee impact
            total_fees = opportunity.fees.get('total_fee', 0)
            fee_impact = total_fees / opportunity.buy_price * 100
            if fee_impact > 0.5:  # Fees eat more than 0.5% of profit
                risk_score += 0.2
                risk_factors.append("high_fees")

            # Factor 4: Exchange reliability
            exchange_risk = self._assess_exchange_risk(opportunity.buy_exchange, opportunity.sell_exchange)
            risk_score += exchange_risk * 0.3

            # Factor 5: Price spread analysis
            spread_risk = self._assess_spread_risk(opportunity)
            risk_score += spread_risk * 0.2

            # Factor 6: Historical success rate (if available)
            historical_risk = self._assess_historical_performance(opportunity)
            risk_score += historical_risk * 0.1

            # Factor 7: Market volatility
            volatility_risk = self._assess_market_volatility(opportunity.symbol)
            risk_score += volatility_risk * 0.1

            # Ensure risk score is between 0 and 1
            risk_score = max(0.0, min(1.0, risk_score))

            logger.debug(
                "Risk assessment for %s: score=%.3f, factors=%s",
                opportunity.symbol, risk_score, risk_factors
            )

            return risk_score

        except Exception as e:
            logger.error("Error assessing opportunity risk: %s", str(e))
            return 0.8  # High risk if assessment fails

    def _assess_exchange_risk(self, buy_exchange: str, sell_exchange: str) -> float:
        """Assess risk based on exchange reliability and history"""
        # Define exchange risk scores (0.0 = low risk, 1.0 = high risk)
        exchange_risks = {
            'binance': 0.1,   # Very reliable
            'coinbase': 0.2,  # Generally reliable
            'kraken': 0.3,    # Good but more conservative
            'bingx': 0.4,     # Newer exchange, higher risk
        }

        buy_risk = exchange_risks.get(buy_exchange.lower(), 0.5)
        sell_risk = exchange_risks.get(sell_exchange.lower(), 0.5)

        # Average risk of both exchanges
        return (buy_risk + sell_risk) / 2

    def _assess_spread_risk(self, opportunity: ArbitrageOpportunity) -> float:
        """Assess risk based on bid-ask spread"""
        try:
            spread_percent = ((opportunity.sell_price - opportunity.buy_price) / opportunity.buy_price) * 100

            if spread_percent < 0.5:
                return 0.8  # Very tight spread might be artificial
            elif spread_percent < 1.0:
                return 0.4  # Good spread
            elif spread_percent < 2.0:
                return 0.2  # Acceptable spread
            else:
                return 0.1  # Wide spread is less risky

        except Exception:
            return 0.5  # Medium risk if calculation fails

    def _assess_historical_performance(self, opportunity: ArbitrageOpportunity) -> float:
        """Assess risk based on historical performance of similar opportunities"""
        # This would typically query a database of past arbitrage attempts
        # For now, return a neutral score
        return 0.5

    def _assess_market_volatility(self, symbol: str) -> float:
        """Assess market volatility for the given symbol"""
        # This would typically use price data to calculate volatility
        # For now, use a simple symbol-based assessment

        volatile_symbols = ['DOGE/USDT', 'SHIB/USDT', 'PEPE/USDT']
        stable_symbols = ['BTC/USDT', 'ETH/USDT', 'USDT/USDC']

        if any(volatile in symbol.upper() for volatile in volatile_symbols):
            return 0.8  # High volatility
        elif any(stable in symbol.upper() for stable in stable_symbols):
            return 0.2  # Low volatility
        else:
            return 0.4  # Medium volatility

    def can_execute_opportunity(self, opportunity: ArbitrageOpportunity) -> Dict[str, Any]:
        """
        Check if an opportunity can be executed based on risk limits

        Returns:
            dict: {
                'can_execute': bool,
                'reasons': List[str],
                'risk_score': float
            }
        """
        reasons = []
        can_execute = True

        try:
            # Check daily loss limit
            if self.daily_loss >= self.config.max_daily_loss_usd:
                reasons.append(f"Daily loss limit reached: ${self.daily_loss:.2f} >= ${self.config.max_daily_loss_usd}")
                can_execute = False

            # Check position limit
            if self.open_positions >= self.config.max_open_positions:
                reasons.append(f"Max open positions reached: {self.open_positions} >= {self.config.max_open_positions}")
                can_execute = False

            # Check single trade limit
            if opportunity.estimated_profit > self.config.max_single_trade_usd:
                reasons.append(f"Trade size too large: ${opportunity.estimated_profit:.2f} > ${self.config.max_single_trade_usd}")
                can_execute = False

            # Check minimum profit threshold
            if opportunity.profit_percent < self.config.min_profit_threshold_percent:
                reasons.append(f"Profit below threshold: {opportunity.profit_percent:.4f}% < {self.config.min_profit_threshold_percent}%")
                can_execute = False

            # Check risk score threshold
            risk_score = self.assess_opportunity(opportunity)
            if risk_score > 0.8:  # Very high risk
                reasons.append(f"Risk score too high: {risk_score:.3f} > 0.8")
                can_execute = False

            return {
                'can_execute': can_execute,
                'reasons': reasons,
                'risk_score': risk_score
            }

        except Exception as e:
            logger.error("Error checking opportunity execution: %s", str(e))
            return {
                'can_execute': False,
                'reasons': [f"Error in risk assessment: {str(e)}"],
                'risk_score': 1.0
            }

    def record_position_open(self, opportunity: ArbitrageOpportunity):
        """Record a new position being opened"""
        position = {
            'symbol': opportunity.symbol,
            'buy_exchange': opportunity.buy_exchange,
            'sell_exchange': opportunity.sell_exchange,
            'profit_percent': opportunity.profit_percent,
            'estimated_profit': opportunity.estimated_profit,
            'opened_at': datetime.now(),
            'status': 'open'
        }

        self.position_history.append(position)
        self.open_positions += 1

        logger.info("Recorded position open: %s for %.4f%% profit",
                   opportunity.symbol, opportunity.profit_percent)

    def record_position_close(self, symbol: str, actual_profit: float, success: bool = True):
        """Record a position being closed"""
        for position in self.position_history:
            if position['symbol'] == symbol and position['status'] == 'open':
                position['status'] = 'closed'
                position['actual_profit'] = actual_profit
                position['closed_at'] = datetime.now()
                position['success'] = success

                self.open_positions = max(0, self.open_positions - 1)
                self.daily_loss += (-actual_profit if actual_profit < 0 else 0)

                logger.info("Recorded position close: %s, profit: %.2f, success: %s",
                           symbol, actual_profit, success)
                break

    def reset_daily_limits(self):
        """Reset daily loss and position tracking"""
        now = datetime.now()

        if now.date() > self.daily_reset_time.date():
            logger.info("Resetting daily limits - previous loss: %.2f", self.daily_loss)
            self.daily_loss = 0.0
            self.daily_reset_time = now.replace(hour=0, minute=0, second=0, microsecond=0)

            # Close any open positions (assume they were closed at EOD)
            for position in self.position_history:
                if position['status'] == 'open':
                    position['status'] = 'closed'
                    position['closed_at'] = self.daily_reset_time
                    position['actual_profit'] = 0.0
                    position['success'] = False

            self.open_positions = 0

    def get_risk_metrics(self) -> Dict[str, Any]:
        """Get current risk metrics"""
        self.reset_daily_limits()  # Check if we need to reset

        return {
            'daily_loss': self.daily_loss,
            'max_daily_loss': self.config.max_daily_loss_usd,
            'open_positions': self.open_positions,
            'max_open_positions': self.config.max_open_positions,
            'daily_loss_percent': (self.daily_loss / self.config.max_daily_loss_usd) * 100 if self.config.max_daily_loss_usd > 0 else 0,
            'position_utilization': (self.open_positions / self.config.max_open_positions) * 100 if self.config.max_open_positions > 0 else 0,
            'total_positions_today': len([p for p in self.position_history if p.get('opened_at', datetime.min).date() == datetime.now().date()]),
            'successful_positions_today': len([p for p in self.position_history if p.get('success', False) and p.get('opened_at', datetime.min).date() == datetime.now().date()])
        }

    def get_position_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get position history for the last N days"""
        cutoff_date = datetime.now() - timedelta(days=days)

        return [
            position for position in self.position_history
            if position.get('opened_at', datetime.max) > cutoff_date
        ]

    def calculate_win_rate(self, days: int = 30) -> float:
        """Calculate win rate over the last N days"""
        recent_positions = self.get_position_history(days)
        closed_positions = [p for p in recent_positions if p.get('status') == 'closed']

        if not closed_positions:
            return 0.0

        successful_positions = [p for p in closed_positions if p.get('success', False)]
        return (len(successful_positions) / len(closed_positions)) * 100

    def get_average_profit(self, days: int = 30) -> float:
        """Get average profit per trade over the last N days"""
        recent_positions = self.get_position_history(days)
        closed_positions = [p for p in recent_positions if p.get('status') == 'closed']

        if not closed_positions:
            return 0.0

        total_profit = sum(p.get('actual_profit', 0) for p in closed_positions)
        return total_profit / len(closed_positions)
