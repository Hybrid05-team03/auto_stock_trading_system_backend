from rest_framework.views import APIView
from rest_framework.response import Response

from .models import OrderRequest
from .serializers import OrderRequestSerializer

from kis.api.quote import kis_get_market_cap
from kis.data.search_code import mapping_code_to_name
from kis.websocket.util.kis_data_save import subscribe_and_get_data
from trading.tasks.auto_buy import auto_buy
from kis.websocket.trading_ws import order_sell, order_buy
from kis.api.account import fetch_psbl_order, fetch_balance


## 매도 가능 여부 조회 계좌 잔고 조회
class IsPossibleSellView(APIView):

    def get(self, request):
        symbol = request.query_params.get("symbol")

        if not symbol:
            return Response({"error": "종목코드 파라미터 누락"}, status=400)

        balance = fetch_balance()

        if balance is None:
            return Response({"error": "잔액 조회 실패"}, status=500)

        # balance["stocks"] = 보유 종목 리스트
        stocks = balance.get("stocks", [])

        # 해당 종목 검색
        target = next((item for item in stocks if item["symbol"] == symbol), None)

        print(f"=======  보유 종목 : {target}")
        if not target:
            return Response({
                "symbol": symbol,
                "possibleSell": False,
                "message": "보유하지 않은 종목입니다."
            }, status=200)

        sellable_qty = int(target.get("sell_psbl_qty", 0))

        return Response({
            "symbol": symbol,
            "possibleSell": sellable_qty > 0,
            "sellableQty": sellable_qty,
            "message": "매도 가능" if sellable_qty > 0 else "매도 가능한 수량 없음"
        }, status=200)


## 매수 가능 여부 조회
class IsPossibleBuyView(APIView):
    def get(self, request):
        symbol = request.query_params.get("symbol")
        if not symbol:
            return Response({"error": "종목코드 파라미터 누락"}, status=400)

        result = fetch_psbl_order(symbol)

        if "error" in result:
            return Response(result, status=500)

        # 매수 가능 여부 판단
        isPossible = result["buyableQty"] > 0 and result["availableCash"] > 0

        response = {
            "symbol": symbol,
            "possibleBuy": isPossible,
            "buyableQty": result["buyableQty"],
            "buyableAmount": result["buyableAmount"],
            "availableCash": result["availableCash"],
            "message": result["message"]
        }

        return Response(response, status=200)


## 자동 매매
class AutoOrderCreateView(APIView):
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
        auto_buy.delay(serializer.instance.id)

        return Response({"message": "주문 요청이 접수되었습니다."}, status=201)


## 수동 매수
class ManualBuyView(APIView):
    def post(self, request):
        symbol = request.data.get("symbol")
        qty = int(request.data.get("qty", 0))
        order_type = request.data.get("order_type", "market")

        if not symbol or qty <= 0:
            return Response({"error": "symbol, qty 필요"}, status=400)

        result = order_sell(symbol, qty, order_type=order_type)

        return Response({
            "ok": result.ok,
            "message": result.message,
            "order_id": result.order_id,
        })


## 수동 매도
class ManualSellView(APIView):
    def post(self, request):
        symbol = request.data.get("symbol")
        qty = int(request.data.get("qty", 0))
        order_type = request.data.get("order_type", "market")

        if not symbol or qty <= 0:
            return Response({"error": "symbol, qty 필요"}, status=400)

        result = order_buy(symbol, qty, order_type=order_type)

        return Response({
            "ok": result.ok,
            "message": result.message,
            "order_id": result.order_id,
        })