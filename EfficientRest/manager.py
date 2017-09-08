import importlib
import json

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from EfficientRest.models import UserAuthKeys

# Imports the endpoint folders
api_endpoints = importlib.import_module(settings.EFFICIENTREST["ENDPOINTS_FOLDER"])


class Manager:
    Code = 500
    Result = {}
    Errors = []
    Callback = None

    endpoint = None

    def __init__(self, request, endpoint, action):
        self.Code = 500
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


        if (self.endpoint.get_special_response()):

            return self.endpoint.getResult()

        else:

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
            return 200

        # Checks if the endpoint is defined
        try:
            self.endpoint = getattr(api_endpoints, str('api_' + endpoint))(request, action)
        except ValueError:
            self.addError("not_found")
            return 404
        else:
            # Endpoint is defnined

            # Checks if the endpoint allow this HTTP method
            if request.method not in self.endpoint.getMethods():
                self.addError("method_not_allowed")
                return 405

            # Checks if the endpoint requires auth
            if self.endpoint.requires_auth():
                try:
                    authkey = request.META['HTTP_AUTHORIZATION']
                except:
                    self.addError("invalid_request")
                    return 401

                if authkey.strip() != "":

                    if "Bearer " not in authkey:
                        self.addError("invalid_request")
                        return 401
                    else:
                        authkey = authkey.replace("Bearer ", "")


                    # Try to get the auth key
                    try:
                        keymodel = UserAuthKeys.objects.get(key=authkey)
                    # TODO: add ip verification, against bruteforce
                    except ObjectDoesNotExist:
                        # Key dont exist
                        self.addError("invalid_request")
                        return 401

                    # Check the key expire date
                    if keymodel.valid():
                        self.endpoint.setUser(keymodel.user)
                    else:
                        self.addError("invalid_grant")
                        return 406

                # User is not authenticated, key was not provided with the request
                else:
                    self.addError("invalid_request")
                    return 401


            # Check if the endpoint requires any action
            if self.endpoint.requires_action() and action == "":
                self.addError("action_required")
                return 400

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
