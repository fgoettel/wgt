"""Provide the WGT info to other services."""
import logging
from datetime import timedelta
from enum import Enum
from typing import List

from aiohttp import web
from aiohttp.web import json_response

from wgt import WGT, __version__
from wgt.types import Unit

routes = web.RouteTableDef()
# Todos:
# . generate wgt instance
# . iterate over sensible values (see read all)
# . generate GET for all
# . generate POST/PUT for all that allow setattr
# Profit
ENDPOINTS = list(WGT.get_all_attributes())
ENDPOINTS_PUT = {}
WGT_IP = "10.1.1.29"
WGT_VERSION = "1.06"
WGT_URL = "/status/"

def populate_put():
    """Populate the put endpoint list."""
    with WGT(ip=WGT_IP, version=WGT_VERSION) as wgt:
        for attr in ENDPOINTS:
            # Check if it can be set
            try:
                setattr(wgt, attr, None)
            except AttributeError:
                continue
            except TypeError:
                pass
            # Check the corresponding type
            type_ = type(getattr(wgt, attr))

            ENDPOINTS_PUT[attr] = type_
    logging.info("Endpoints with put: %s", ENDPOINTS_PUT)


@routes.get("/")
async def info(request) -> json_response:
    """Return version of the WGT module."""
    print(request)
    data = {"version": __version__, "wgt_url": WGT_URL}
    data["endpoints_get"] = ENDPOINTS
    data["endpoints_put"] = ENDPOINTS_PUT
    return json_response(data)

def validate_endpoint_get(endpoint):
    if endpoint not in ENDPOINTS:
        logging.info("Failed to get %s", endpoint)
        raise web.HTTPNotFound

def validate_endpoint_put(endpoint):
    if endpoint not in ENDPOINTS_PUT.keys():
        logging.info("Failed to put %s", endpoint)
        raise web.HTTPMethodNotAllowed(method="put", allowed_methods="get")

@routes.put(WGT_URL + "{endpoint}")
async def put_status(request):

    # Get endpoint name
    endpoint = request.match_info["endpoint"].lower()

    # Validate that this is an actual endpoint
    validate_endpoint_get(endpoint)
    validate_endpoint_put(endpoint)

    # Ensure that the data was put as json/application type
    if not request.content_type == "application/json":
        raise web.HTTPUnsupportedMediaType(reason="Only application/json ")

    # Try to get the data and translate it to a json
    text = await request.text()
    try:
        data = json.loads(text)
    except ValueError:
        raise web.HTTPUnsupportedMediaType(reason="Couldn't convert data to json.")
    logging.debug("Received %s", data)

    # Ensure that we he have the expected keywords
    value = data.get("value", None)
    name = data.get("name", None)
    if (value is None) and (name is None):
         raise web.HTTPUnprocessableEntity(reason="Need either name or value in request.")


    raise web.HTTPNotImplemented

@routes.get(WGT_URL + "{attribute}")
async def get_status(request):
    """Return status."""
    attribute = request.match_info["attribute"].lower()

    # Check if the attribute is a valid endpoint
    data = {"error": 0}
    validate_endpoint_get(attribute)

    # Connect to wgt and read attribute
    with WGT(ip=WGT_IP, version=WGT_VERSION) as wgt:
        status = getattr(wgt, attribute)

    # Convert status to a dict
    if isinstance(status, (Enum, Unit)):
        data[attribute] = {"name": status.name, "value": status.value}
    elif isinstance(status, timedelta):
        if status.days > 0:
            data[attribute] = {"name": f"{status.days} Tage", "value": status.days}
        else:
            minutes = status.seconds * 60
            data[attribute] = {"name": f"{minutes} Minuten", "value": minutes}
    elif status is None:
        data["error"] = f"Endpoint '{attribute}' is not available in your WGT version.'"
    else:
        logging.error("Couldn't parse status of %s", attribute)
        raise web.HTTPInternalServerError

    return web.json_response(data)


def main():
    """Start the server."""
    populate_put()
    app = web.Application()
    app.add_routes(routes)
    web.run_app(app)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
