import os
import copy

import pyblish.api
import ayon_api

import substance_painter.textureset
from ayon_core.pipeline import tempdir
from ayon_substancepainter.api.lib import (
    get_parsed_export_maps,
    get_filtered_export_preset,
    strip_template
)
from ayon_core.pipeline.create import get_product_name


class CollectTextureSet(pyblish.api.InstancePlugin):
    """Extract Textures using an output template config"""
    # TODO: Production-test usage of color spaces
    # TODO: Detect what source data channels end up in each file

    label = "Collect Texture Set images"
    hosts = ["substancepainter"]
    families = ["textureSet"]
    order = pyblish.api.CollectorOrder + 0.01

    def process(self, instance):

        config = self.get_export_config(instance)
        project_name = instance.context.data["projectName"]
        folder_entity = ayon_api.get_folder_by_path(
            project_name,
            instance.data["folderPath"]
        )
        instance.data["folderEntity"] = folder_entity
        task_name = instance.data.get("task")
        task_entity = None
        if folder_entity and task_name:
            task_entity = ayon_api.get_task_by_name(
                project_name, folder_entity["id"], task_name
            )
            instance.data["taskEntity"] = task_entity

        instance.data["exportConfig"] = config
        strip_texture_set = instance.data["creator_attributes"].get(
            "flattenTextureSets", False)
        maps = get_parsed_export_maps(config, strip_texture_set)
        # Let's break the instance into multiple instances to integrate
        # a product per generated texture or texture UDIM sequence
        for (texture_set_name, stack_name), template_maps in maps.items():
            self.log.info(f"Processing {texture_set_name}/{stack_name}")
            for (template, tilename), outputs in template_maps.items():
                self.log.info(
                    f"Processing {template} with tile name {tilename}"
                )
                self.create_image_instance(
                    instance,
                    template,
                    outputs,
                    folder_entity=folder_entity,
                    task_entity=task_entity,
                    texture_set_name=texture_set_name,
                    stack_name=stack_name,
                    uv_tile_name=tilename,
                    strip_texture_set=strip_texture_set
                )

    def create_image_instance(
        self,
        instance,
        template,
        outputs,
        folder_entity,
        task_entity,
        texture_set_name,
        stack_name,
        uv_tile_name="",
        strip_texture_set=False
    ):
        """Create a new instance per image or UDIM sequence.

        The new instances will be of product type `image`.

        """

        context = instance.context
        first_filepath = outputs[0]["filepath"]
        fnames = [os.path.basename(output["filepath"]) for output in outputs]
        ext = os.path.splitext(first_filepath)[1]
        assert ext.lstrip("."), f"No extension: {ext}"

        # all_texture_sets = substance_painter.textureset.all_texture_sets()
        # Define the suffix we want to give this particular texture
        # set and set up a remapped product naming for it.
        suffix = ""
        if not strip_texture_set:
            texture_set = substance_painter.textureset.TextureSet.from_name(
                texture_set_name
            )
            # More than one texture set, include texture set name
            suffix += f".{texture_set_name}"
            if texture_set.is_layered_material() and stack_name:
                # More than one stack, include stack name
                suffix += f".{stack_name}"

        if uv_tile_name:
            suffix += f".{uv_tile_name}"

        # Always include the map identifier
        map_identifier = strip_template(template)
        suffix += f".{map_identifier}"

        # Keep product type from instance if was customized
        product_type = instance.data["productType"]
        if product_type == instance.data["productBaseType"]:
            product_type = None

        # TODO: The product type actually isn't 'texture' currently but
        #   for now this is only done so the product name starts with
        #   'texture'
        product_base_type = "texture"
        image_kwargs = dict(
            project_name=context.data["projectName"],
            folder_entity=folder_entity,
            task_entity=task_entity,
            product_base_type=product_base_type,
            product_type=product_type or product_base_type,
            host_name=context.data["hostName"],
            project_settings=context.data["project_settings"],
        )
        image_product_name = get_product_name(
            variant=instance.data["variant"] + suffix,
            **image_kwargs
        )
        image_product_group_name = get_product_name(
            variant=instance.data["variant"],
            **image_kwargs
        )

        # Prepare representation
        representation = {
            "name": ext.lstrip("."),
            "ext": ext.lstrip("."),
            "files": fnames if len(fnames) > 1 else fnames[0],
        }

        # Mark as UDIM explicitly if it has UDIM tiles.
        if bool(outputs[0].get("udim")):
            # The representation for a UDIM sequence should have a `udim` key
            # that is a list of all udim tiles (str) like: ["1001", "1002"]
            # strings. See CollectTextures plug-in and Integrators.
            representation["udim"] = [output["udim"] for output in outputs]

        # Set up the representation for thumbnail generation
        # TODO: Simplify this once thumbnail extraction is refactored
        staging_dir = os.path.dirname(first_filepath)
        representation["tags"] = ["review"]
        representation["stagingDir"] = staging_dir
        # Clone the instance
        product_base_type = "image"
        image_instance = context.create_instance(image_product_name)
        image_instance[:] = instance[:]
        image_instance.data.update(copy.deepcopy(dict(instance.data)))
        image_instance.data["name"] = image_product_name
        image_instance.data["label"] = image_product_name
        image_instance.data["productName"] = image_product_name
        image_instance.data["productType"] = product_type or product_base_type
        image_instance.data["productBaseType"] = product_base_type
        image_instance.data["family"] = product_base_type
        image_instance.data["families"] = [product_base_type, "textures"]
        if instance.data["creator_attributes"].get("review"):
            image_instance.data["families"].append("review")

            entity: dict = instance.data.get("taskEntity")
            if not entity:
                entity = instance.data["folderEntity"]

            fps: float = entity["attrib"]["fps"]
            image_instance.data["fps"] = fps
            if bool(outputs[0].get("udim")):
                udim = sorted(int(output["udim"]) for output in outputs)
                image_instance.data["frameStart"] = udim[0]
                image_instance.data["frameEnd"] = udim[-1]
            else:
                # Use start of UDIM range as fallback frame for single images
                image_instance.data["frameStart"] = 1001
                image_instance.data["frameEnd"] = 1001

        image_instance.data["representations"] = [representation]

        # Group the textures together in the loader
        image_instance.data["productGroup"] = image_product_group_name

        # Store the texture set name and stack name on the instance
        image_instance.data["textureSetName"] = texture_set_name
        image_instance.data["textureStackName"] = stack_name

        # Store color space with the instance
        # Note: The extractor will assign it to the representation
        colorspace = outputs[0].get("colorSpace")
        if colorspace:
            self.log.debug(f"{image_product_name} colorspace: {colorspace}")
            image_instance.data["colorspace"] = colorspace

        # Store the instance in the original instance as a member
        instance.append(image_instance)

    def get_export_config(self, instance):
        """Return an export configuration dict for texture exports.

        This config can be supplied to:
            - `substance_painter.export.export_project_textures`
            - `substance_painter.export.list_project_textures`

        See documentation on substance_painter.export module about the
        formatting of the configuration dictionary.

        Args:
            instance (pyblish.api.Instance): Texture Set instance to be
                published.

        Returns:
            dict: Export config

        """

        creator_attrs = instance.data["creator_attributes"]
        preset_url = creator_attrs["exportPresetUrl"]

        is_single_output = creator_attrs.get(
            "flattenTextureSets", False)

        # Temporary directory purely for 'collecting' the expected output files
        # which is replaced in the export config by the
        # `CollectTextureSetStagingDir` plug-in below at a later collector
        # order that has correctly defined anatomy data for the instance's
        # custom staging dir.
        temp_dir = tempdir.get_temp_dir(
            instance.context.data["projectName"],
            use_local_temp=True)

        # See: https://substance3d.adobe.com/documentation/ptpy/api/substance_painter/export  # noqa
        config = {  # noqa
            "exportShaderParams": True,
            "exportPath": temp_dir,
            "defaultExportPreset": preset_url,

            # Custom overrides to the exporter
            "exportParameters": [
                {
                    "parameters": {
                        "fileFormat": creator_attrs["exportFileFormat"],
                        "sizeLog2": creator_attrs["exportSize"],
                        "paddingAlgorithm": creator_attrs["exportPadding"],
                        "dilationDistance": creator_attrs["exportDilationDistance"]  # noqa
                    }
                }
            ]
        }
        # Create the list of Texture Sets to export.
        export_texture_sets = creator_attrs.get("exportTextureSets", [])
        if not export_texture_sets:
            # Export all texture sets
            export_texture_sets = [
                texture_set.name() for texture_set in
                substance_painter.textureset.all_texture_sets()
            ]

        config["exportList"] = [
            {"rootPath": texture_set_name}
            for texture_set_name in export_texture_sets
        ]

        for override in config["exportParameters"]:
            parameters = override.get("parameters")
            for key, value in dict(parameters).items():
                if value is None:
                    parameters.pop(key)

        channel_layer = creator_attrs.get("exportChannel", [])
        maps = get_filtered_export_preset(
            preset_url, channel_layer, is_single_output
        )
        config.update(maps)
        return config


