import subprocess

from PIL.ImageShow import XDGViewer


class SilentViewer(XDGViewer):
    def show_file(self, path, **options):
        """
        Display given file.
        """
        subprocess.call(["xdg-open", path], stderr=subprocess.DEVNULL)
        return 1
