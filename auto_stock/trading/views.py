from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import OrderRequest
from .serializers import OrderRequestSerializer

from kis.api.quote import kis_get_market_cap
from kis.data.search_code import mapping_code_to_name
from kis.websocket.util.kis_data_save import subscribe_and_get_data


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
                "status": "매수중"
            })

        return Response(response_list, status=200)


    ## 주문 요청 처리
    def post(self, request):
        serializer = OrderRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()  # DB 저장

        return Response(
            {"message": "주문 요청 처리되었습니다."},
            status=status.HTTP_201_CREATED,
        )