class CollectTextureSetStagingDir(pyblish.api.InstancePlugin):
    """Set the staging directory for the `textureSet` instance taking into
    account custom staging dirs. Propagate this custom staging dir to the
    individual texture image instances that are created from the textureSet"""

    label = "Texture Set Staging Dir"
    hosts = ["substancepainter"]
    families = ["textureSet"]

    # Run after CollectManagedStagingDir
    order = pyblish.api.CollectorOrder + 0.4991

    def process(self, instance):

        staging_dir = instance.data["stagingDir"]

        # Update export config
        config = instance.data["exportConfig"]
        config["exportPath"] = staging_dir

        # Update image instances and their representations
        for image_instance in instance:

            # Include the updated config
            image_instance.data["exportConfig"] = copy.deepcopy(config)
            image_instance.data["stagingDir"] = staging_dir

            # Update representation staging dir.
            for repre in image_instance.data["representations"]:
                repre["stagingDir"] = staging_dir


class CollectCustomExportPresetUrl(pyblish.api.InstancePlugin):
    """Collect Export Preset Url when single texture output enabled."""

    label = "Collect Export Preset for Single Texture Output"
    hosts = ["substancepainter"]
    families = ["textureSet"]

    # Run after CollectManagedStagingDir
    order = pyblish.api.CollectorOrder + 0.4992

    def process(self, instance):
        # Update export config
        if not instance.data["creator_attributes"].get(
            "flattenTextureSets", False):
            return

        config = instance.data["exportConfig"]
        export_config = copy.deepcopy(config)
        custom_export_preset = "Ayon_Custom_Preset"
        for export_preset in export_config["exportPresets"]:
            export_preset["name"] = custom_export_preset

        export_config["defaultExportPreset"] = custom_export_preset
        instance.data["exportConfig"] = export_config
        # Update image instances and their representations
        for image_instance in instance:

            # Include the updated config
            image_instance.data["exportConfig"] = export_config
