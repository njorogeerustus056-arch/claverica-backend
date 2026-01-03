@echo off
echo Testing Authentication with Your Credentials
echo ============================================
echo.

set EMAIL=eruznyaga001@gmail.com
set PASSWORD=38876879Eruz

echo Testing Login...
curl -X POST "https://claverica-backend.onrender.com/api/auth/login/" ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"%EMAIL%\",\"password\":\"%PASSWORD%\"}" ^
  -o login_response.json

echo.
echo Login Response:
type login_response.json
echo.

REM Extract token if login was successful
for /f "tokens=2 delims=:," %%a in ('type login_response.json ^| findstr "access"') do (
    set TOKEN=%%~a
    set TOKEN=!TOKEN:"=!
    set TOKEN=!TOKEN: =!
)

if defined TOKEN (
    echo Found token: !TOKEN:~0,50!...
    echo.
    echo Testing /me endpoint...
    curl "https://claverica-backend.onrender.com/api/auth/me/" ^
      -H "Authorization: Bearer !TOKEN!" ^
      -o me_response.json
    echo.
    echo /me Response:
    type me_response.json
) else (
    echo No token found in response.
    echo.
    echo Trying registration instead...
    curl -X POST "https://claverica-backend.onrender.com/api/auth/register/" ^
      -H "Content-Type: application/json" ^
      -d "{\"email\":\"%EMAIL%\",\"password\":\"%PASSWORD%\",\"password2\":\"%PASSWORD%\"}" ^
      -o register_response.json
    echo.
    echo Registration Response:
    type register_response.json
)

echo.
echo ============================================
echo Testing complete.