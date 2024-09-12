import copy
import os

from ayon_core.pipeline import KnownPublishError, publish
from ayon_core.lib import (
    ToolNotFoundError,
    get_oiio_tool_args,
    run_subprocess,
)
from ayon_core.pipeline.colorspace import (
    get_ocio_config_colorspaces
)


def convert_to_tx(
    source,
    ocio_config_path=None,
    colorspace=None,
    target_colorspace=None,
    staging_dir=None,
    log=None
):
    """Process the texture.

    This function requires the `maketx` executable to be available in an
    OpenImageIO toolset detectable by AYON.

    Args:
        source (str): Path to source file.
        ocio_config_path (str): Path to the OCIO config file.
        colorspace (str): Colorspace of the source file.
        target_colorspace (str): Target colorspace
        staging_dir (str): Output directory to write to.
        log (logging.Logger): Python logger.

    Returns:
        str: The resulting texture path.

    """

    try:
        maketx_args = get_oiio_tool_args("maketx")
    except ToolNotFoundError:
        raise KnownPublishError(
            "OpenImageIO is not available on the machine")

    # Define .tx filepath in staging if source file is not .tx
    fname, ext = os.path.splitext(os.path.basename(source))
    if ext == ".tx":
        return source

    # Hardcoded default arguments for maketx conversion based on Arnold's
    # txManager in Maya
    args = [
        # unpremultiply before conversion (recommended when alpha present)
        "--unpremult",
        # use oiio-optimized settings for tile-size, planarconfig, metadata
        "--oiio",
        "--filter", "lanczos3",
    ]

    if ocio_config_path:
        args.extend(["--colorconvert", colorspace, target_colorspace])
        args.extend(["--colorconfig", ocio_config_path])

    subprocess_args = maketx_args + [
        "-v",  # verbose
        "-u",  # update mode
        # --checknan doesn't influence the output file but aborts the
        # conversion if it finds any. So we can avoid it for the file hash
        "--checknan",
        source
    ]

    subprocess_args.extend(args)
    # if self.extra_args:
    #     subprocess_args.extend(self.extra_args)

    destination = os.path.join(staging_dir, fname + ".tx")
    subprocess_args.extend(["-o", destination])

    # We want to make sure we are explicit about what OCIO config gets
    # used. So when we supply no --colorconfig flag that no fallback to
    # an OCIO env var occurs.
    env = os.environ.copy()
    env.pop("OCIO", None)

    log.info(" ".join(subprocess_args))
    try:
        run_subprocess(subprocess_args, env=env)
    except Exception:
        log.error("Texture maketx conversion failed", exc_info=True)
        raise

    return destination


class ExtractMakeTX(publish.Extractor,
                    publish.ColormanagedPyblishPluginMixin):
    """Extract MakeTX

    This requires color management to be enabled so that the MakeTX file
    generation is converted to the correct render colorspace.

    Adds an extra `tx` representation to the instance.

    """

    label = "Extract TX"
    hosts = ["substancepainter"]
    families = ["image"]

    # Run directly after textures export
    order = publish.Extractor.order - 0.099

    def process(self, instance):

        representations: "list[dict]" = instance.data["representations"]

        # If a tx representation is present we skip extraction
        if any(repre["name"] == "tx" for repre in representations):
            return

        for representation in list(representations):
            tx_representation = copy.deepcopy(representation)
            tx_representation["name"] = "tx"
            tx_representation["ext"] = "tx"

            colorspace_data: dict = tx_representation.get("colorspaceData", {})
            if not colorspace_data:
                continue

            colorspace: str = colorspace_data["colorspace"]
            ocio_config_path: str = colorspace_data["config"]["path"]
            target_colorspace = self.get_target_colorspace(ocio_config_path)

            source_files = representation["files"]
            is_sequence = isinstance(source_files, (list, tuple))
            if not is_sequence:
                source_files = [source_files]

            # Generate the TX files
            tx_files = []
            for source_filepath in source_files:
                tx_filepath = convert_to_tx(
                    source_filepath,
                    ocio_config_path=ocio_config_path,
                    colorspace=colorspace,
                    target_colorspace=target_colorspace,
                    staging_dir=instance.data["stagingDir"],
                    log=self.log
                )
                tx_files.append(tx_filepath)

            # Make sure to store again as single file it was also in the
            # original representation
            if not is_sequence:
                tx_files = tx_files[0]

            tx_representation["files"] = tx_files

            representations.append(tx_representation)

            # Only ever one `tx` representation is needed
            break

    def get_target_colorspace(self, ocio_path: str) -> str:
        ocio_colorspaces = get_ocio_config_colorspaces(ocio_path)
        return ocio_colorspaces["roles"]["rendering"]["colorspace"]
