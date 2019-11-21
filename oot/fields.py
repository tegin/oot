class Field:
    def __init__(
        self, name, description=False, placeholder=False, required=True, sequence=10
    ):
        self.name = name
        self.description = description
        self.placeholder = placeholder
        self.required = required
        self.sequence = sequence

    def generate(self):
        result = {"name": self.name, "sequence": self.sequence}
        if self.description:
            result["description"] = self.description
        if self.placeholder:
            result["placeHolder"] = self.placeholder
        if self.required:
            result["required"] = self.required
        return result
