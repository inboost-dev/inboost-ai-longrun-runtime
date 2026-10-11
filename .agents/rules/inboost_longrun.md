# InBoost LongRun Optimization Rules

1. **Context Conservation**: Before reading large files, use `l0_view_outline` to inspect declarations and structure.
2. **Test Failure Isolation**: Filter test logs and runtime exceptions via `l0_clean_test_log` to eliminate noise and isolate failing lines.
3. **Syntax Integrity**: Validate all code modifications and diffs with `l0_verify_syntax` prior to finalizing changes.
4. **Edit Scope Compliance**: Ensure edits remain focused and within budget. Verify with `l0_verify_edit_scope`.
5. **Execution Optimization**: Run test commands via `l0_run_test` for compact results. Check session economy with `l0_savings_report`.
