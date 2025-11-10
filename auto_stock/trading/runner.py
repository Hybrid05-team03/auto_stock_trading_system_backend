# trading/runner.py
from typing import List, Dict
from trading.strategy.rsi_strategy import StrategyConfig, Portfolio, decide
from trading.broker.kis_broker import Broker, OrderResult

def run_once(watchlist: List[str], cash: float, positions: Dict[str, Dict], cfg: StrategyConfig = StrategyConfig(), dry_run=True):
    """
    - watchlist: 감시 종목 리스트 (ex: ["005930", "000660", ...])
    - cash, positions: 포트폴리오 상태 (실제로는 DB에서 읽기/쓰기)
    - dry_run=True면 가상 주문
    """
    pf = Portfolio(cash=cash, positions=positions)
    broker = Broker(dry_run=dry_run)

    results = []
    for symbol in watchlist:
        d = decide(symbol, pf, cfg)
        action: OrderResult | None = None

        if d.side == "BUY" and d.qty > 0:
            action = broker.buy_market(symbol, d.qty)
            if action.ok:
                # 포지션 반영 (간단 처리)
                cost = (d.price or 0) * d.qty
                pf.cash -= cost
                pf.positions[symbol] = {"qty": d.qty, "avg_price": d.price}
        elif d.side == "SELL" and symbol in pf.positions:
            qty = d.qty if d.qty > 0 else pf.positions[symbol]["qty"]
            action = broker.sell_market(symbol, qty)
            if action.ok:
                # 현금 반영 (간단 처리)
                income = (d.price or 0) * qty
                pf.cash += income
                pf.positions[symbol] = {"qty": 0, "avg_price": pf.positions[symbol]["avg_price"]}

        results.append({
            "symbol": symbol,
            "decision": d.side,
            "reason": d.reason,
            "rsi": d.rsi,
            "price": d.price,
            "qty": d.qty,
            "order": (action.__dict__ if action else None),
        })

    # 실제 서비스에선 여기서 DB에 pf 상태 저장
    return {"cash": pf.cash, "positions": pf.positions, "results": results}