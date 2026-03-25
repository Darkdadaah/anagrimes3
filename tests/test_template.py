#!/usr/bin/env python
"""
Unit tests for the Template class.
"""
import pytest
from wikt.wiki.template import Template, TemplateError



def test_repr():
    """Test __repr__ method."""
    template = Template(title="Template1", unnamed=["arg1"], named={"B": "arg2"})
    assert repr(template) == "{{ Template1 | ['arg1'] || {'B': 'arg2'} }}"


@pytest.mark.parametrize(
    "template_str, expected_title, expected_named, expected_unnamed",
    [
        ("{{ Template1 | arg1 | arg2 }}", "Template1", {}, ['arg1', 'arg2']),
        ("{{ Template1 | A=arg1 | B = arg2 }}", "Template1", {"A": "arg1", "B": "arg2"}, []),
        ("{{ Template1 | A=arg1 | B= }}", "Template1", {"A": "arg1"}, []),
        ("{{ Template1 | }}", "Template1", {}, []),
    ]
)
def test_from_string(template_str, expected_title, expected_named, expected_unnamed):
    """Test the from_string method of the Template class."""
    template = Template.from_string(template_str)
    assert template.title == expected_title
    assert template.named == expected_named
    assert template.unnamed == expected_unnamed


@pytest.mark.parametrize(
    "template_str",
    [
        ("{{}}"),
        ("{{ | arg1 | B = arg2 }}"),
    ]
)
def test_from_string_failures(template_str):
    """Test the from_string method of the Template class with invalid inputs."""
    with pytest.raises(TemplateError):
        t = Template.from_string(template_str)
        print(t)


@pytest.mark.parametrize(
    "line_str, expected_titles",
    [
        ("{{ Template1 | 1=arg1 | 2=arg2 }} {{Template2}}", ["Template1", "Template2"]),
        ("", []),
    ]
)
def test_list_templates(line_str, expected_titles):
    """Test the list_templates method of the Template class."""
    templates = Template.list_templates(line_str)
    titles = [t.title for t in templates]
    assert titles == expected_titles


def test_list_templates_empty():
    """Test the list_templates method of the Template class with an empty string."""
    line_str = ""
    templates = Template.list_templates(line_str)
    assert len(templates) == 0
