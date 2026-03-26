#!/usr/bin/env python
"""
Unit tests for the Template class.
"""
import pytest
from wikt.wiki.template import Template, TemplateError, MAX_UNAMED


def test_repr():
    """Test __repr__ method."""
    template = Template(title="Template1", unnamed=["arg1"], named={"B": "arg2"})
    assert repr(template) == r"{{ Template1 | ['arg1'] || {'B': 'arg2'} }}"


def test_max_params():
    """Test max_params method."""
    pars_list = []
    for par in range(1, MAX_UNAMED + 2):
        pars_list.append(f"{par} = val{par}")
    temp_str = r"{{ Template | " + " | ".join(pars_list) + r" }}"
    with pytest.raises(TemplateError):
        Template.from_string(temp_str)


@pytest.mark.parametrize(
    "template_str, expected_title, expected_named, expected_unnamed",
    [
        (r"{{ Template1 | arg1 | arg2 }}", "Template1", {}, ["arg1", "arg2"]),
        (r"{{ Template1 | A=arg1 | B = arg2 }}", "Template1", {"A": "arg1", "B": "arg2"}, []),
        (r"{{ Template1 | A=arg1 | B= }}", "Template1", {"A": "arg1"}, []),
        (r"{{ Template1 | }}", "Template1", {}, []),
    ],
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
        (r"{{}}"),
        (r"{{ | arg1 | B = arg2 }}"),
    ],
)
def test_from_string_failures(template_str):
    """Test the from_string method of the Template class with invalid inputs."""
    with pytest.raises(TemplateError):
        t = Template.from_string(template_str)
        print(t)


@pytest.mark.parametrize(
    "line_str, expected_titles",
    [
        (r"{{ Template1 | 1=arg1 | 2=arg2 }} {{Template2}}", ["Template1", "Template2"]),
        (r"", []),
    ],
)
def test_list_templates(line_str, expected_titles):
    """Test the list_templates method of the Template class."""
    templates = Template.list_templates(line_str)
    titles = [t.title for t in templates]
    assert titles == expected_titles
