import csv
from pathlib import Path

import numpy as np


EXPECTED_COLUMNS = ("Reading", "X", "Y", "Z")


def _parse_xyz(value, column, file_path, line_number):
    try:
        return float(value.strip().replace(",", "."))
    except ValueError as error:
        raise ValueError(
            f"{file_path}:{line_number}: invalid {column} value {value!r}"
        ) from error


def read_xyz_table(file_path):
    """Read a semicolon-delimited Reading/X/Y/Z measurement table."""
    file_path = Path(file_path)
    rows = []
    seen_readings = set()

    with file_path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.reader(csv_file, delimiter=";")
        try:
            header = tuple(column.strip() for column in next(reader))
        except StopIteration as error:
            raise ValueError(f"{file_path}: empty CSV file") from error

        if header != EXPECTED_COLUMNS:
            expected = ";".join(EXPECTED_COLUMNS)
            raise ValueError(f"{file_path}: expected header {expected!r}")

        for line_number, row in enumerate(reader, start=2):
            if len(row) != len(EXPECTED_COLUMNS):
                raise ValueError(
                    f"{file_path}:{line_number}: expected 4 semicolon-delimited fields"
                )

            reading = row[0].strip()
            if not reading:
                raise ValueError(f"{file_path}:{line_number}: empty Reading value")

            reading_key = reading.upper()
            if reading_key in seen_readings:
                raise ValueError(
                    f"{file_path}:{line_number}: duplicate Reading value {reading!r}"
                )
            seen_readings.add(reading_key)

            xyz = np.array(
                [
                    _parse_xyz(row[index], column, file_path, line_number)
                    for index, column in enumerate(EXPECTED_COLUMNS[1:], start=1)
                ]
            )
            rows.append((reading, xyz))

    if not rows:
        raise ValueError(f"{file_path}: CSV file contains no measurements")

    return rows


def read_xyz_ramp(file_path):
    rows = read_xyz_table(file_path)

    for line_number, (reading, _) in enumerate(rows, start=2):
        try:
            int(reading)
        except ValueError as error:
            raise ValueError(
                f"{file_path}:{line_number}: grayscale Reading must be an integer"
            ) from error

    return np.stack([xyz for _, xyz in rows])


def read_named_xyz(file_path, required_readings):
    measurements = {reading.upper(): xyz for reading, xyz in read_xyz_table(file_path)}
    missing = [reading for reading in required_readings if reading not in measurements]
    if missing:
        raise ValueError(
            f"{file_path}: missing required Reading values: {', '.join(missing)}"
        )
    return measurements