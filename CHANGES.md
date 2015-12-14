# ChangeLog

Please note:
[the extension](https://ext.plesk.com/packages/f6847e61-33a7-4104-8dc9-d26a0183a8dd-letsencrypt) and [the plugin](https://pypi.python.org/pypi/letsencrypt-plesk) have separate release cycles.
The extension always installs the latest plugin version available on PyPI.
The changelog contains both components under the corresponding titles.

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
