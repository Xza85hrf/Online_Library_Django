@echo off
echo Updating Flux AI Environment...
echo This will update the tokenizers package to fix compatibility issues.
echo.

python update_flux_environment.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Environment update completed successfully!
    echo You can now run the test_single_image.py script to verify the advanced AI image generation.
) else (
    echo.
    echo Environment update encountered issues.
    echo Please check the flux_environment_update.log file for details.
)

pause
