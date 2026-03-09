# -*- coding: utf-8 -*-
"""Creator plugin for creating workfiles."""
from ayon_core.pipeline import CreatedInstance, AutoCreator

from ayon_substancepainter.api.pipeline import (
    set_instances,
    set_instance,
    get_instances
)

import substance_painter.project


class CreateWorkfile(AutoCreator):
    """Workfile auto-creator."""
    identifier = "io.openpype.creators.substancepainter.workfile"
    label = "Workfile"
    product_base_type = "workfile"
    product_type = product_base_type
    icon = "document"

    default_variant = "Main"
    settings_category = "substancepainter"
    active_on_create = True

    def create(self):
        if not substance_painter.project.is_open():
            return

        variant = self.default_variant

        # Workfile instance should always exist and must only exist once.
        # As such we'll first check if it already exists and is collected.
        current_instance = next(
            (
                instance for instance in self.create_context.instances
                if instance.creator_identifier == self.identifier
            ), None)

        current_folder_path = None
        if current_instance is not None:
            current_folder_path = current_instance["folderPath"]

        project_entity = self.create_context.get_current_project_entity()
        folder_entity = self.create_context.get_current_folder_entity()
        task_entity = self.create_context.get_current_task_entity()

        project_name = project_entity["name"]
        folder_path = folder_entity["path"]
        task_name = task_entity["name"]
        host_name = self.create_context.host_name

        if current_instance is None:
            self.log.info("Auto-creating workfile instance...")
            product_name = self.get_product_name(
                project_name=project_name,
                project_entity=project_entity,
                folder_entity=folder_entity,
                task_entity=task_entity,
                variant=variant,
                host_name=host_name,
                product_type=self.product_type,
            )
            data = {
                "folderPath": folder_path,
                "task": task_name,
            }

            current_instance = self.create_instance_in_context(product_name,
                                                               data)
        elif (
            current_folder_path != folder_path
            or current_instance["task"] != task_name
        ):
            # Update instance context if is not the same
            product_name = self.get_product_name(
                project_name=project_name,
                project_entity=project_entity,
                folder_entity=folder_entity,
                task_entity=task_entity,
                variant=variant,
                host_name=host_name,
                product_type=self.product_type,
            )
            current_instance["folderPath"] = folder_path
            current_instance["task"] = task_name
            current_instance["productName"] = product_name

        current_instance["active"] = self.active_on_create
        current_instance["variant"] = variant

        set_instance(
            instance_id=current_instance.get("instance_id"),
            instance_data=current_instance.data_to_store()
        )

    def collect_instances(self):
        for instance in get_instances():
            product_base_type = instance.get("productBaseType")
            if not product_base_type:
                product_base_type = instance.get("productType")
            if (
                instance.get("creator_identifier") == self.identifier
                or product_base_type == self.product_base_type
            ):
                self.create_instance_in_context_from_existing(instance)

    def update_instances(self, update_list):
        instance_data_by_id = {}
        for instance, _changes in update_list:
            # Persist the data
            instance_id = instance.get("instance_id")
            instance_data = instance.data_to_store()
            instance_data["active"] = instance.get(
                "active", self.active_on_create
            )
            instance_data_by_id[instance_id] = instance_data
        set_instances(instance_data_by_id, update=True)

    # Helper methods (this might get moved into Creator class)
    def create_instance_in_context(self, product_name, data):
        instance = CreatedInstance(
            product_base_type=self.product_base_type,
            product_type=self.product_type,
            product_name=product_name,
            data=data,
            creator=self
        )
        self.create_context.creator_adds_instance(instance)
        return instance

    def create_instance_in_context_from_existing(self, data):
        instance = CreatedInstance.from_existing(data, self)
        self.create_context.creator_adds_instance(instance)
        return instance
