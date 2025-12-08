
from trading.models import OrderRequest

def cancel_order_request(order_id: int):
    try:
        order_request = OrderRequest.objects.get(id=order_id)
    except OrderRequest.DoesNotExist:
        return False

    order_request.delete()
    return True