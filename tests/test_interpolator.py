import pytest
from envoy.interpolator import (
    interpolate_env,
    find_references,
    InterpolationError,
)


def test_interpolate_brace_style():
    env = {"BASE": "/app", "DATA": "${BASE}/data"}
    result = interpolate_env(env)
    assert result["DATA"] == "/app/data"


def test_interpolate_bare_style():
    env = {"HOST": "localhost", "URL": "http://$HOST:8080"}
    result = interpolate_env(env)
    assert result["URL"] == "http://localhost:8080"


def test_interpolate_chained_references():
    env = {"A": "hello", "B": "${A}_world", "C": "${B}!"}
    result = interpolate_env(env)
    assert result["C"] == "hello_world!"


def test_interpolate_no_references_unchanged():
    env = {"KEY": "simple_value", "OTHER": "123"}
    result = interpolate_env(env)
    assert result == env


def test_interpolate_undefined_ref_lenient():
    env = {"KEY": "${UNDEFINED}_suffix"}
    result = interpolate_env(env, strict=False)
    assert result["KEY"] == "${UNDEFINED}_suffix"


def test_interpolate_undefined_ref_strict_raises():
    env = {"KEY": "${MISSING}"}
    with pytest.raises(InterpolationError, match="Undefined variable"):
        interpolate_env(env, strict=True)


def test_interpolate_circular_reference_raises():
    env = {"A": "${B}", "B": "${A}"}
    with pytest.raises(InterpolationError, match="Circular reference"):
        interpolate_env(env)


def test_interpolate_does_not_mutate_original():
    env = {"BASE": "/opt", "PATH_VAR": "${BASE}/bin"}
    original = dict(env)
    interpolate_env(env)
    assert env == original


def test_interpolate_with_os_env_fallback():
    env = {"FULL_PATH": "${SYSTEM_ROOT}/app"}
    os_env = {"SYSTEM_ROOT": "/usr/local"}
    result = interpolate_env(env, os_env=os_env)
    assert result["FULL_PATH"] == "/usr/local/app"


def test_interpolate_env_overrides_os_env():
    env = {"VAR": "local", "USE": "${VAR}"}
    os_env = {"VAR": "system"}
    result = interpolate_env(env, os_env=os_env)
    assert result["USE"] == "local"


def test_find_references_brace_style():
    env = {"KEY": "${FOO}_${BAR}"}
    refs = find_references(env)
    assert refs["KEY"] == ["FOO", "BAR"]


def test_find_references_bare_style():
    env = {"KEY": "$HOST:$PORT"}
    refs = find_references(env)
    assert "HOST" in refs["KEY"]
    assert "PORT" in refs["KEY"]


def test_find_references_no_refs_excluded():
    env = {"KEY": "plain_value", "OTHER": "${REF}"}
    refs = find_references(env)
    assert "KEY" not in refs
    assert "OTHER" in refs


def test_find_references_empty_env():
    assert find_references({}) == {}
