import pytest
import argparse
from io import StringIO
from envoy.cli_compare import build_parser, run_compare


@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path


def make_args(local=".env", against="other.env", remote=False, no_mask=False):
    return argparse.Namespace(
        local=local,
        against=against,
        remote=remote,
        no_mask=no_mask,
    )


def test_compare_identical_files(temp_dir):
    env_a = temp_dir / ".env"
    env_b = temp_dir / "other.env"
    env_a.write_text("APP_NAME=envoy\nDEBUG=true\n")
    env_b.write_text("APP_NAME=envoy\nDEBUG=true\n")

    out, err = StringIO(), StringIO()
    args = make_args(local=str(env_a), against=str(env_b))
    result = run_compare(args, stdout=out, stderr=err)

    assert result == 0
    assert err.getvalue() == ""
    output = out.getvalue()
    assert "Comparing" in output


def test_compare_shows_diff(temp_dir):
    env_a = temp_dir / ".env"
    env_b = temp_dir / "other.env"
    env_a.write_text("APP_NAME=envoy\nONLY_IN_A=yes\n")
    env_b.write_text("APP_NAME=envoy\nONLY_IN_B=yes\n")

    out, err = StringIO(), StringIO()
    args = make_args(local=str(env_a), against=str(env_b))
    result = run_compare(args, stdout=out, stderr=err)

    assert result == 0
    output = out.getvalue()
    assert "ONLY_IN_A" in output or "ONLY_IN_B" in output


def test_compare_missing_local_returns_error(temp_dir):
    env_b = temp_dir / "other.env"
    env_b.write_text("KEY=value\n")

    out, err = StringIO(), StringIO()
    args = make_args(local=str(temp_dir / "missing.env"), against=str(env_b))
    result = run_compare(args, stdout=out, stderr=err)

    assert result == 1
    assert "Error loading local file" in err.getvalue()


def test_compare_missing_against_returns_error(temp_dir):
    env_a = temp_dir / ".env"
    env_a.write_text("KEY=value\n")

    out, err = StringIO(), StringIO()
    args = make_args(local=str(env_a), against=str(temp_dir / "missing.env"))
    result = run_compare(args, stdout=out, stderr=err)

    assert result == 1
    assert "Error loading comparison file" in err.getvalue()


def test_compare_masks_sensitive_values_by_default(temp_dir):
    env_a = temp_dir / ".env"
    env_b = temp_dir / "other.env"
    env_a.write_text("SECRET_KEY=supersecret\n")
    env_b.write_text("SECRET_KEY=othersecret\n")

    out, err = StringIO(), StringIO()
    args = make_args(local=str(env_a), against=str(env_b), no_mask=False)
    run_compare(args, stdout=out, stderr=err)

    output = out.getvalue()
    assert "supersecret" not in output
    assert "othersecret" not in output


def test_compare_no_mask_reveals_values(temp_dir):
    env_a = temp_dir / ".env"
    env_b = temp_dir / "other.env"
    env_a.write_text("SECRET_KEY=supersecret\n")
    env_b.write_text("SECRET_KEY=othersecret\n")

    out, err = StringIO(), StringIO()
    args = make_args(local=str(env_a), against=str(env_b), no_mask=True)
    run_compare(args, stdout=out, stderr=err)

    output = out.getvalue()
    assert "supersecret" in output or "othersecret" in output


def test_compare_remote_file(temp_dir):
    env_a = temp_dir / ".env"
    remote_file = temp_dir / "remote.env"
    env_a.write_text("APP=local\n")
    remote_file.write_text("APP=remote\n")

    out, err = StringIO(), StringIO()
    args = make_args(local=str(env_a), against=str(remote_file), remote=True, no_mask=True)
    result = run_compare(args, stdout=out, stderr=err)

    assert result == 0
    output = out.getvalue()
    assert "APP" in output


def test_build_parser_returns_parser():
    parser = build_parser()
    assert parser is not None
    args = parser.parse_args(["--against", "other.env"])
    assert args.against == "other.env"
    assert args.local == ".env"
    assert args.remote is False
    assert args.no_mask is False
