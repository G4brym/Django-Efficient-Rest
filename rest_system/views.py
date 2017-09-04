from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from rest_system.manager import Manager


@csrf_exempt
def index_req(request):
    return JsonResponse({"error": "not found"}, status=404)

@csrf_exempt
def api_req(request, endpoint, action=""):
    result = Manager(request, str(endpoint), str(action))

    return JsonResponse(result.getResult(), status=result.getCode())

        # Old method
        #dict = {
        #    "callback": willCallback,
        #    "response": json.dumps(result.getResult())
        #}
        #return render(request, 'api_callback.html', dict, status=result.getCode(), content_type="application/json")