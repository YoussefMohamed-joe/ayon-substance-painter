"""Remap paths before they are handed over to Substance Painter.

Substance Painter cannot resolve the studio's UNC shares - it never sees the
``\\\\192.168.8.210\\...`` hosts - so every path that leaves AYON and enters
the Substance Painter Python API has to be expressed with the mapped drive
letter the workstation already has.

The mapping is hardcoded here on purpose: it is machine-level studio truth, it
needs no server settings and therefore no addon upload to take effect. To add
or change a share, edit `PATH_MAPPING` below.

This module deliberately avoids importing ``substance_painter`` so it stays
importable (and testable) outside of the host.
"""

from ayon_core.lib import Logger

log = Logger.get_logger(__name__)

_SEPARATORS = "\\/"

#: Source path root -> root to use inside Substance Painter.
#: Mirrors the workstation's mapped network drives (`net use`).
PATH_MAPPING = [
    (r"\\192.168.8.210\VFX-Projects", "X:"),
    (r"\\192.168.8.210\Render", "R:"),
    (r"\\192.168.8.226\FX-sim", "F:"),
]


def _comparable(path):
    """Return path in a form usable for case-insensitive prefix matching.

    Only used for *comparison*, never for the value that is returned to the
    caller.
    """
    return path.replace("/", "\\").rstrip(_SEPARATORS).lower()


def remap_path(path, mappings=None):
    """Return `path` with any known source root swapped for its mapping.

    Matching is case-insensitive and only on whole path components, so
    ``\\\\host\\Render`` never matches ``\\\\host\\Render_old``. The first
    matching entry wins and the path is returned unchanged when nothing
    matches - so this is safe to call on any path.

    Args:
        path (str): The path to remap.
        mappings (Optional[list[tuple[str, str]]]): Override the mapping,
            mostly useful for testing.

    Returns:
        str: The remapped path, using forward slashes when remapped.
    """
    if not path:
        return path

    if mappings is None:
        mappings = PATH_MAPPING

    path_cmp = _comparable(path)
    for source, destination in mappings:
        source_cmp = _comparable(source)
        if path_cmp != source_cmp and not path_cmp.startswith(
            source_cmp + "\\"
        ):
            continue

        # Keep the remainder exactly as it was, only replace the root.
        remainder = path[len(source.rstrip(_SEPARATORS)):]
        remainder = remainder.replace("\\", "/").lstrip("/")
        remapped = destination.rstrip(_SEPARATORS).replace("\\", "/")
        if remainder:
            remapped = f"{remapped}/{remainder}"

        log.debug(f"Remapped path for Substance Painter:"
                  f" '{path}' -> '{remapped}'")
        return remapped

    return path
