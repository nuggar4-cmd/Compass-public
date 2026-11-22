# Compass

Compass is a desktop app for finding software and visiting its official website. It includes local search, categories, alphabetical sorting and publisher details, with an interface in English and Turkish.

## Windows x64 portable candidate

[Download the RC10 Windows x64 ZIP](https://github.com/nuggar4-cmd/Compass-public/releases/download/v1.0.0rc10/Compass-1.0.0rc10-Windows-x64.zip) · [SHA-256 checksum](https://github.com/nuggar4-cmd/Compass-public/releases/download/v1.0.0rc10/Compass-1.0.0rc10-Windows-x64.zip.sha256) · [RC10 release notes](https://github.com/nuggar4-cmd/Compass-public/releases/tag/v1.0.0rc10)

Both packages are available without signing in to GitHub.

1. If you want to verify the download, compare the checksum file to the output from `Get-FileHash -Algorithm SHA256 .\Compass-1.0.0rc10-Windows-x64.zip` in PowerShell.
2. Extract the portable ZIP, open the `Compass` folder and double-click `Compass.exe`. Keep `_internal` alongside it. Python is bundled.
3. The candidate requires Windows x64 and the [Microsoft Edge WebView2 Evergreen Runtime](https://developer.microsoft.com/microsoft-edge/webview2/). If Windows blocks the unsigned executable, report the message and leave its protection settings enabled.

## Debian and Ubuntu package

[Download the RC10 Debian/Ubuntu package (.deb)](https://github.com/nuggar4-cmd/Compass-public/releases/download/v1.0.0rc10/Compass-1.0.0rc10-Linux-all.deb) · [SHA-256 checksum](https://github.com/nuggar4-cmd/Compass-public/releases/download/v1.0.0rc10/Compass-1.0.0rc10-Linux-all.deb.sha256)

Install the package and its dependencies with APT. It requires Python 3.11 or newer and WebKitGTK 2.40 or newer.

```sh
sudo apt install ./Compass-1.0.0rc10-Linux-all.deb
```

Launch **Compass** from the application menu or run `compass-desktop`. The Debian package uses the OS-provided WebKitGTK and keeps UI assets on a private, local renderer scheme. To build the package yourself, run `sh scripts/build-deb.sh`. The package and checksum appear in `dist/release`.

## Use Compass

Search by app name, keyword or publisher address, or narrow the catalog by category. Choose **Cards** or **List** to change the display and **Recently added** to see the newest entries. **Clear filters** resets the search, category and sort together. Press Ctrl+K to focus search or Escape to close app details. Select **Details** to review the complete address before choosing **Visit official website**.

RC7 lets you combine search terms in any order and look up apps by publisher domain. If the desktop catalog fails to load, Compass explains what happened and offers **Retry**.

The desktop catalog includes 268 reviewed publisher listings across nine categories. The Turkish interface also finds common Turkish search terms such as `ses düzenleme` and `şifre`.

**Safe** (**Güvenli** in Turkish) identifies a reviewed publisher starting address. The check covers the address shown on the card. The browser and publisher handle redirects and downloaded files. **Caution** describes details such as a beta release or evaluation license. If an address fails the catalog check, Compass shows **Blocked** and skips opening it. The Gaming category includes Steam, Epic Games Launcher, Battle.net, and PS Remote Play.

The [approved publisher destinations](APPROVED_SITES.md) are bundled. Compass has no accounts, telemetry, search-history storage, downloads, installers or automatic updates. Its Windows loopback listener serves only the bundled interface assets and closes with the app. The initial publisher address is checked against the catalog. Once the browser opens it, redirects, privacy and downloads are handled by the browser and publisher.

## Check a link on desktop

Open **Link check** and paste a complete HTTPS address. **Safe** means the starting address matches a reviewed catalog entry. A well-formed address outside the catalog shows **Unverified**. Unsupported addresses, including local network and non-HTTPS addresses, show **Blocked** with a reason. Compass checks the pasted address locally without opening or looking up the page. This check covers the starting address. The content of the page, redirects, and downloaded files require their own checks.

**Explain with local AI** is optional. On a computer running [Ollama](https://ollama.com/download), run `ollama pull qwen2.5:0.5b` once, then use the button in Compass. The Ollama service must be running on `127.0.0.1:11434` on the same computer. To disable Ollama cloud features, set `OLLAMA_NO_CLOUD=1` in the environment that starts `ollama serve`. [Ollama setup](https://docs.ollama.com/quickstart) · [Ollama local-only settings](https://docs.ollama.com/faq) · [Qwen 2.5 0.5B model](https://ollama.com/library/qwen2.5:0.5b)

Compass sends only a fixed result code and interface language to the local model. The model chooses which explanation to show. The catalog and URL rules determine the status, including when Ollama is unavailable. Compass clears the pasted text when you leave the checker.

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
