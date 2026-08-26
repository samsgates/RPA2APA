from pathlib import Path
import zipfile
import pytest
from rpa2apa_api.uploads import extract_project_zip, UnsafeArchive


def test_safe_zip_extract(tmp_path):
    z = tmp_path / "p.zip"
    with zipfile.ZipFile(z, "w") as f:
        f.writestr("project.json", '{"name":"x"}')
        f.writestr("Main.xaml", '<Activity xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"><Sequence /></Activity>')
    out = extract_project_zip(z, tmp_path / "work")
    assert (out / "project.json").exists()


def test_zip_slip_blocked(tmp_path):
    z = tmp_path / "bad.zip"
    with zipfile.ZipFile(z, "w") as f:
        f.writestr("../escape.txt", "bad")
    with pytest.raises(UnsafeArchive):
        extract_project_zip(z, tmp_path / "work")
