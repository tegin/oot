from .connection import OdooConnectionXMLRPC
from .fields import Field
from .oot import Oot


class OotXmlRpc(Oot):
    model = ""
    function = ""
    connection_class = OdooConnectionXMLRPC

    odoo_user = Field(name="Odoo user", required=True, sequence=2)
    odoo_db = Field(name="Odoo Database", required=True, sequence=1)
    odoo_password = Field(name="Odoo Password", required=True, sequence=3)

    def check_key(self, key, **kwargs):
        return self.connection.execute_action(
            key,
            model=kwargs.get("model", self.model),
            function=kwargs.get("function", self.function),
        )
