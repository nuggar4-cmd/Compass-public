# Compass

Compass is an English-language desktop app for finding software and visiting its official website. It includes local search, categories, alphabetical sorting and publisher details.

## Windows x64 portable candidate

[Download the RC6 Windows x64 ZIP](https://github.com/nuggar4-cmd/Compass-public/releases/download/v1.0.0rc6/Compass-1.0.0rc6-Windows-x64.zip) · [SHA-256 checksum](https://github.com/nuggar4-cmd/Compass-public/releases/download/v1.0.0rc6/Compass-1.0.0rc6-Windows-x64.zip.sha256) · [RC6 release notes](https://github.com/nuggar4-cmd/Compass-public/releases/tag/v1.0.0rc6)

Both packages are available without signing in to GitHub.

1. If you want to verify the download, compare the checksum file to the output from `Get-FileHash -Algorithm SHA256 .\Compass-1.0.0rc6-Windows-x64.zip` in PowerShell.
2. Extract the portable ZIP, open the `Compass` folder and double-click `Compass.exe`. Keep `_internal` alongside it. Python is bundled.
3. The candidate requires Windows x64 and the [Microsoft Edge WebView2 Evergreen Runtime](https://developer.microsoft.com/microsoft-edge/webview2/). If Windows blocks the unsigned executable, report the message and leave its protection settings enabled.

## Debian and Ubuntu package

[Download the RC6 Debian/Ubuntu package (.deb)](https://github.com/nuggar4-cmd/Compass-public/releases/download/v1.0.0rc6/Compass-1.0.0rc6-Linux-all.deb) · [SHA-256 checksum](https://github.com/nuggar4-cmd/Compass-public/releases/download/v1.0.0rc6/Compass-1.0.0rc6-Linux-all.deb.sha256)

Install the package and its dependencies with APT. It requires Python 3.11 or newer and WebKitGTK 2.40 or newer.

```sh
sudo apt install ./Compass-1.0.0rc6-Linux-all.deb
```

Launch **Compass** from the application menu or run `compass-desktop`. The Debian package uses the OS-provided WebKitGTK and keeps UI assets on a private, local renderer scheme. To build the package yourself, run `sh scripts/build-deb.sh`. The package and checksum appear in `dist/release`.

## Use Compass

Enter an app name or keyword in search, or narrow the list by category. Press Ctrl+K to focus search, or Escape to close app details. Select **Details** to see the publisher and complete destination. **Visit official website** asks for native confirmation before opening the default browser.

RC7 lets you combine search terms in any order and look up apps by publisher domain. If the desktop catalog fails to load, Compass explains what happened and offers **Retry**.

RC8 shows whether Compass is connecting to the desktop or reading the local catalog. It opens the catalog as soon as it is ready. The catalog includes 76 publisher listings and a Communication category.

**Verified publisher** identifies a reviewed starting address. **Caution** describes details such as a publisher preview or external downloads. If an address fails the catalog check, Compass shows **Blocked** and skips opening it. The Gaming category includes Steam, Epic Games Launcher, GOG GALAXY, and the itch.io app.

The [approved publisher destinations](APPROVED_SITES.md) are bundled. Compass has no accounts, telemetry, search-history storage, downloads, installers or automatic updates. Its Windows loopback listener serves only the four bundled interface assets and closes with the app. The initial publisher address is checked against the catalog. Once the browser opens it, redirects, privacy and downloads are handled by the browser and publisher.

## Suggest a catalog link

Choose **Suggest a link** in Compass (RC5 and later) or [open the suggestion form](https://github.com/nuggar4-cmd/Compass-public/issues/new?template=catalog-suggestion.yml). Sign in to GitHub to submit a public suggestion with the app name and its official publisher URL. Maintainers review [open catalog suggestions](https://github.com/nuggar4-cmd/Compass-public/issues?q=is%3Aissue+is%3Aopen+in%3Atitle+%22Catalog+suggestion%22), confirm that each page belongs to the publisher and check for duplicates before adding it to the bundled catalog.

## Build from source

On Windows x64, install CPython 3.14 and the Evergreen runtime, then open PowerShell in this folder:

```powershell
.\scripts\build-windows.ps1
```

The script installs hash-pinned build and runtime dependencies in a temporary environment, verifies the bundled catalog and runs the Python tests. It includes third-party notices in the `licenses` folder and writes the unsigned ZIP and checksum to `dist\release`. Add `-SmokeTest` to exercise the WebView2 bridge and launch an extracted copy of the packaged executable on an interactive Windows desktop.

For source development, install the lock into a clean Windows x64 CPython 3.14 environment:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes --only-binary=:all: -r requirements-windows-bootstrap.lock
.\.venv\Scripts\python.exe -m pip install --require-hashes --only-binary=:all: --no-binary=proxy-tools --no-build-isolation --no-cache-dir -r requirements-windows-x64.lock
.\.venv\Scripts\python.exe main.py
```

After setup, `start-windows.bat` also starts the source app. For an offline browser preview, open `ui/index.html`. The preview supports browsing and searching the catalog. To open a publisher site through Compass, use the desktop app.

## Sign the Windows package

On a Windows signing workstation with the Windows SDK and a trusted publisher certificate accessible in `Cert:\CurrentUser\My`, run:

```powershell
.\scripts\build-windows.ps1 -SmokeTest `
  -SigningCertificateThumbprint <publisher-certificate-thumbprint> `
  -TimestampUrl <RFC3161-timestamp-service>
```

The build signs `Compass.exe` before archiving it and verifies the Authenticode signature, timestamp and publisher thumbprint against the extracted executable. The checksum covers the complete ZIP.

## Verify changes

```text
python scripts/sync_catalog.py --check
python -m unittest discover -s tests -v
```

Update `compass/catalog.py` after the project owner approves a publisher destination. Run `python scripts/sync_catalog.py` to regenerate `ui/catalog.js` and commit both files. The Windows workflow checks the actual Edge WebView2 engine, exercises the native Cancel and OK buttons, checks the exact address handed to a test browser opener and launches the extracted portable package. The Debian workflow exercises the packaged UI and native confirmation with WebKitGTK.

## Stable release criteria

Test the exact packaged ZIP on clean Windows 10 and Windows 11 x64 systems without installing Python. Check launch, keyboard navigation, WebView2 setup guidance, and Cancel and OK with each machine's actual default browser. Review the locked dependencies, sign and timestamp the binary with the project's signing identity, then verify the signature and checksum of the package distributed through the intended release channel. Windows Server CI and the portable package are intended for candidate validation.
