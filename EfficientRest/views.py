from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from EfficientRest.manager import Manager

from rest_framework.decorators import api_view
from rest_framework.response import Response


@csrf_exempt
def index_req(request):
    return JsonResponse({"error": "not found"}, status=404)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def api_req(request, endpoint, action=""):
    result = Manager(request, str(endpoint), str(action))

    return Response(result.getResult(), status=result.getCode())

        # Old method
        #dict = {
        #    "callback": willCallback,
        #    "response": json.dumps(result.getResult())
        #}
        #return render(request, 'api_callback.html', dict, status=result.getCode(), content_type="application/json")