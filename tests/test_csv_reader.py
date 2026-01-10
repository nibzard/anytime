"""Tests for CSV reader with schema validation."""

import tempfile
from pathlib import Path

import pytest

from anytime.io.csv_reader import (
    CSVReader,
    CSVSchema,
    read_one_sample_csv,
    read_ab_test_csv,
)


def test_csv_reader_valid_data():
    """CSV reader should successfully read valid data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("value\n")
        f.write("0.5\n")
        f.write("0.6\n")
        f.write("0.4\n")
        f.flush()
        path = f.name

    try:
        reader = read_one_sample_csv(path)
        values = []

        for row, row_num in reader.rows():
            val = reader.read_numeric(row, "value")
            if val is not None:
                values.append(val)

        assert len(values) == 3
        assert values == [0.5, 0.6, 0.4]

        summary = reader.get_summary()
        assert summary["row_count"] == 3
        assert summary["missing_values"] == 0
        assert summary["invalid_values"] == 0
    finally:
        Path(path).unlink()


def test_csv_reader_missing_column():
    """CSV reader should raise error when required column is missing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("wrong_column\n")
        f.write("0.5\n")
        f.flush()
        path = f.name

    try:
        reader = read_one_sample_csv(path)
        with pytest.raises(Exception) as exc_info:
            for _ in reader.rows():
                pass
        assert "missing required columns" in str(exc_info.value).lower()
    finally:
        Path(path).unlink()


def test_csv_reader_handles_missing_values():
    """CSV reader should handle empty/missing numeric values."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("value\n")
        f.write("0.5\n")
        f.write('""')  # Empty quoted string (will be read as empty string, not skipped)
        f.write("\n")   # End the line
        f.write("0.4\n")
        f.flush()
        path = f.name

    try:
        reader = read_one_sample_csv(path)
        values = []

        for row, row_num in reader.rows():
            val = reader.read_numeric(row, "value")
            if val is not None:
                values.append(val)

        assert len(values) == 2
        assert values == [0.5, 0.4]

        summary = reader.get_summary()
        assert summary["missing_values"] == 1
    finally:
        Path(path).unlink()


def test_csv_reader_handles_invalid_values():
    """CSV reader should handle non-numeric values."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("value\n")
        f.write("0.5\n")
        f.write("not_a_number\n")
        f.write("0.4\n")
        f.flush()
        path = f.name

    try:
        reader = read_one_sample_csv(path)
        values = []

        for row, row_num in reader.rows():
            val = reader.read_numeric(row, "value")
            if val is not None:
                values.append(val)

        assert len(values) == 2
        assert values == [0.5, 0.4]

        summary = reader.get_summary()
        assert summary["invalid_values"] == 1
    finally:
        Path(path).unlink()


def test_csv_reader_ab_test_schema():
    """AB test schema should validate arm and value columns."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("arm,value\n")
        f.write("A,0.5\n")
        f.write("B,0.6\n")
        f.flush()
        path = f.name

    try:
        reader = read_ab_test_csv(path)
        rows = list(reader.rows())

        assert len(rows) == 2
        assert rows[0][0]["arm"] == "A"
        assert rows[0][0]["value"] == "0.5"
        assert rows[1][0]["arm"] == "B"
        assert rows[1][0]["value"] == "0.6"
    finally:
        Path(path).unlink()


def test_csv_schema_validation():
    """CSV schema should validate column definitions."""
    # Valid schema
    schema = CSVSchema(
        required_columns={"value"},
        numeric_columns={"value"},
    )
    assert schema.required_columns == {"value"}

    # Invalid schema - required column not in numeric/optional
    with pytest.raises(ValueError, match="not in numeric/optional"):
        CSVSchema(
            required_columns={"value", "missing_col"},
            numeric_columns={"value"},
        )


def test_csv_reader_custom_column():
    """CSV reader should support custom column names."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("metric\n")
        f.write("0.5\n")
        f.flush()
        path = f.name

    try:
        reader = read_one_sample_csv(path, value_column="metric")
        values = []

        for row, row_num in reader.rows():
            val = reader.read_numeric(row, "metric")
            if val is not None:
                values.append(val)

        assert values == [0.5]
    finally:
        Path(path).unlink()
