# # auto_stock/tasks.py
#
# from celery import shared_task
# from kis.websocket.manage.ws_manager import KISWebSocketManager
#
# @shared_task(queue="websocket")
# def start_ws_manager():
#     mgr = KISWebSocketManager("/tryitout/H0STCNT0")
#     mgr.connect()
#
#     # 구독할 모든 종목
#     watch_list = ["005930", "000660", "035420", "068270", "035720"]
#     for code in watch_list:
#         mgr.subscribe(code, "H0STCNT0")
#
#     mgr.listen()