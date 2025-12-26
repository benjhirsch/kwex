@echo off

kwex templates/regression_test_no_spice.vm tests/regression_test.fit tests/regression_test.lbl --output tests/output/regression_test_no_spice.lblx --log tests/output/regression_test_no_spice.log --override keep_json=ENABLED output_check=ENABLED warning_output=INFO

fc /b tests\output\regression_test_no_spice.lblx tests\success\regression_test_no_spice_success.lblx >nul
if errorlevel 1 (
    echo bad > report.txt
) else (
    echo good > report.txt
)
