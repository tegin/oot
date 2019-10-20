import json
import time
import os
from flask import Flask, render_template, request
from werkzeug.serving import make_server
import threading
import logging
import requests
from .access_point import OotAccessPoint
from .utils import is_interface_up
from wifi import Cell
import pycountry
import subprocess

_logger = logging.getLogger(__name__)

COUNTRIES = {c.alpha_2: c.name for c in pycountry.countries}


def check_configuration(result, odoo_link, iot_template):
    response = requests.post(odoo_link, data={"template": iot_template})
    response.raise_for_status()
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


def initialize(oot):
    app = Flask(
        __name__,
        template_folder="%s/templates" % oot.folder,
        static_folder="%s/static" % oot.folder,
    )
    app.secret_key = os.urandom(12)

    connected_eth = is_interface_up("eth0")
    connected_eth = False

    global processed, ssid, password, odoo_link, result_data, country, hidden
    ssid = False
    password = False
    odoo_link = False
    result_data = False
    processed = False
    country = False
    hidden = False
    interfaces = False
    if not connected_eth:
        interfaces = [cell.ssid for cell in Cell.all("wlan0")]

    @app.route("/")
    def form():
        _logger.debug("inside form")
        return render_template(
            oot.form_template,
            port=3000,
            fields=oot.fields or {},
            interfaces=interfaces,
            countries=COUNTRIES,
            connected=connected_eth,
        )

    @app.route("/result", methods=["POST", "GET"])
    def result():
        if request.method == "POST":
            results = request.form
            result_dic = results.to_dict(flat=False)
            result = {}
            for key in oot.fields:
                value = result_dic.get(key, False)
                if value:
                    value = value[0]
                result[key] = value
            if connected_eth:
                check_configuration(result, result_dic["odoo_link"][0], oot.template)
                with open(oot.connection_path, "w+") as outfile:
                    json.dump(result, outfile)
            else:
                global odoo_link, ssid, password, country, result_data, hidden
                odoo_link = result_dic["odoo_link"][0]
                ssid = result_dic["ssid"][0]
                password = result_dic["password"][0] or False
                hidden = False
                country = result_dic["country"][0]
                _logger.info(result_dic)
                result_data = result.copy()
            global processed
            processed = True
            return render_template(
                oot.result_template, result=result, fields=oot.fields
            )

    _logger.info("Configuring Access Point")
    access_point = OotAccessPoint(ssid="OoTDevice")
    server = ServerThread(app)
    try:
        access_point.start()
        _logger.info("Access Point configured")
        if not access_point.is_running():
            raise Exception("Access point could not be raised")
        server.start()
        while not processed and access_point.is_running():
            pass
        _logger.info("Configuration has been launched. Waiting for execution")
        time.sleep(10)
    except KeyboardInterrupt:
        server.shutdown()
        access_point.stop()
        raise
    server.shutdown()
    _logger.info("Server closed")
    access_point.stop()
    _logger.info("Access Point closed")
    if connected_eth:
        return
    if not connected_eth and result_data:
        with open("/etc/wpa_supplicant/wpa_supplicant.conf", "w") as f:
            f.write("ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n")
            f.write("update_config=1\n")
            if country:
                f.write("country=%s\n\n" % country)
            f.write("network={")
            f.write("        ssid=%s\n" % ssid)
            if password:
                f.write("        psk=%s\n" % password)
            if hidden:
                f.write("        scan_ssid=1")
            f.write("}\n")
        subprocess.run(["wpa_cli", "terminate"])
        subprocess.run(["systemctl", "restart", "dhcpcd.service"])
        checks = 0
        while not is_interface_up("wlan0") and checks < 20:
            checks += 1
            time.sleep(1)
        if checks >= 20:
            raise Exception("WPA could not be configured")
        check_configuration(result_data, odoo_link, oot.template)
        with open(oot.connection_path, "w+") as outfile:
            json.dump(result_data, outfile)
        return
    raise Exception("Connection was not executed properly")
