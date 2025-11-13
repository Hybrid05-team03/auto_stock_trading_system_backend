from dataclasses import dataclass

@dataclass
class RSIStrategyParams:
    """RSI 기반 자동매매 전략의 주요 파라미터"""
    period: int = 2                    # RSI 기간
    buy_threshold: float = 10.0        # RSI < 10 → 매수
    sell_threshold: float = 70.0       # RSI > 70 → 매도
    max_positions: int = 10            # 최대 보유 종목 수
    allocation_ratio: float = 0.1      # 자산 중 10%씩 배분
    min_order_qty: int = 1             # 최소 주문 수량
    use_profit_filter: bool = True     # RSI 매도 시 수익 여부 확인
    stop_loss_rate: float = 0.08       # 손절 8%