#!/usr/bin/env python
"""
Unit tests for the Template class.
"""
import pytest
from wikt.wiki.template import Template, TemplateError


@pytest.mark.parametrize(
    "template_str, expected_title, expected_named, expected_unnamed",
    [
        ("{{ Template1 | arg1 | arg2 }}", "Template1", {}, ['arg1', 'arg2']),
        ("{{ Template1 | A=arg1 | B = arg2 }}", "Template1", {"A": "arg1", "B": "arg2"}, []),
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


def test_list_templates():
    """Test the list_templates method of the Template class."""
    line_str = "{{ Template1 | 1=arg1 | 2=arg2 }} {{ Template2 | 3=arg3 }}"
    templates = Template.list_templates(line_str)
    assert len(templates) == 2
    assert templates[0].title == "Template1"
    assert templates[1].title == "Template2"


def test_list_templates_empty():
    """Test the list_templates method of the Template class with an empty string."""
    line_str = ""
    templates = Template.list_templates(line_str)
    assert len(templates) == 0
