from xmlrpc.client import ServerProxy

from .odoo_connection import OdooConnection


class OdooConnectionXMLRPC(OdooConnection):
    def set_params(self):
        self.odoo_host = self.j_data["host"]
        self.odoo_user = self.j_data["odoo_user"]
        self.odoo_db = self.j_data["odoo_db"]
        self.odoo_password = self.j_data["odoo_password"]
        self.common = ServerProxy("{}/xmlrpc/2/common".format(self.odoo_host))
        self.uid = self.common.authenticate(
            self.odoo_db, self.odoo_user, self.odoo_password, {}
        )
        self.models = ServerProxy("{}/xmlrpc/2/object".format(self.odoo_host))

    def execute_action(self, key, model="", function="", **kwargs):
        return self.models.execute_kw(
            self.odoo_db, self.uid, self.odoo_password, model, function, [key]
        )

    @classmethod
    def check_configuration(cls, parameters, oot):
        oot.checking_connection()
        host = parameters.get("odoo_link")
        common = ServerProxy("{}/xmlrpc/2/common".format(host))
        try:
            uid = common.authenticate(
                parameters["result_data"]["odoo_db"],
                parameters["result_data"]["odoo_user"],
                parameters["result_data"]["odoo_password"],
                {},
            )
            if not uid:
                raise Exception("Connection failed")
        except Exception:
            oot.failure_connection()
            raise
        parameters["result_data"].update({"host": host})
        oot.finished_connection()
