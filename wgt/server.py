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

WGT_URL = "/status/"


def put_endpoints(endpoints_get: Dict[str, Any]) -> Dict[str, Any]:
    """Populate the put endpoint list."""
    endpoints_put = {}
    with WGT(ip="10.1.1.29", version="1.06") as wgt:
        # TODO: Do it without instantiation of a WGT
        for endpoint, type_ in endpoints_get.items():
            # Check if it can be set
            try:
                setattr(wgt, endpoint, None)
            except AttributeError:
                continue
            except TypeError:
                pass
            # Check the corresponding type
            type_ = type(getattr(wgt, endpoint))
            endpoints_put[endpoint] = type_
    return endpoints_put


def get_endpoints() -> Dict[str, Any]:
    """Get endpoint names."""
    endpoints_get = {}
    with WGT(ip="10.1.1.29", version="1.06") as wgt:
        for endpoint in WGT.get_all_attributes():
            # Get the corresponding type
            # TODO: Do it without instantiation of a WGT
            type_ = type(getattr(wgt, endpoint))
            endpoints_get[endpoint] = type_
    return endpoints_get


@routes.get("/")
async def info(request: Request) -> Response:
    """Return version of the WGT module."""
    data: Dict[str, Union[List, str]] = {}
    data["version"] = __version__
    data["wgt_url"] = WGT_URL
    data["get_endpoints"] = list(request.app["get_endpoints"].keys())
    data["put_endpoints"] = list(request.app["put_endpoints"].keys())
    return web.json_response(data)


def validate_endpoint_get(request: Request) -> str:
    """Ensure that the given endpoint is valid. If not raise a 404."""

    endpoint = str(request.match_info["endpoint"]).lower()

    if endpoint not in request.app["get_endpoints"]:
        logging.info("Failed to get %s", endpoint)
        raise web.HTTPNotFound

    return endpoint


def validate_endpoint_put(request: Request) -> str:
    """Ensure that the given endpoint is valid. If not raise a 405."""

    endpoint = validate_endpoint_get(request)

    if endpoint not in request.app["put_endpoints"]:
        logging.info("Failed to put %s", endpoint)
        raise web.HTTPMethodNotAllowed(method="put", allowed_methods="get")
    return endpoint


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

    # Validate that this is an actual endpoint
    endpoint = validate_endpoint_put(request=request)

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
    type_ = request.app["get_endpoints"][endpoint]
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


@routes.get(WGT_URL + "{endpoint}")
async def get_status(request: Request) -> Response:
    """Return status."""

    # Check if the attribute is a valid endpoint
    endpoint = validate_endpoint_get(request)

    data: Dict[str, Union[str, Dict[str, Union[str, int, float]]]] = {}
    data["error"] = ""

    # Connect to wgt and read attribute
    with WGT(ip=request.app["wgt_ip"], version=request.app["wgt_version"]) as wgt:
        status = getattr(wgt, endpoint)

    # Convert status to a dict
    if isinstance(status, (Enum, Unit)):
        data[endpoint] = {"name": status.name, "value": status.value}
    elif isinstance(status, timedelta):
        if status.days > 0:
            data[endpoint] = {"name": f"{status.days} Tage", "value": status.days}
        else:
            minutes = status.seconds / 60
            data[endpoint] = {"name": f"{minutes} Minuten", "value": minutes}
    elif status is None:
        data["error"] = f"Endpoint '{endpoint}' is not available in your WGT version.'"
    else:
        logging.error("Couldn't parse status of %s", endpoint)
        raise web.HTTPInternalServerError

    return web.json_response(data)


def main() -> None:
    """Start the server."""
    app = web.Application()
    app["wgt_ip"] = "10.1.1.29"
    app["wgt_version"] = "1.06"
    get_endpoint_list = get_endpoints()
    app["get_endpoints"] = get_endpoint_list
    app["put_endpoints"] = put_endpoints(get_endpoint_list)
    app.add_routes(routes)
    web.run_app(app)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
