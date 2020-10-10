"""Provide the WGT info to other services."""
import logging
from datetime import timedelta
from enum import Enum

from aiohttp import web

from wgt import __version__
from wgt.lueftungsanlage import WGT
from wgt.types import Unit

routes = web.RouteTableDef()
# Todos:
# . generate wgt instance
# . iterate over sensible values (see read all)
# . generate GET for all
# . generate POST/PUT for all that allow setattr
# Profit
ENDPOINTS = list(WGT.get_all_attributes())


@routes.get("/")
async def version(request):
    """Return version of the WGT module."""
    print(request)
    data = {"version": __version__, "wgt_url": "/wgt/"}
    return web.json_response(data)


@routes.get("/status/{attribute}")
async def stosslueftung(request):
    """Return stosslueftung modus."""
    print(request)
    attribute = request.match_info["attribute"].lower()

    # Check if the attribute is a valid endpoint
    data = {"error": 0}
    if attribute not in ENDPOINTS:
        logging.info("Trying to access %s", attribute)
        data["error"] = "invalid endpoint"
        return web.json_response(data)

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
        data["error"] = f"Couldn't parse '{attribute}'' with '{status}'"
    return web.json_response(data)


def main():
    """Start the server."""
    app = web.Application()
    app.add_routes(routes)
    web.run_app(app)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
