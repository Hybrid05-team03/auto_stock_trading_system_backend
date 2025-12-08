from rest_framework.views import APIView
from rest_framework.response import Response

from .models import OrderRequest, OrderExecution
from .serializers import OrderRequestSerializer

from kis.api.quote import kis_get_market_cap
from kis.data.search_code import mapping_code_to_name
from kis.websocket.util.kis_data_save import subscribe_and_get_data
from trading.tasks.auto_order import auto_order

from kis.websocket.trading_ws import order_sell, order_buy, order_cancel
from kis.api.account import fetch_psbl_order, fetch_balance, fetch_recent_ccld



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
        orders = OrderRequest.objects.all().order_by("-updated_at")

        response_list = []
        for order in orders:
            executions = OrderExecution.objects.filter(order_request=order)
            exec_list = [
                {
                    "side": exec.executed_side,
                    "price": exec.executed_price,
                    "kis_order_id": exec.kis_order_id,
                }
                for exec in executions
            ]

            name = mapping_code_to_name(order.symbol)
            response_list.append({
                "symbol": order.symbol,
                "name": name,
                "executions": exec_list,
                "strategy": order.strategy,
                "gap": order.target_profit,
                "quantity": order.quantity,
                "status": order.status,
            })

        return Response(response_list, status=200)


    ## 주문 요청 처리
    def post(self, request):
        serializer = OrderRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()  # DB 저장

        # TODO 매수 검증 로직 추가
        # inquire - psbl - order : 해당 종목이 시장에서 매수 가능한 지 검증
        # 사용자 계좌 정보 추가
        # 잔고를 받아, 매수 가능한지 검증

        # 자동 매매 태스크 실행
        auto_order.delay(serializer.instance.id)

        return Response({"message": "주문 요청이 접수되었습니다."}, status=201)


## 수동 매수(buy)
class ManualBuyView(APIView):
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


## 수동 매도(sell)
class ManualSellView(APIView):
    def post(self, request):
        symbol = request.data.get("symbol")
        qty = int(request.data.get("qty"))
        order_type = request.data.get("order_type", "market")

        if not symbol or qty <= 0:
            return Response({"error": "symbol, qty 필요"}, status=400)

        result = order_sell(symbol, qty, order_type=order_type)

        return Response({
            "ok": result.ok,
            "message": result.message,
            "order_id": result.order_id,
        })


## 주문 취소
class OrderCancelView(APIView):
    def post(self, request):
        symbol = request.data.get("symbol")
        order_id = request.data.get("order_id")
        qty = int(request.data.get("quantity", 0))
        total = request.data.get("total", False)

        if not symbol or not order_id:
            return Response({"error": "symbol, order_id 필수"}, status=400)

        if not total and qty <= 0:
            return Response({"error": "qty > 0 또는 total=True 필요"}, status=400)

        result = order_cancel(symbol, order_id, qty, total=total)

        return Response({
            "ok": result.ok,
            "message": result.message,
            "order_id": result.order_id,
        })


## 사용자 최근 체결가 조회 (주문번호로 단건 조회)
class RecentCCLD(APIView):
    def get(self, request):
        kis_order_id = request.query_params.get("kis_order_id")
        symbol = request.query_params.get("symbol")

        if not kis_order_id or not symbol:
            return Response({
                "ok": False,
                "message": "요청 시 kis_order_id, symbol 모두 필요"
            }, status=400)

        result = fetch_recent_ccld(kis_order_id, symbol)

        return Response({
            "ok": True,
            "message": "체결내역 조회 완료",
            "content": result
        })

