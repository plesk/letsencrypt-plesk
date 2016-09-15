# ChangeLog

Please note:
[the extension](https://ext.plesk.com/packages/f6847e61-33a7-4104-8dc9-d26a0183a8dd-letsencrypt) and [the plugin](https://pypi.python.org/pypi/letsencrypt-plesk) have separate release cycles.
The extension always installs the latest plugin version available on PyPI.
The changelog contains both components under the corresponding titles.

## Extension 1.8
* Upgrade on Windows recreates virtualenv
* Fix issues after upgrade Plesk to Onyx

## Extension 1.7 and Plugin 0.1.7
* ConnectionError on Windows 2012 (issue #103)
* Update certificate with new API in Onyx
* Use certbot packages instead of letsencrypt
* Update subscriber agreement
* Hide disabled webspaces from the domains list

## Extension 1.6
* Switch from system python to plesk-py27 on all unix OSes (issues #59, #68, #70)

## Extension 1.5-1 and Plugin 0.1.5
* Windows support (2012 and above, Plesk 12.5 MU#24 is required)
* Translation added (ar, cs-CZ, da-DK, de-DE, el-GR, es-ES, fi-FI, fr-FR, he-IL, hu-HU, id-ID, it-IT, ja-JP, ko-KR, ms-MY, nb-NO, nl-NL, pl-PL, pt-BR, pt-PT, ro-RO, ru-RU, sv-SE, th-TH, tl-PH, tr-TR, uk-UA, vi-VN, zh-CN, zh-TW)
* Bugfix: Always put .htaccess in the challenges folder (issues #63 and #82)

## Extension 1.4-1
* Fix certificates renew task broken in 1.3 (issue #77)

## Extension 1.3-1
* Debian 6 is now supported
* No more conflicts with alt-python-virtualenv on CloudLinux
* Extension now ignores unsupported domains:
  * Inactive (disabled/suspended) domains
  * Wildcard subdomains
  * Domains without web hosting
  * IDN domains
* Fixed PHP Warning: Invalid argument supplied for foreach
* Users can now secure Plesk with www. prefix in hostname (issue #11)
* Store CLI options for certificate renewal (issue #46)

## Plugin 0.1.2
* Disable rewrite rules and satisfy authentication (with `.htaccess` file) in challenges directory (issues #13 and #16)
* ExpatError in case Plesk port 8443 is customized (issue #30). Thanks to @MatrixCrawler
* Disable HTTPS warnings: localhost is always trusted

## Extension 1.2-1
* Ability to use the certificate for Plesk (issue #11)
* Bugfix: Duplicate renew tasks if the original was changed
* Add note about monthly certificate renewal

## Plugin 0.1.1
* Ability to use the certificate for Plesk: `--letsencrypt-plesk:plesk-secure-panel` (issue #11)

## Extension 1.1-1
* Ability to include www.domain.tld as an alternative domain name (issue #4)
* Save the previously used e-mail address (issue #17)

## Extension 1.0-1
* Install binary dependences from wheels (gcc is not required)
* List of hosted domains and subdomains
* Button under each domain on Websites&Domains
* Submit e-mail and automaticaly install the certificate on the domain
* Monthly task renews certificates issued by Let's Encrypt (according to the name of the certificate)

## Plugin 0.1.0
* Retrieve info about hosted domains through Plesk API
* Install certificates in Plesk
* Treat www.domain.tld as an alias of domain.tld
