@echo off
setlocal

set NO_KWEX = 0
set IGNORE_JAVA=0
set IGNORE_KERNEL=0

for %%A in (%*) do (
    if "%%A"=="no-kwex" (
        set NO_KWEX=1
    ) 
    if "%%A"=="ignore-java" (
        set IGNORE_JAVA=1
    ) 
    if "%%A"=="ignore-kernel" (
        set IGNORE_KERNEL=1
    )
)

if %NO_KWEX% == 0 (
    kwex ../templates/regression_test.vm regression_test.fit regression_test.lbl --output output/regression_test.lblx --log output/regression_test.log --override keep_json=ENABLED output_check=ENABLED warning_output=INFO
)

fc output\regression_test.lblx success\regression_test_success.lblx >nul
if errorlevel 1 (
    echo lblx bad
) else (
    echo lblx good
)

fc output\vals_regression_test.json success\vals_regression_test_success.json >nul
if errorlevel 1 (
    echo json bad
) else (
    echo json good
)

set output_log=output\regression_test.log
set output_nts=output\regression_test_nts.log
set success_log=success\regression_test_success.log
set success_nts=success\regression_test_success_nts.log

powershell -command "(Get-Content '%output_log%') -replace '^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}: ?', '' | Set-Content '%output_nts%' -Encoding ASCII"

powershell -command "(Get-Content '%success_log%') -replace '^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}: ?', '' | Set-Content '%success_nts%' -Encoding ASCII"

if %IGNORE_JAVA% == 1 (
    powershell -command "(Get-Content '%output_nts%') -notmatch 'VelocityWorker' -notmatch 'Java' | Set-Content '%output_nts%' -Encoding ASCII"
)

if %IGNORE_KERNEL% == 1 (
    powershell -command "(Get-Content '%output_nts%') -notmatch 'metakernel' | Set-Content '%output_nts%' -Encoding ASCII"
)

fc %output_nts% %success_nts% >nul
if errorlevel 1 (
    echo log bad
) else (
    echo log good
)

del %output_nts% %success_nts%
pause
