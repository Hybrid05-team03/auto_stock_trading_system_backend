# # trading/tasks.py
# import logging
#
# from trading.services.trading_auto import auto_trade
#
# from celery import shared_task
# from tmp.websocket.manage.ws_manager import KISWebSocketManager
# from trading.services.trading_ws_handler import realtime_price_callback
#
#
# logger = logging.getLogger(__name__)
#
#
# ## Celery Worker로 웹 소켓 연결 유지
# @shared_task(name="trading.run_auto_trading")
# def run_auto_trading():
#
#     manager = KISWebSocketManager(endpoint="/tryitout")  # KIS realtime endpoint (BASE_URL + endpoint + tr_id)
#     manager.connect()
#
#     # 테스트 : 삼성, 하이닉스
#     manager.subscribe("005930")
#     manager.subscribe("000660")
#
#     # 무한 루프 실행
#     manager.listen(on_message=realtime_price_callback)