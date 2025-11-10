from rest_framework.views import APIView
from rest_framework.response import Response
from trading.services.indicators import calculate_rsi
from trading.services.kis_client import get_price_data  # 한투 API 래퍼
import pandas as pd

class RSIView(APIView):
    def get(self, request):
        symbol = request.query_params.get('symbol', '005930')
        df = pd.DataFrame(get_price_data(symbol))
        df['RSI(2)'] = calculate_rsi(df)

        return Response(df[['date', 'close', 'RSI(2)']].tail(10).to_dict(orient='records'))