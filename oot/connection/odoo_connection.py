class OdooConnection:
    def __init__(self, datajson):
        self.j_data = datajson
        self.set_params()

    def set_params(self):
        pass

    def execute_action(self, key, **kwargs):
        pass

    @classmethod
    def check_configuration(cls, parameters, oot):
        pass
