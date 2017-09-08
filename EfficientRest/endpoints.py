import json
import math

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django import forms

from EfficientRest.forms import modelField


class EndpointType():
    methods = []

    user = None

    request = None
    action = None

    input_data = None

    Code = 500
    Result = {}
    Errors = []

    useSafe = True

    def __init__(self, request, action):
        self.Code = 500
        self.Result = {}
        self.Errors = []

        self.request = request
        self.action = action

        if self.request.method == "GET":
            self.input_data = self.request.GET
        else:
            self.input_data = self.request.body

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

    def addErrorJson(self, error):
        self.Errors.append(json.loads(error))

    def setUser(self, user):
        self.user = user

    def process(self):
        # Must be overwriten
        self.setCode(500)



class Model(EndpointType):

    def process(self):
        if self.requires_action():
            if settings.DEBUG:
                self.setCode(getattr(self, str(self.request.method.lower() + "_" + self.action))())
            else:
                try:
                    self.setCode(getattr(self, str(self.request.method.lower() + "_" + self.action))())
                except AttributeError:
                    self.addError("not found")
                    self.setCode(404)
        else:
            if self.action:
                if settings.DEBUG:
                    self.setCode(getattr(self, str(self.request.method.lower() + "_process_single"))(self.action))
                else:
                    try:
                        self.setCode(getattr(self, str(self.request.method.lower() + "_process_single"))(self.action))
                    except AttributeError:
                        self.addError("not found")
                        self.setCode(404)
            else:
                if settings.DEBUG:
                    self.setCode(getattr(self, str(self.request.method.lower() + "_process"))())
                else:
                    try:
                        self.setCode(getattr(self, str(self.request.method.lower() + "_process"))())
                    except AttributeError:
                        self.addError("not found")
                        self.setCode(404)


class Service(EndpointType):

    def process(self):
        if self.requires_action:
            if settings.DEBUG:
                self.setCode(getattr(self, str(self.request.method.lower() + "_" + self.action))())
            else:
                try:
                    self.setCode(getattr(self, str(self.request.method.lower() + "_" + self.action))())
                except AttributeError:
                    self.addError("not found")
                    self.setCode(404)
        else:
            try:
                self.setCode(getattr(self, str(self.request.method.lower() + "_process"))())
            except AttributeError:
                self.addError("not found")
                self.setCode(404)

class BaseModel(Model):
    class Meta:
        methods = ["GET", "POST", "PATCH", "DELETE"]

        requires_action = False
        requires_auth = True

        Model = None
        FormFields = {}
        Form2Model = {}

    Form = None

    def __init__(self, request, action):
        Model.__init__(self, request, action)
        self.Form = type('APIForm',  # form name is irrelevant
                (forms.BaseForm,), # Dont remove the first comma in this line, really important
                {'base_fields': self.Meta.FormFields})

    def get_process(self):
        #####
        # Retrieves the number of pages for this model
        #####

        page = self.request.GET.get('page', None)
        if page != None:
            try:
                clean_id = int(page)
            except:
                return 400

            skip = (clean_id - 1) * settings.EFFICIENTREST["OBJECTS_PER_REQUEST"]
            get = skip + settings.EFFICIENTREST["OBJECTS_PER_REQUEST"]

            totalObjs = self.Meta.Model.objects.all().count()

            if skip > totalObjs or clean_id == 0:
                return 406

            try:
                objectList = self.Meta.Model.objects.all()[skip:get]
            except ObjectDoesNotExist:
                return 404

            tmp = []
            for object in objectList:
                tmp.append(object.get_as_dict())

            if totalObjs <= get:
                next = False
            else:
                next = True

            if clean_id < 2:
                previous = False
            else:
                previous = True


            self.setResult({"results": tmp, "meta":{"count": totalObjs, "next": next, "previous": previous}})
            return 200


        # Process Coalescing
        ids = self.request.GET.getlist('ids[]', None)
        if ids != None:
            clean_ids = []
            final_dict = []

            for id in ids:
                try:
                    clean_ids.append(int(id))
                except:
                    return 400

            objectList = self.Meta.Model.objects.filter(id__in=clean_ids)

            for object in objectList:
                final_dict.append(object.get_as_dict())

            self.setResult(final_dict)

            # Disable Django safe mode, so it can actualy return a List
            self.setSafe(False)
            return 200



        objectList = self.Meta.Model.objects.all().count()

        pages = math.ceil(objectList / settings.EFFICIENTREST["OBJECTS_PER_REQUEST"])
        if pages > 0:
            pages = pages-1

        self.setResult({"pages": pages, "count": objectList})
        return 200

    def get_process_single(self, id):
        #####
        # Retrieves a single object
        #####

        try:
            clean_id = int(id)
        except:
            return 400

        try:
            object = self.Meta.Model.objects.get(id=clean_id)
        except ObjectDoesNotExist:
            return 404

        self.setResult(object.get_as_dict())
        return 200

    def post_process(self):
        #####
        # Saves a new Object
        #####

        form = self.Form(self.getInputJson())

        if form.is_valid():
            try:
                final = {}
                for validation_var, model_var in self.Meta.Form2Model.items():
                    if isinstance(model_var, modelField):
                        tmp_var = form.cleaned_data[validation_var]

                        if(model_var.model.objects.filter(id=tmp_var).exists()):
                            final[validation_var+"_id"] = tmp_var
                        else:
                            self.addError("Model Object not found")
                            return 406

                    else:
                        final[model_var] = form.cleaned_data[validation_var]

                object = self.Meta.Model.objects.create(**final)

                self.setResult(object.get_as_dict())
                return 200
            # Error un key value dict
            except KeyError:
                return 500

        else:
            self.addErrorJson(form.errors.as_json())
            print(form.errors.as_json())
            return 400

    def patch_process_single(self, id):
        #####
        # Updates an Object
        #####

        try:
            clean_id = int(id)
        except:
            return 400

        form = self.Form(self.getInputJson())

        if form.is_valid():

            try:
                # TODO: optimize this one two, so FE can send only one var insted of the hole model
                object = self.Meta.Model.objects.get(id=clean_id)
            except ObjectDoesNotExist:
                return 401

            object.desc = form.cleaned_data["desc"]

            return 200

        else:
            self.addErrorJson(form.errors.as_json())
            print(form.errors.as_json())
            return 400

    def delete_process_single(self, id):
        #####
        # Deletes a single product
        #####

        try:
            clean_id = int(id)
        except:
            return 400

        try:
            object = self.Meta.Model.objects.get(id=clean_id)
        except ObjectDoesNotExist:
            return 401

        object.delete()

        return 200