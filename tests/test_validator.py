"""Tests for envoy.validator module."""

import pytest
from envoy.validator import (
    validate_key,
    validate_env,
    has_errors,
    format_issues,
    ValidationIssue,
)


def test_validate_key_valid():
    assert validate_key('MY_VAR') is True
    assert validate_key('_PRIVATE') is True
    assert validate_key('CamelCase123') is True


def test_validate_key_invalid():
    assert validate_key('1STARTS_WITH_NUM') is False
    assert validate_key('HAS-HYPHEN') is False
    assert validate_key('HAS SPACE') is False
    assert validate_key('') is False


def test_validate_env_no_issues():
    env = {'APP_NAME': 'myapp', 'PORT': '8080'}
    issues = validate_env(env)
    assert issues == []


def test_validate_env_invalid_key():
    env = {'bad-key': 'value'}
    issues = validate_env(env)
    assert len(issues) == 1
    assert issues[0].severity == 'error'
    assert 'bad-key' in issues[0].message


def test_validate_env_empty_value_warning():
    env = {'EMPTY_VAR': ''}
    issues = validate_env(env)
    assert len(issues) == 1
    assert issues[0].severity == 'warning'
    assert 'EMPTY_VAR' in issues[0].message


def test_validate_env_missing_required_key():
    env = {'APP_NAME': 'myapp'}
    issues = validate_env(env, required_keys=['APP_NAME', 'SECRET_KEY'])
    assert len(issues) == 1
    assert issues[0].severity == 'error'
    assert 'SECRET_KEY' in issues[0].message


def test_validate_env_multiple_issues():
    env = {'bad-key': '', 'GOOD_KEY': 'val'}
    issues = validate_env(env, required_keys=['MISSING'])
    severities = {i.severity for i in issues}
    assert 'error' in severities
    assert 'warning' in severities
    assert len(issues) == 3  # invalid key error + empty value warning + missing key error


def test_has_errors_true():
    issues = [ValidationIssue(key='X', message='bad', severity='error')]
    assert has_errors(issues) is True


def test_has_errors_false_with_warnings():
    issues = [ValidationIssue(key='X', message='empty', severity='warning')]
    assert has_errors(issues) is False


def test_has_errors_empty():
    assert has_errors([]) is False


def test_format_issues_no_issues():
    assert format_issues([]) == 'No issues found.'


def test_format_issues_mixed():
    issues = [
        ValidationIssue(key='A', message='Something wrong', severity='error'),
        ValidationIssue(key='B', message='Empty value', severity='warning'),
    ]
    output = format_issues(issues)
    assert '[ERROR]' in output
    assert '[WARN]' in output
    assert 'Something wrong' in output
    assert 'Empty value' in output
