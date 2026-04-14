"""Tests for envoy.obfuscator."""

import pytest
from envoy.obfuscator import (
    partial_reveal,
    scramble_value,
    obfuscate_env,
    get_obfuscated_keys,
    ObfuscatorError,
)


def test_partial_reveal_default():
    assert partial_reveal("supersecret") == "supe*******"


def test_partial_reveal_custom_reveal():
    assert partial_reveal("abcdefgh", reveal=2) == "ab******"


def test_partial_reveal_zero_reveal():
    assert partial_reveal("hello", reveal=0) == "*****"


def test_partial_reveal_longer_than_value():
    assert partial_reveal("hi", reveal=10) == "hi"


def test_partial_reveal_empty_value():
    assert partial_reveal("", reveal=4) == ""


def test_partial_reveal_negative_reveal_raises():
    with pytest.raises(ObfuscatorError):
        partial_reveal("value", reveal=-1)


def test_partial_reveal_custom_mask_char():
    assert partial_reveal("secret", reveal=2, mask_char="#") == "se####"


def test_scramble_value_replaces_all():
    assert scramble_value("hello") == "*****"


def test_scramble_value_preserves_length():
    val = "mysecret123"
    assert len(scramble_value(val)) == len(val)


def test_scramble_value_custom_char():
    assert scramble_value("abc", mask_char="-") == "---"


def test_obfuscate_env_all_keys_by_default():
    env = {"A": "hello", "B": "world"}
    result = obfuscate_env(env, reveal=2)
    assert result["A"] == "he***"
    assert result["B"] == "wo***"


def test_obfuscate_env_specific_keys():
    env = {"SECRET": "abc123", "NAME": "alice"}
    result = obfuscate_env(env, keys=["SECRET"], reveal=2)
    assert result["SECRET"] == "ab****"
    assert result["NAME"] == "alice"


def test_obfuscate_env_does_not_mutate_original():
    env = {"KEY": "plaintext"}
    obfuscate_env(env, reveal=3)
    assert env["KEY"] == "plaintext"


def test_obfuscate_env_scramble_mode():
    env = {"TOKEN": "abc123"}
    result = obfuscate_env(env, scramble=True)
    assert result["TOKEN"] == "******"


def test_obfuscate_env_skips_missing_keys():
    env = {"A": "value"}
    result = obfuscate_env(env, keys=["A", "MISSING"], reveal=2)
    assert "MISSING" not in result
    assert result["A"] == "va***"


def test_get_obfuscated_keys_returns_changed():
    original = {"A": "hello", "B": "world"}
    obfuscated = {"A": "he***", "B": "world"}
    changed = get_obfuscated_keys(original, obfuscated)
    assert changed == ["A"]


def test_get_obfuscated_keys_empty_when_no_change():
    env = {"A": "same"}
    assert get_obfuscated_keys(env, dict(env)) == []
