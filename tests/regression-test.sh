#!/usr/bin/env bash
set -euo pipefail

kwex ../templates/regression_test.vm regression_test.fit regression_test.lbl --output output/regression_test.lblx --log output/regression_test.log --override keep_json=ENABLED output_check=ENABLED warning_output=INFO

if cmp -s output/regression_test.lblx success/regression_test_success.lblx; then
    echo "lblx good"
else
    echo "lblx bad"
fi

if cmp -s output/vals_regression_test.json success/vals_regression_test_success.json; then
    echo "json good"
else
    echo "json bad"
fi

output_log=output/regression_test.log
output_nts=output/regression_test_nts.log
success_log=success/regression_test_success.log
success_nts=success/regression_test_success_nts.log

sed -E 's/^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}: ?//' "$output_log" > "$output_nts"
sed -E 's/^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}: ?//' "$success_log" > "$success_nts"

if "$1" == "ignore-java"; then
    sed -E -i "/Java/d; /VelocityWorker/d" "$output_nts"

if cmp -s "$output_nts" "$success_nts"; then
    echo "log good"
else
    echo "log bad"
fi

rm -f "$output_nts" "$success_nts"
