from celery import shared_task
from trading.strategy.rsi_strategy import auto_trading_runner

@shared_task
def run_auto_trading(symbol):
    auto_trading_runner(symbol)