from rest_framework.response import Response
from rest_framework.views import APIView

from .services import get_access_token_info


class TokenStatusView(APIView):
    """
    Simple endpoint to inspect cached token metadata.
    """

    def get(self, request):
        return Response(get_access_token_info())
