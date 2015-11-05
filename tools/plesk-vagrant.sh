#!/bin/bash
set -e
export PLESK_DISABLE_HOSTNAME_CHECKING=1

wget -q -O /root/ai http://autoinstall.plesk.com/plesk-installer
bash /root/ai \
	--select-product-id=plesk \
	--select-release-id=PLESK_12_5_30 \
	--install-component panel \
	--install-component phpgroup \
	--install-component web-hosting \
	--install-component mod_fcgid \
	--install-component proftpd \
	--install-component webservers \
	--install-component nginx \
	--install-component mysqlgroup \
	--install-component php5.6 \
	--install-component l10n \
	--install-component heavy-metal-skin
plesk bin init_conf --init \
	-email changeme@example.com \
	-passwd changeme \
	-hostname-not-required
plesk bin license -i A00Q00-28H603-TPKC32-NH3N93-XF3830
plesk bin settings --set admin_info_not_required=true

