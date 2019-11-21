from xmlrpc.client import ServerProxy

from .odoo_connection import OdooConnection


class OdooConnectionXMLRPC(OdooConnection):
    def set_params(self):
        self.odoo_host = self.j_data["host"]
        self.odoo_user = self.j_data["user"]
        self.odoo_db = self.j_data["db"]
        self.odoo_password = self.j_data["password"]
        self.common = ServerProxy("{}/xmlrpc/2/common".format(self.odoo_host))
        self.uid = self.common.authenticate(
            self.odoo_db, self.odoo_user, self.odoo_password, {}
        )
        self.models = ServerProxy("{}/xmlrpc/2/object".format(self.odoo_host))

    def execute_action(self, key, model="", function="", **kwargs):
        self.models.execute_kw(
            self.odoo_db, self.uid, self.odoo_password, model, function, [key]
        )
