from xml.etree.ElementTree import Element, ElementTree
import pytest
from ...util.hart_parse import (
    find_text_xml,
    find_xml,
    findall_xml,
    parse_contest_results,
)


@pytest.fixture
def namespace():
    return "http://tempuri.org/CVRDesign.xsd"


def test_find_text_xml(namespace):
    root = Element("Root")
    child = Element(f"{{{namespace}}}Tag")
    child.text = "Test"
    root.append(child)
    assert find_text_xml(ElementTree(root), "Tag") == "Test"
    assert find_text_xml(None, "Tag") is None
    assert find_text_xml(ElementTree(root), "NonExistentTag") is None


def test_find_xml(namespace):
    root = Element("Root")
    child = Element(f"{{{namespace}}}Tag")
    root.append(child)
    assert find_xml(ElementTree(root), "Tag") is not None
    assert find_xml(ElementTree(root), "NonExistentTag") is None


def test_findall_xml(namespace):
    root = Element("Root")
    child1 = Element(f"{{{namespace}}}Tag")
    child2 = Element(f"{{{namespace}}}Tag")
    root.extend([child1, child2])
    assert len(findall_xml(ElementTree(root), "Tag")) == 2
    assert len(findall_xml(ElementTree(root), "NonExistentTag")) == 0


def test_parse_contest_results(namespace):
    cvr = Element(f"{{{namespace}}}CVR")
    contests = Element(f"{{{namespace}}}Contests")
    contest = Element(f"{{{namespace}}}Contest")
    contest_name = Element(f"{{{namespace}}}Name")
    contest_name.text = "Contest1"
    options = Element(f"{{{namespace}}}Options")
    option = Element(f"{{{namespace}}}Option")
    option_name = Element(f"{{{namespace}}}Name")
    option_name.text = "Choice1"
    option.append(option_name)
    options.append(option)
    contest.append(contest_name)
    contest.append(options)
    contests.append(contest)
    cvr.append(contests)
    cvr_xml = ElementTree(cvr)

    results = parse_contest_results(cvr_xml)
    assert "Contest1" in results
    assert "Choice1" in results["Contest1"]
