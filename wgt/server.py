"""Provide the WGT info to other services."""
import json
import logging
from datetime import timedelta
from enum import Enum, EnumMeta
from typing import Any, Dict, List, Union

from aiohttp import web
from aiohttp.web_request import Request
from aiohttp.web_response import Response

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
WGT_URL = "/status/"


def populate_put() -> None:
    """Populate the put endpoint list."""
    with WGT(ip="10.1.1.29", version="1.06") as wgt:
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
async def info(request: Request) -> Response:
    """Return version of the WGT module."""
    # TODO: Create info url with datatypes to all endpoints
    # pylint: disable=unused-argument
    data: Dict[str, Union[List, str]] = {}
    data["version"] = __version__
    data["wgt_url"] = WGT_URL
    data["endpoints_get"] = ENDPOINTS
    data["endpoints_put"] = list(ENDPOINTS_PUT.keys())
    return web.json_response(data)


def validate_endpoint_get(endpoint: str) -> None:
    """Ensure that the given endpoint is valid. If not raise a 404."""
    if endpoint not in ENDPOINTS:
        logging.info("Failed to get %s", endpoint)
        raise web.HTTPNotFound


def validate_endpoint_put(endpoint: str) -> None:
    """Ensure that the given endpoint is valid. If not raise a 405."""
    validate_endpoint_get(endpoint)
    if endpoint not in ENDPOINTS_PUT.keys():
        logging.info("Failed to put %s", endpoint)
        raise web.HTTPMethodNotAllowed(method="put", allowed_methods="get")


def value_to_enum(value: str, enum_class: EnumMeta) -> Any:
    """Translate a value to an enum.

    Returns Enum on success, otherwise a HTTPUnprocessableEntity error
    is raised.
    """

    try:
        value_int = int(value)
    except ValueError as int_conversion_error:
        raise web.HTTPUnprocessableEntity(
            reason="Couldnt transform value to int as required for enum."
        ) from int_conversion_error

    try:
        value_typed = enum_class(value_int)
    except ValueError as enum_conversion_error:
        raise web.HTTPUnprocessableEntity(
            reason=f"Invalid value for {enum_class}."
        ) from enum_conversion_error
    return value_typed


@routes.put(WGT_URL + "{endpoint}")
async def put_status(request: Request) -> Response:
    """Set a status of the wgt."""

    # Get endpoint name
    endpoint = request.match_info["endpoint"].lower()

    # Validate that this is an actual endpoint
    validate_endpoint_put(endpoint)

    # Ensure that the data was put as json/application type
    if not request.content_type == "application/json":
        raise web.HTTPUnsupportedMediaType(reason="Only application/json ")

    # Try to get the data and translate it to a json
    text = await request.text()
    try:
        data = json.loads(text)
    except ValueError as data_conversion_error:
        raise web.HTTPUnsupportedMediaType(
            reason="Couldn't convert data to json."
        ) from data_conversion_error
    logging.debug("Received %s", data)

    # Ensure that we he have the expected keywords
    value = data.get("value", None)
    if value is None:
        raise web.HTTPUnprocessableEntity(reason="Need 'value' in request.")

    # Convert received input to expected format
    type_ = ENDPOINTS_PUT[endpoint]
    value_typed = None
    if issubclass(type_, Enum):
        value_typed = value_to_enum(value, type_)
    elif issubclass(type_, Unit):
        value_typed = type_(float(value))
    else:
        raise web.HTTPNotImplemented

    # Check if we have a sound value
    if value_typed is None:
        raise web.HTTPInternalServerError

    # Set the typed value
    with WGT(ip=request.app["wgt_ip"], version=request.app["wgt_version"]) as wgt:
        try:
            setattr(wgt, endpoint, value_typed)
        except ValueError as err:
            raise web.HTTPUnprocessableEntity(reason=str(err))
    raise web.HTTPOk


@routes.get(WGT_URL + "{attribute}")
async def get_status(request: Request) -> Response:
    """Return status."""
    attribute = request.match_info["attribute"].lower()

    # Check if the attribute is a valid endpoint
    data: Dict[str, Union[str, Dict[str, Union[str, int, float]]]] = {}
    data = {"error": ""}
    validate_endpoint_get(attribute)

    # Connect to wgt and read attribute
    with WGT(ip=request.app["wgt_ip"], version=request.app["wgt_version"]) as wgt:
        status = getattr(wgt, attribute)

    # Convert status to a dict
    if isinstance(status, (Enum, Unit)):
        data[attribute] = {"name": status.name, "value": status.value}
    elif isinstance(status, timedelta):
        if status.days > 0:
            data[attribute] = {"name": f"{status.days} Tage", "value": status.days}
        else:
            minutes = status.seconds / 60
            data[attribute] = {"name": f"{minutes} Minuten", "value": minutes}
    elif status is None:
        data["error"] = f"Endpoint '{attribute}' is not available in your WGT version.'"
    else:
        logging.error("Couldn't parse status of %s", attribute)
        raise web.HTTPInternalServerError

    return web.json_response(data)


def main() -> None:
    """Start the server."""
    populate_put()  # TODO: only do once needed
    app = web.Application()
    app["wgt_ip"] = "10.1.1.29"
    app["wgt_version"] = "1.06"
    app.add_routes(routes)
    web.run_app(app)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
