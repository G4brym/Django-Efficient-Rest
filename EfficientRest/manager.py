import importlib
import json

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import AnonymousUser

from rest_framework import status


# Imports the endpoint folders
api_endpoints = importlib.import_module(settings.EFFICIENTREST["ENDPOINTS_FOLDER"])


class Manager:
    Code = status.HTTP_500_INTERNAL_SERVER_ERROR
    Result = {}
    Errors = []
    Callback = None

    endpoint = None

    def __init__(self, request, endpoint, action):
        self.Code = status.HTTP_500_INTERNAL_SERVER_ERROR
        self.Result = {}
        self.Errors = []

        has_callback = request.GET.get('callback', None)
        if has_callback:
            self.Callback = has_callback

        self.setCode(self.process(request, endpoint, action))

    def getResult(self):
        if (int(str(self.endpoint.getCode())[:1]) in [4, 5]):
            errors = self.endpoint.getErrors()
            if(len(errors) == 1):
                return {"error": errors[0]}
            else:
                return {"errors": errors}

        return self.endpoint.Result

    def getCode(self):
        return self.Code

    def setCode(self, code):
        self.Code = code

    def getSafe(self):
        return self.endpoint.getSafe()

    def addError(self, error):
        self.Errors.append(error)

    def process(self, request, endpoint, action):
        # Respond to CORS requests, almost never enters this because of the middleware, but just in case
        if request.method == "OPTIONS":
            return status.HTTP_200_OK

        # Checks if the endpoint is defined
        try:
            self.endpoint = getattr(api_endpoints, str('api_' + endpoint))(request, action)
        except ValueError:
            self.addError("not_found")
            return status.HTTP_404_NOT_FOUND
        else:
            # Endpoint is defnined

            # Checks if the endpoint allow this HTTP method
            if request.method not in self.endpoint.getMethods():
                self.addError("method_not_allowed")
                return status.HTTP_405_METHOD_NOT_ALLOWED

            # Checks if the endpoint requires auth
            if self.endpoint.requires_auth() and request.user == None:
                self.addError("invalid_request")
                return status.HTTP_401_UNAUTHORIZED


            # Check if the endpoint requires any action
            if self.endpoint.requires_action() and action == "":
                self.addError("action_required")
                return status.HTTP_400_BAD_REQUEST

            # Runs the endpoint logics
            self.endpoint.process()

            # Gets the endpoint answers
            response = self.endpoint.getResult()

            # Display the result in the console, but only if the debug is on
            if settings.DEBUG:
                print(json.dumps(response))

            return self.endpoint.getCode()


# TODO: finish a local request for automated tests
class LocalRequest(Manager):
    def __init__(self, request, endpoint, action):
        self.result = {
            "code": 500,
            "result": {},
            "errors": []
        }

        tmp_callback = request.GET.get('callback', None)
        if tmp_callback:
            self.result["callback"] = tmp_callback

        self.setCode(self.process(request, endpoint, action))
