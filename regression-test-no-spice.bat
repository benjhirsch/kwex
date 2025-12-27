@echo off
setlocal

kwex templates/regression_test_no_spice.vm tests/regression_test.fit tests/regression_test.lbl --output tests/output/regression_test_no_spice.lblx --log tests/output/regression_test_no_spice.log --override keep_json=ENABLED output_check=ENABLED warning_output=INFO

fc tests\output\regression_test_no_spice.lblx tests\success\regression_test_no_spice_success.lblx >nul
if errorlevel 1 (
    echo lblx bad
) else (
    echo lblx good
)

fc tests\output\vals_regression_test_no_spice.json tests\success\vals_regression_test_no_spice_success.json >nul
if errorlevel 1 (
    echo json bad
) else (
    echo json good
)

set output_log=tests\output\regression_test_no_spice.log
set output_nts=tests\output\regression_test_no_spice_nts.log
set success_log=tests\success\regression_test_no_spice_success.log
set success_nts=tests\success\regression_test_no_spice_success_nts.log

powershell -command ^
    "(Get-Content '%output_log%') -replace '^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}: ?', '' | Set-Content '%output_nts%'"

powershell -command ^
    "(Get-Content '%success_log%') -replace '^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}: ?', '' | Set-Content '%success_nts%'"

fc %output_nts% %success_nts% >nul
if errorlevel 1 (
    echo log bad
) else (
    echo log good
)

del %output_nts% %success_nts%
pause
