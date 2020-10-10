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
ENDPOINTS_PUT: List[str] = []


@routes.get("/")
async def version(request) -> json_response:
    """Return version of the WGT module."""
    print(request)
    data = {"version": __version__, "wgt_url": "/wgt/"}
    return json_response(data)


@routes.get("/status/{attribute}")
async def stosslueftung(request):
    """Return stosslueftung modus."""
    print(request)
    attribute = request.match_info["attribute"].lower()

    # Check if the attribute is a valid endpoint
    data = {"error": 0}
    if attribute not in ENDPOINTS:
        logging.info("Failed to get %s", attribute)
        raise web.HTTPNotFound

    # Connect to wgt and read attribute
    with WGT("10.1.1.29", version="1.06") as wgt:
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
    app = web.Application()
    app.add_routes(routes)
    web.run_app(app)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
