from collections import defaultdict
from xml.etree.ElementTree import Element, ElementTree

NAMESPACE = "http://tempuri.org/CVRDesign.xsd"


def find_text_xml(xml: ElementTree | Element | None, tag: str):
    if xml is None:
        return None
    result = find_xml(xml, tag)
    return None if (result is None or result.text == "") else result.text


def find_xml(xml: ElementTree | Element, tag: str):
    return xml.find(f"{{{NAMESPACE}}}{tag}")


def findall_xml(xml: ElementTree | Element, tag: str):
    return xml.findall(f"{{{NAMESPACE}}}{tag}")


def parse_contest_results(cvr_xml: ElementTree):
    # { contest_name: voted_for_choices }
    results = defaultdict(set)
    contests = findall_xml(find_xml(cvr_xml, "Contests"), "Contest")
    for contest in contests:
        contest_name = find_xml(contest, "Name").text
        # From what we've seen so far with Hart CVRs, the only choices
        # listed are the ones with votes (i.e. with "Value" = 1), so if we
        # see a choice, we can count it as a vote.
        choices = findall_xml(find_xml(contest, "Options"), "Option")
        for choice in choices:
            if find_xml(choice, "WriteInData"):
                choice_name = "Write-In"
            else:
                choice_name = find_xml(choice, "Name").text
            results[contest_name].add(choice_name)

    return results
