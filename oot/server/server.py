import json
import logging
import os
import subprocess
import threading
import time

import pycountry
import requests
from flask import Flask, render_template, request
from werkzeug.serving import make_server
from wifi import Cell

from .access_point import OotAccessPoint
from .utils import is_interface_up

_logger = logging.getLogger(__name__)

DEFAULT_IP = "192.168.45.1"

COUNTRIES = {c.alpha_2: c.name for c in pycountry.countries}


def check_configuration(result, odoo_link, oot):
    oot.checking_connection()
    response = requests.post(odoo_link, data={"template": oot.template})
    try:
        response.raise_for_status()
    except requests.HTTPError:
        oot.failure_connection()
        raise
    oot.finished_connection()
    result.update(json.loads(response.content.decode("utf-8")))


class ServerThread(threading.Thread):
    def __init__(self, app):
        threading.Thread.__init__(self)
        self.srv = make_server(host="0.0.0.0", port=3000, app=app)
        self.ctx = app.app_context()
        self.ctx.push()
        _logger.debug("ServerThread Class Initialized")

    def run(self):
        _logger.debug("Serve forever")
        self.srv.serve_forever()

    def shutdown(self):
        _logger.debug("Shutdown")
        self.srv.shutdown()


def initialize(oot, no_access_point=False):
    app = Flask(
        __name__,
        template_folder="%s/templates" % oot.folder,
        static_folder="%s/static" % oot.folder,
    )
    app.secret_key = os.urandom(12)

    connected_eth = is_interface_up("eth0")

    parameters = {"interfaces": []}
    if not connected_eth and not no_access_point:
        parameters["interfaces"] = [cell.ssid for cell in Cell.all("wlan0")]

    @app.route("/")
    def form():
        _logger.debug("inside form")
        return render_template(
            oot.form_template,
            port=3000,
            fields=oot._fields or {},
            interfaces=parameters["interfaces"],
            countries=COUNTRIES,
            connected=connected_eth or no_access_point,
        )

    @app.route("/extra_tools", methods=["POST", "GET"])
    def extra_tools():
        extra_tools = oot.extra_tools()
        for key in request.args:
            if key == "tool":
                tool = extra_tools.get(request.args.get(key))
                if tool:
                    tool["function"]()
        return render_template(oot.extra_tools_template, tools=oot.extra_tools())

    @app.route("/result", methods=["POST", "GET"])
    def result():
        if request.method == "POST":
            results = request.form
            result_dic = results.to_dict(flat=False)
            result = {}
            for key in oot._fields:
                value = result_dic.get(key, False)
                if value:
                    value = value[0]
                result[key] = value
            if connected_eth or no_access_point:
                check_configuration(result, result_dic["odoo_link"][0], oot)
                with open(oot.connection_path, "w+") as outfile:
                    json.dump(result, outfile)
            else:
                parameters.update(
                    {
                        "odoo_link": result_dic["odoo_link"][0],
                        "ssid": result_dic["ssid"][0],
                        "password": result_dic["password"][0] or False,
                        "hidden": False,
                        "country": result_dic["country"][0],
                        "result_data": result.copy(),
                    }
                )
                oot.waiting_for_connection()
            parameters["processed"] = True
            return render_template(
                oot.result_template, result=result, fields=oot.fields
            )

    if no_access_point:
        access_point = False
    else:
        _logger.info("Configuring Access Point")
        access_point = OotAccessPoint(ssid=oot.ssid, ip=DEFAULT_IP)
    interfaces = is_interface_up("wlan0") or []
    first_start = not any(
        interface.get("addr", False) == DEFAULT_IP for interface in interfaces
    )
    process(oot, access_point, app, parameters, connected_eth, first_start)


def process(oot, access_point, app, parameters, connected_eth, first_start=False):
    server = ServerThread(app)
    try:
        if access_point:
            access_point.start()
            if first_start:
                _logger.info(
                    "On first start we must create twice the access point for configuration"
                )
                access_point.stop()
                access_point.start()
            _logger.info("Access Point configured")
            if not access_point.is_running():
                raise Exception("Access point could not be raised")
        server.start()
        oot.start_connection(server, access_point)
        while not parameters.get("processed") and (not access_point or access_point.is_running()):
            pass
        _logger.info("Configuration has been launched. Waiting for execution")
        time.sleep(10)
    except KeyboardInterrupt:
        server.shutdown()
        if access_point:
            access_point.stop()
        raise
    server.shutdown()
    _logger.info("Server closed")
    if access_point:
        access_point.stop()
        _logger.info("Access Point closed")
    if connected_eth:
        return
    if not connected_eth and parameters.get("result_data", False) and access_point:
        with open("/etc/wpa_supplicant/wpa_supplicant.conf", "w") as f:
            f.write("ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n")
            f.write("update_config=1\n")
            if parameters.get("country"):
                f.write("country=%s\n\n" % parameters.get("country"))
            f.write("network={\n")
            f.write('        ssid="%s"\n' % parameters.get("ssid"))
            if parameters.get("password"):
                f.write('        psk="%s"\n' % parameters.get("password"))
            if parameters.get("hidden"):
                f.write("        scan_ssid=1")
            f.write("}\n")
        subprocess.run(["wpa_cli", "terminate"])
        subprocess.run(["systemctl", "restart", "dhcpcd.service"])
        checks = 0
        interfaces = is_interface_up("wlan0") or []
        while (
            not any(
                interface.get("addr", False) != DEFAULT_IP for interface in interfaces
            )
        ) and checks < 20:
            checks += 1
            time.sleep(1)
            interfaces = is_interface_up("wlan0") or []
        if checks >= 20:
            parameters["processed"] = False
            return process(oot, access_point, app, parameters, connected_eth)
        try:
            check_configuration(
                parameters.get("result_data"), parameters.get("odoo_link"), oot
            )
        except requests.HTTPError:
            parameters["processed"] = False
            return process(oot, access_point, app, parameters, connected_eth)
        with open(oot.connection_path, "w+") as outfile:
            json.dump(parameters.get("result_data"), outfile)
