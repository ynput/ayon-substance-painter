import os
import pyblish.api


class CollectWorkfileRepresentation(pyblish.api.InstancePlugin):
    """Create a publish representation for the current workfile instance."""

    order = pyblish.api.CollectorOrder
    label = "Workfile representation"
    hosts = ["substancepainter"]
    families = ["workfile"]

    def process(self, instance):

        context = instance.context
        current_file = context.data.get("currentFile")
        if not current_file:
            self.log.warning("Current file is not saved. File could not be "
                             "collected as workfile representation.")
            return

        folder, file = os.path.split(current_file)
        filename, ext = os.path.splitext(file)

        instance.data["representations"] = [{
            "name": ext.lstrip("."),
            "ext": ext.lstrip("."),
            "files": file,
            "stagingDir": folder,
        }]
