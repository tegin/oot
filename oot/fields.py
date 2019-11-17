class Field:
    def __init__(self, name, description=False, placeholder=False, required=True):
        self.name = name
        self.description = description
        self.placeholder = placeholder
        self.required = required

    def generate(self):
        result = {"name": self.name}
        if self.description:
            result["description"] = self.description
        if self.placeholder:
            result["placeHolder"] = self.placeholder
        if self.required:
            result["required"] = self.required
        return result
