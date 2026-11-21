# Bundled third-party notices

The Windows packaging script also copies CPython's LICENSE.txt and the license
files from installed Python packages whose files appear in the PyInstaller bundle.

- Microsoft.Web.WebView2 contains the original license and notice from
  Microsoft.Web.WebView2 1.0.3856.49. pywebview 6.2.1 supplies the SDK DLLs.
  [NuGet package](https://www.nuget.org/packages/Microsoft.Web.WebView2/1.0.3856.49)
- proxy-tools contains the upstream license missing from the 0.1.0 source
  distribution. [Upstream license](https://github.com/jtushman/proxy_tools/blob/db43f1e35d4f90a65c5a4d56d9e9af88212ec6e6/LICENSE.txt)
- pywebview-js contains the notices for the JavaScript libraries in pywebview's
  bundled DOM serializer and polyfills.
- pywebview-js covers domJSON 0.1.2, Native Promise Only 0.8.1, and Symbol-ES6
  0.1.2 in the bundled pywebview JavaScript assets.
- OpenSSL 3.5.9 and Expat 2.9.0 supply the shipped TLS libraries and Python XML
  parser. [OpenSSL license](https://github.com/openssl/openssl/blob/openssl-3.5.9/LICENSE.txt)
  [Expat license](https://github.com/libexpat/libexpat/blob/R_2_9_0/expat/COPYING)
