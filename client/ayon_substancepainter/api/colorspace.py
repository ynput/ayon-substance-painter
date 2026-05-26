"""Substance Painter OCIO management

Adobe Substance 3D Painter supports OCIO color management using a per project
configuration. Output color spaces are defined at the project level

More information see:
  - https://substance3d.adobe.com/documentation/spdoc/color-management-223053233.html
  - https://substance3d.adobe.com/documentation/spdoc/color-management-with-opencolorio-225969419.html

"""  # noqa E501
import substance_painter.export

from .lib import (
    get_document_structure,
    get_channel_format
)


def _iter_document_stack_channels():
    """Yield all stack paths and channels project"""

    for material in get_document_structure()["materials"]:
        material_name = material["name"]
        for stack in material["stacks"]:
            stack_name = stack["name"]
            if stack_name:
                stack_path = [material_name, stack_name]
            else:
                stack_path = material_name
            for channel in stack["channels"]:
                yield stack_path, channel


def _get_first_color_and_data_stack_and_channel():
    """Return first found color channel and data channel."""
    color_channel = None
    data_channel = None
    for stack_path, channel in _iter_document_stack_channels():
        channel_format = get_channel_format(stack_path, channel)
        if channel_format["color"]:
            color_channel = (stack_path, channel)
        else:
            data_channel = (stack_path, channel)

        if color_channel and data_channel:
            return color_channel, data_channel

    return color_channel, data_channel


def get_project_channel_data():
    """Return colorSpace settings for the current substance painter project.

    In Substance Painter only color channels have Color Management enabled
    whereas data channels have no color management applied. This can't be
    changed. The artist can only customize the export color space for color
    channels per bit-depth for 8 bpc, 16 bpc and 32 bpc.

    As such this returns the color space for 'data' and for per bit-depth
    for color channels.

    Example output:
    {
        "data": {'colorSpace': 'Utility - Raw'},
        "8": {"colorSpace": "ACES - AcesCG"},
        "16": {"colorSpace": "ACES - AcesCG"},
        "16f": {"colorSpace": "ACES - AcesCG"},
        "32f": {"colorSpace": "ACES - AcesCG"}
    }

    """
    config = {
        "exportPath": "/",
        "exportShaderParams": False,
        "defaultExportPreset": "query_preset",

        "exportPresets": [{
            "name": "query_preset",

            # List of maps making up this export preset.
            "maps": [{
                # Generate filename that contains just the colorspace and a
                # placeholder character (for potential empty colorspace values)
                # to get colorspace name from export file list
                "fileName": "_$colorSpace",
                # List of source/destination defining which channels will
                # make up the texture file.
                "channels": [],
                "parameters": {
                    "fileFormat": "exr",
                    "bitDepth": "32f",
                    "dithering": False,
                    "sizeLog2": 4,
                    "paddingAlgorithm": "passthrough",
                    "dilationDistance": 16
                }
            }]
        }],
    }

    def _get_colorspace(config_):
        # Return the basename of the single output path we defined
        result = substance_painter.export.list_project_textures(config_)
        path = next(iter(result.values()))[0]
        return {
            # strip extension, path slashes and also the starting `_`
            # from our filename (to ensure it at least has some filename)
            "colorSpace": path.strip("/\\.exr")[1:],
        }

    # Query for each type of channel (color and data)
    color_channel, data_channel = _get_first_color_and_data_stack_and_channel()
    colorspaces = {}
    for key, channel_data in {
        "data": data_channel,
        "color": color_channel
    }.items():
        if channel_data is None:
            # No channel of that datatype anywhere in the Stack. We're
            # unable to identify the output color space of the project
            colorspaces[key] = None
            continue

        stack, channel = channel_data

        # Stack must be a string
        if not isinstance(stack, str):
            # Assume iterable
            stack = "/".join(stack)

        # Define the temp output config
        config["exportList"] = [{"rootPath": stack}]
        config_map = config["exportPresets"][0]["maps"][0]
        config_map["channels"] = [
            {
                "destChannel": x,
                "srcChannel": x,
                "srcMapType": "documentMap",
                "srcMapName": channel
            } for x in "RGB"
        ]

        if key == "color":
            # Query for each bit depth
            # Color space definition can have a different OCIO config set
            # for 8-bit, 16-bit and 32-bit outputs so we need to check each
            # bit depth
            for depth in ["8", "16", "16f", "32f"]:
                config_map["parameters"]["bitDepth"] = depth  # noqa
                colorspaces[key + depth] = _get_colorspace(config)
        else:
            # Data channel (not color managed)
            colorspaces[key] = _get_colorspace(config)

    return colorspaces
