"""The small RDML fixtures are what the loader tests will assume they are."""

import zipfile

from lxml import etree

RDML_NS = "{http://www.rdml.org}"


def test_smoke_rdml_is_a_zipped_rdml_document(smoke_rdml):
    with zipfile.ZipFile(smoke_rdml) as archive:
        assert archive.namelist() == ["rdml_data.xml"]
        root = etree.fromstring(archive.read("rdml_data.xml"))
    assert root.tag == f"{RDML_NS}rdml"
    assert root.findall(f"{RDML_NS}experiment")


def test_xxe_fixture_declares_an_external_entity(fixtures_dir):
    text = (fixtures_dir / "xxe.rdml").read_text()
    assert '<!ENTITY xxe SYSTEM "canary.txt">' in text


def test_xxe_fixture_is_inert_under_a_hardened_parser(fixtures_dir):
    parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False)
    root = etree.parse(str(fixtures_dir / "xxe.rdml"), parser).getroot()
    publisher = root.find(f"{RDML_NS}id/{RDML_NS}publisher")
    assert publisher is not None
    assert "canary" not in etree.tostring(publisher, encoding="unicode")
