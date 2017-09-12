import json
import math

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django import forms

from EfficientRest.forms import modelField

from rest_framework import status
from rest_framework.settings import api_settings
from rest_framework.renderers import JSONRenderer

class EndpointType():
    methods = []

    user = None

    request = None
    action = None

    input_data = None

    Code = status.HTTP_500_INTERNAL_SERVER_ERROR
    Result = {}
    Errors = []

    useSafe = True

    def __init__(self, request, action):
        self.Code = status.HTTP_500_INTERNAL_SERVER_ERROR
        self.Result = {}
        self.Errors = []

        self.request = request
        self.action = action

        self.input_data = self.request.data

    def get_special_response(self):
        try:
            return self.Meta.special_response
        except:
            return False

    def getSafe(self):
        return self.useSafe

    def setSafe(self, value):
        self.useSafe = value

    def requires_action(self):
        return self.Meta.requires_action

    def requires_auth(self):
        return self.Meta.requires_auth

    def getInput(self):
        return self.input_data

    def getInputPOST(self):
        return self.request.POST

    def getInputJson(self):
        try:
            return json.loads(self.input_data.decode("utf-8"))
        except AttributeError:
            return self.input_data.dict()
        except ValueError:
            return json.loads("{}")

    def getMethods(self):
        return self.Meta.methods

    def setResult(self, result):
        self.Result = result

    def getResult(self):
        return self.Result

    def getCode(self):
        return self.Code

    def setCode(self, code):
        self.Code = code

    def getErrors(self):
        return self.Errors

    def addError(self, error):
        self.Errors.append(error)

    def setErrors(self, errors):
        self.Errors = errors

    def addErrorJson(self, error):
        self.Errors.append(json.loads(error))

    def setUser(self, user):
        self.user = user

    def process(self):
        # Must be overwriten
        self.setCode(status.HTTP_500_INTERNAL_SERVER_ERROR)



class Model(EndpointType):

    def process(self):
        if self.requires_action():
            if settings.DEBUG:
                self.setCode(getattr(self, str(self.request.method.lower() + "_" + self.action))())
            else:
                try:
                    self.setCode(getattr(self, str(self.request.method.lower() + "_" + self.action))())
                except AttributeError:
                    self.addError("not_found")
                    self.setCode(status.HTTP_404_NOT_FOUND)
        else:
            if self.action:
                if settings.DEBUG:
                    self.setCode(getattr(self, str(self.request.method.lower() + "_process_single"))(self.action))
                else:
                    try:
                        self.setCode(getattr(self, str(self.request.method.lower() + "_process_single"))(self.action))
                    except AttributeError:
                        self.addError("not_found")
                        self.setCode(status.HTTP_404_NOT_FOUND)
            else:
                if settings.DEBUG:
                    self.setCode(getattr(self, str(self.request.method.lower() + "_process"))())
                else:
                    try:
                        self.setCode(getattr(self, str(self.request.method.lower() + "_process"))())
                    except AttributeError:
                        self.addError("not_found")
                        self.setCode(status.HTTP_404_NOT_FOUND)


class Service(EndpointType):

    def process(self):
        if self.requires_action:
            if settings.DEBUG:
                self.setCode(getattr(self, str(self.request.method.lower() + "_" + self.action))())
            else:
                try:
                    self.setCode(getattr(self, str(self.request.method.lower() + "_" + self.action))())
                except AttributeError:
                    self.addError("not_found")
                    self.setCode(status.HTTP_404_NOT_FOUND)
        else:
            try:
                self.setCode(getattr(self, str(self.request.method.lower() + "_process"))())
            except AttributeError:
                self.addError("not_found")
                self.setCode(status.HTTP_404_NOT_FOUND)

class BaseModel(Model):
    class Meta:
        methods = ["GET", "POST", "PATCH", "DELETE"]

        requires_action = False
        requires_auth = True

        Model = None
        Serializer = None

    def __init__(self, request, action):
        Model.__init__(self, request, action)

    def get_process(self):
        #####
        # Retrieves the number of pages for this model
        #####

        page = self.request.GET.get('page', None)
        if page != None:
            try:
                clean_id = int(page)
            except:
                return status.HTTP_400_BAD_REQUEST

            skip = (clean_id - 1) * api_settings.PAGE_SIZE
            get = skip + api_settings.PAGE_SIZE

            totalObjs = self.Meta.Model.objects.all().count()

            if skip > totalObjs or clean_id == 0:
                return status.HTTP_406_NOT_ACCEPTABLE

            try:
                objectList = self.Meta.Model.objects.all()[skip:get]
            except ObjectDoesNotExist:
                return status.HTTP_404_NOT_FOUND

            serializer = self.Meta.Serializer(objectList, many=True).data

            if totalObjs <= get:
                next = False
            else:
                next = True

            if clean_id < 2:
                previous = False
            else:
                previous = True


            self.setResult({"results": serializer, "meta":{"count": totalObjs, "next": next, "previous": previous}})
            return status.HTTP_200_OK


        # Process Coalescing
        ids = self.request.GET.getlist('ids[]', None)
        if ids != None:
            clean_ids = []

            for id in ids:
                try:
                    clean_ids.append(int(id))
                except:
                    return status.HTTP_400_BAD_REQUEST

            objectList = self.Meta.Model.objects.filter(id__in=clean_ids)

            serializer = self.Meta.Serializer(objectList, many=True).data

            self.setResult(serializer)
            return status.HTTP_200_OK



        objectList = self.Meta.Model.objects.all().count()

        pages = math.ceil(objectList / api_settings.PAGE_SIZE)
        if pages > 0:
            pages = pages-1

        self.setResult({"pages": pages, "count": objectList})
        return status.HTTP_200_OK

    def get_process_single(self, id):
        #####
        # Retrieves a single object
        #####

        try:
            clean_id = int(id)
        except:
            return status.HTTP_400_BAD_REQUEST

        try:
            object = self.Meta.Model.objects.get(id=clean_id)
        except ObjectDoesNotExist:
            return status.HTTP_404_NOT_FOUND

        self.setResult(object.get_as_dict())
        return status.HTTP_200_OK

    def post_process(self):
        #####
        # Saves a new Object
        #####

        serializer = self.Meta.Serializer(data=self.getInputPOST())
        if serializer.is_valid():
            serializer.save()
            self.setResult(serializer.data)
            return status.HTTP_201_CREATED

        self.setErrors(serializer.errors)
        return status.HTTP_400_BAD_REQUEST

    def put_process_single(self, id):
        #####
        # Updates an Object
        #####

        try:
            clean_id = int(id)
        except:
            return status.HTTP_400_BAD_REQUEST

        try:
            object = self.Meta.Model.objects.get(id=clean_id)
        except:
            return status.HTTP_404_NOT_FOUND

        serializer = self.Meta.Serializer(object, data=self.getInput(), partial=True)

        if serializer.is_valid():
            serializer.save()
            self.setResult(serializer.data)
            return status.HTTP_202_ACCEPTED

    def delete_process_single(self, id):
        #####
        # Deletes a single product
        #####

        try:
            clean_id = int(id)
        except:
            return status.HTTP_400_BAD_REQUEST

        try:
            object = self.Meta.Model.objects.get(id=clean_id)
        except ObjectDoesNotExist:
            return status.HTTP_404_NOT_FOUND

        object.delete()

        return status.HTTP_200_OK