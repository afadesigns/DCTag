import pathlib
import shutil
import tempfile


data_path = pathlib.Path(__file__).parent / "data"


def get_clean_data_path():
    """Return .rtdc file in a temp dir for modification"""
    tdir = tempfile.mkdtemp(prefix="dctag_data_")
    orig = data_path / "blood_rbc_leukocytes.rtdc"
    new = pathlib.Path(tdir) / orig.name
    shutil.copy2(orig, new)
    return new
