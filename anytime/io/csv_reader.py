"""CSV reader with schema validation for anytime inference."""

import csv
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from anytime.errors import ConfigError


@dataclass
class CSVSchema:
    """Schema definition for CSV input files.

    Attributes:
        required_columns: Set of column names that must be present
        numeric_columns: Set of column names that must contain numeric values
        optional_columns: Set of column names that may be present (not required)
    """

    required_columns: set[str]
    numeric_columns: set[str]
    optional_columns: set[str] = frozenset()

    def __post_init__(self):
        # Validate that all required columns are also in numeric or optional
        all_defined = self.numeric_columns | self.optional_columns
        missing = self.required_columns - all_defined
        if missing:
            raise ValueError(f"Required columns not in numeric/optional: {missing}")


# Predefined schemas
ONE_SAMPLE_SCHEMA = CSVSchema(
    required_columns={"value"},
    numeric_columns={"value"},
    optional_columns=set(),
)

AB_TEST_SCHEMA = CSVSchema(
    required_columns={"arm", "value"},
    numeric_columns={"value"},
    optional_columns={"arm"},  # arm column is required but not numeric
)


class CSVReader:
    """Validated CSV reader for anytime inference.

    Handles missing values, invalid data, and schema validation.
    """

    def __init__(self, path: str, schema: CSVSchema):
        """Initialize CSV reader with schema validation.

        Args:
            path: Path to CSV file
            schema: Schema definition for validation

        Raises:
            FileNotFoundError: If file doesn't exist
            ConfigError: If schema validation fails
        """
        self.path = Path(path)
        self.schema = schema
        self._row_number = 0
        self._missing_values = 0
        self._invalid_values = 0

        if not self.path.exists():
            raise FileNotFoundError(f"CSV file not found: {path}")

    def validate_header(self, reader: csv.DictReader) -> None:
        """Validate CSV header against schema.

        Raises:
            ConfigError: If required columns are missing
        """
        if not reader.fieldnames:
            raise ConfigError(f"CSV file has no header row: {self.path}")

        present = set(reader.fieldnames)
        required = self.schema.required_columns

        missing = required - present
        if missing:
            raise ConfigError(
                f"CSV missing required columns: {missing}. "
                f"Found columns: {present}. "
                f"Required: {required}"
            )

    def read_numeric(self, row: dict[str, str], column: str) -> float | None:
        """Read and validate a numeric value.

        Args:
            row: CSV row as dictionary
            column: Column name to read

        Returns:
            Float value, or None if the value is missing/invalid

        Side effects:
            Increments _missing_values or _invalid_values counter
        """
        value_str = row.get(column, "")

        # Handle empty/missing values
        if not value_str or value_str.strip() == "":
            self._missing_values += 1
            return None

        # Try to parse as float
        try:
            return float(value_str)
        except ValueError:
            self._invalid_values += 1
            return None

    def rows(self) -> Iterator[tuple[dict[str, str], int]]:
        """Iterate over validated rows.

        Yields:
            Tuple of (row_dict, row_number) for each row

        Raises:
            ConfigError: If schema validation fails on header
        """
        with open(self.path, "r") as f:
            reader = csv.DictReader(f)
            self.validate_header(reader)

            for row in reader:
                self._row_number += 1
                yield row, self._row_number

    def get_summary(self) -> dict[str, Any]:
        """Get summary of read operation.

        Returns:
            Dictionary with row_count, missing_values, invalid_values
        """
        return {
            "row_count": self._row_number,
            "missing_values": self._missing_values,
            "invalid_values": self._invalid_values,
        }


def read_one_sample_csv(path: str, value_column: str = "value") -> CSVReader:
    """Create a CSV reader for one-sample analysis.

    Args:
        path: Path to CSV file
        value_column: Name of column containing values (default: "value")

    Returns:
        CSVReader instance with appropriate schema

    Raises:
        ConfigError: If schema setup fails
    """
    schema = CSVSchema(
        required_columns={value_column},
        numeric_columns={value_column},
        optional_columns=set(),
    )
    return CSVReader(path, schema)


def read_ab_test_csv(
    path: str,
    arm_column: str = "arm",
    value_column: str = "value"
) -> CSVReader:
    """Create a CSV reader for A/B test analysis.

    Args:
        path: Path to CSV file
        arm_column: Name of column containing arm labels (default: "arm")
        value_column: Name of column containing values (default: "value")

    Returns:
        CSVReader instance with appropriate schema

    Raises:
        ConfigError: If schema setup fails
    """
    schema = CSVSchema(
        required_columns={arm_column, value_column},
        numeric_columns={value_column},
        optional_columns={arm_column},  # arm column is required but not numeric
    )
    return CSVReader(path, schema)
