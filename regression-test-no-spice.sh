#!/usr/bin/env bash
set -euo pipefail

kwex templates/regression_test_no_spice.vm tests/regression_test.fit tests/regression_test.lbl --output tests/output/regression_test_no_spice.lblx --log tests/output/regression_test_no_spice.log --override keep_json=ENABLED output_check=ENABLED warning_output=INFO

if cmp -s tests/output/regression_test_no_spice.lblx tests/success/regression_test_no_spice_success.lblx; then
    echo "lblx good"
else
    echo "lblx bad"
fi

if cmp -s tests/output/vals_regression_test_no_spice.json tests/success/vals_regression_test_no_spice_success.json; then
    echo "json good"
else
    echo "json bad"
fi

output_log=tests/output/regression_test_no_spice.log
output_nts=tests/output/regression_test_no_spice_nts.log
success_log=tests/success/regression_test_no_spice_success.log
success_nts=tests/success/regression_test_no_spice_success_nts.log

sed -E 's/^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}: ?//' "$output_log" > "$output_nts"
sed -E 's/^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}: ?//' "$success_log" > "$success_nts"

if cmp -s output_nts success_nts; then
    echo "log good"
else
    echo "log bad"
fi

rm -f "$output_nts" "$success_nts"
