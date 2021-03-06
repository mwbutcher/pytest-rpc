# -*- coding: utf-8 -*-

"""Test cases for the 'get_xsd' utility function for retrieving the XSD for the project."""

# ======================================================================================================================
# Imports
# ======================================================================================================================
from __future__ import absolute_import
from lxml import etree
from pytest_rpc import MK8S_ENV_VARS, ASC_ENV_VARS, get_xsd
from tests.conftest import run_and_parse
from tests.conftest import run_and_parse_with_config

# ======================================================================================================================
# Globals
# ======================================================================================================================
TEST_ENV_VARS = list(ASC_ENV_VARS)      # Shallow copy.
MK8S_TEST_ENV_VARS = list(MK8S_ENV_VARS)      # Shallow copy.


# ======================================================================================================================
# Tests
# ======================================================================================================================
def test_happy_path_asc(testdir, properly_decorated_test_function):
    """Verify that 'get_xsd' returns an XSD stream that can be used to validate JUnitXML."""

    # Setup
    testdir.makepyfile(properly_decorated_test_function.format(test_name='test_happy_path',
                                                               test_id='123e4567-e89b-12d3-a456-426655440000',
                                                               jira_id='ASC-123'))

    xml_doc = run_and_parse(testdir).xml_doc
    xmlschema = etree.XMLSchema(etree.parse(get_xsd()))

    # Test
    xmlschema.assertValid(xml_doc)


def test_happy_path_mk8s(testdir, properly_decorated_test_function):
    """Verify that 'get_xsd' returns an XSD stream that can be used to validate JUnitXML when configured with mk8s."""

    # Setup
    testdir.makepyfile(properly_decorated_test_function.format(test_name='test_happy_path',
                                                               test_id='123e4567-e89b-12d3-a456-426655440000',
                                                               jira_id='ASC-123'))
    config = \
"""
[pytest]
ci-environment=mk8s
"""  # noqa

    xml_doc = run_and_parse_with_config(testdir, config).xml_doc
    xmlschema = etree.XMLSchema(etree.parse(get_xsd('mk8s')))

    # Test
    xmlschema.assertValid(xml_doc)


def test_multiple_jira_references(testdir):
    """Verify that 'get_xsd' returns an XSD stream when a testcase is decorated Jira mark with multiple
    arguments.
    """

    # Setup
    testdir.makepyfile("""
                import pytest
                @pytest.mark.jira('ASC-123', 'ASC-124')
                @pytest.mark.test_id('123e4567-e89b-12d3-a456-426655440000')
                def test_xsd():
                    pass
    """)

    xml_doc = run_and_parse(testdir).xml_doc
    xmlschema = etree.XMLSchema(etree.parse(get_xsd()))

    # Test
    xmlschema.assertValid(xml_doc)


def test_missing_required_marks(testdir, undecorated_test_function):
    """Verify that XSD will enforce the presence of 'test_id' and 'jira_id' properties for test cases."""

    # Setup
    testdir.makepyfile(undecorated_test_function.format(test_name='test_typo_global'))

    xml_doc = run_and_parse(testdir).xml_doc
    xmlschema = etree.XMLSchema(etree.parse(get_xsd()))

    # Test
    assert xmlschema.validate(xml_doc) is False


def test_extra_testcase_property(testdir, properly_decorated_test_function):
    """Verify that XSD will enforce the strict presence of only required test case properties."""

    # Setup
    testdir.makepyfile(properly_decorated_test_function.format(test_name='test_extra_mark',
                                                               test_id='123e4567-e89b-12d3-a456-426655440000',
                                                               jira_id='ASC-123'))

    xml_doc = run_and_parse(testdir).xml_doc

    # Add another property element for the testcase.
    xml_doc.find('./testcase/properties').append(etree.Element('property',
                                                               attrib={'name': 'extra', 'value': 'fail'}))
    xmlschema = etree.XMLSchema(etree.parse(get_xsd()))

    # Test
    assert xmlschema.validate(xml_doc) is False


def test_typo_property(testdir, properly_decorated_test_function):
    """Verify that XSD will enforce the only certain property names are allowed for the testcase."""

    # Setup
    testdir.makepyfile(properly_decorated_test_function.format(test_name='test_typo_mark',
                                                               test_id='123e4567-e89b-12d3-a456-426655440000',
                                                               jira_id='ASC-123'))

    xml_doc = run_and_parse(testdir).xml_doc

    # Add another property element for the testcase.
    xml_doc.find('./testcase/properties/property').attrib['name'] = 'wrong_test_id'
    xmlschema = etree.XMLSchema(etree.parse(get_xsd()))

    # Test
    assert xmlschema.validate(xml_doc) is False
