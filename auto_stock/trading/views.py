from rest_framework.views import APIView
from rest_framework.response import Response

from .models import OrderRequest
from .serializers import OrderRequestSerializer

from kis.api.quote import kis_get_market_cap
from kis.data.search_code import mapping_code_to_name
from kis.websocket.util.kis_data_save import subscribe_and_get_data
from trading.tasks.auto_trade import auto_trade

class OrderCreateView(APIView):
    ## 주문 기록 목록 조회
    def get(self, request):
        orders = OrderRequest.objects.all().order_by("-created_at")

        # 종목코드 리스트
        symbols = [o.symbol for o in orders]
        symbols = list(set(symbols))  # 중복 제거

        ui_map = {}  # 실시간 정보 저장

        # 각 종목의 실시간 데이터
        for code in symbols:
            data = subscribe_and_get_data("H0STCNT0", code, "price", timeout=7)
            stock_name = mapping_code_to_name(code)

            if data:
                ui_map[code] = {
                    "name": stock_name,
                    "symbol": code,
                    "current_price": data.get("current_price"),
                    "target_price": kis_get_market_cap(code),
                    "change_percent": data.get("change_rate"),
                    "volume": data.get("trade_value"),
                }
            else:
                ui_map[code] = {
                    "name": stock_name,
                    "symbol": code,
                    "current_price": None,
                    "target_price": None,
                    "change_percent": None,
                    "volume": None,
                }

        response_list = []
        for order in orders:
            info = ui_map.get(order.symbol, {})

            response_list.append({
                "name": info.get("name"),
                "symbol": order.symbol,
                "currentPrice": info.get("current_price"),
                "targetPrice": info.get("target_price"),
                "strategy": order.strategy.upper(),
                "changePercent": info.get("change_percent"),
                "status": order.status
            })

        return Response(response_list, status=200)


    ## 주문 요청 처리
    def post(self, request):
        serializer = OrderRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()  # DB 저장

        # 자동 매매 태스크 실행
        auto_trade.delay(serializer.instance.id)

        return Response({"message": "주문 요청이 접수되었습니다."}, status=201)


# -------------------------------------------------------
# 실시간 자동매매 시작 (Celery 트리거)
# -------------------------------------------------------
# @api_view(["POST"])
# def start_auto_trading(request):
#     symbol = request.query_params.get("code")
#
#     if not symbol:
#         return Response({"error": "code 쿼리 파라미터가 필요합니다."}, status=400)
#
#     run_auto_trading.delay(symbol)
#
#     return Response({
#         "message": f"{symbol} 자동매매 작업이 Celery 워커에서 실행됩니다.",
#         "symbol": symbol
#     })