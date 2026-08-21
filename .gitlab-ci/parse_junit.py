#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2025-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import os
import pathlib
import sys
import xml.etree.ElementTree as ET  # nosec


def count_errors(junit_file):
    error_counter = 0
    tree = ET.parse(junit_file)  # noqa: S314
    root = tree.getroot()
    testsuites = root.findall("testsuite") if root.tag == "testsuites" else [root]

    for testsuite in testsuites:
        errors = int(testsuite.attrib.get("errors", "0"))
        failures = int(testsuite.attrib.get("failures", "0"))
        error_counter += errors + failures
    return error_counter


def coverage_percent(coverage_file):
    """
    Total line coverage from a cobertura report, as a percentage.

    Taken from 'lines-covered' and 'lines-valid' rather than the 'line-rate'
    attribute, which is rounded to four decimal places in the file.
    """
    root = ET.parse(coverage_file).getroot()  # noqa: S314
    valid = int(root.attrib["lines-valid"])
    if valid == 0:
        return 100.0
    return 100.0 * int(root.attrib["lines-covered"]) / valid


def clean_junit_xml(junit_file):
    """
    gitlab refuses to parse large junit files.
    This removes stdout and stderr from sucessful tests to decrease the file size.
    """
    tree = ET.parse(junit_file)  # noqa: S314
    root = tree.getroot()
    testsuites = root.findall("testsuite") if root.tag == "testsuites" else [root]

    for testsuite in testsuites:
        errors = int(testsuite.attrib.get("errors", "0"))
        failures = int(testsuite.attrib.get("failures", "0"))
        if errors == 0 and failures == 0:
            for testcase in testsuite.findall("testcase"):
                for tag in ["system-out", "system-err"]:
                    elem = testcase.find(tag)
                    if elem is not None:
                        testcase.remove(elem)

    tree.write(junit_file, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    test_report_path = pathlib.Path("./results")
    version = os.getenv("PYTHON_VERSION")
    failed = False

    junit_file = test_report_path / f"report_{version}.xml"
    print(f"Parsing {junit_file}")
    if not junit_file.is_file():
        print("Missing report file")
        sys.exit(1)
    error_counter = count_errors(junit_file)
    clean_junit_xml(junit_file)
    if error_counter > 0:
        print(f"Found {error_counter} errors.")
        failed = True

    # pytest already checks this with '--cov-fail-under', but it reports it the
    # same way it reports a failing test: exit code 1. The test run tolerates
    # that so that the run reaches the step which fetches the results, which
    # left a coverage drop with nothing to report it. Check it here instead,
    # where the reports have arrived and the exit code is the job's verdict.
    limit = os.getenv("COVERAGE_LIMIT")
    if limit:
        coverage_file = test_report_path / f"coverage_{version}.xml"
        if not coverage_file.is_file():
            print(f"Missing coverage report {coverage_file}")
            sys.exit(1)
        percent = coverage_percent(coverage_file)
        print(f"Coverage {percent:.2f}%, required {float(limit):.2f}%")
        if percent < float(limit):
            print("Coverage below the required limit.")
            failed = True

    if failed:
        sys.exit(1)
