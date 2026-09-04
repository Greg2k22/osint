#!/usr/bin/env python3
import argparse
from osint_workbench.services.tool_runs import finalize_case_tool_runs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('case')
    args = parser.parse_args()
    result = finalize_case_tool_runs(args.case)
    print(f"CASE tool status: {result['status']}")
    return 2 if result['status'] == 'FAILED' else 0


if __name__ == '__main__':
    raise SystemExit(main())
