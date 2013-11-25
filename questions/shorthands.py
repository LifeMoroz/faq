# coding=utf-8
import json as _json
from django.http import HttpResponse, Http404


def json(data):
    """
    Returns the HttpResponse object with provided data in json
    """
    return HttpResponse(_json.dumps(data), mimetype='application/json')