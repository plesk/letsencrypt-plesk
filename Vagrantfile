# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

# Setup instructions from docs/contributing.rst
$ubuntu_setup_script = <<SETUP_SCRIPT
cd /vagrant
./tools/plesk-vagrant.sh
./bootstrap/install-deps.sh
./bootstrap/dev/venv.sh
SETUP_SCRIPT

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.define "ubuntu-trusty", primary: true do |ubuntu_trusty|
    ubuntu_trusty.vm.box = "ubuntu/trusty64"
    ubuntu_trusty.vm.provider "parallels" do |v|
      ubuntu_trusty.vm.box = "puphpet/ubuntu1404-x64"
    end

    ubuntu_trusty.vm.provision "shell", inline: $ubuntu_setup_script
    ubuntu_trusty.vm.provider "virtualbox" do |v|
      # VM needs more memory to run test suite, got "OSError: [Errno 12]
      # Cannot allocate memory" when running
      # letsencrypt.client.tests.display.util_test.NcursesDisplayTest
      v.memory = 1024
    end
    config.vm.network "forwarded_port", guest: 80, host: 1080
    config.vm.network "forwarded_port", guest: 433, host: 10443
    # Plesk ports
    config.vm.network "forwarded_port", guest: 8443, host: 8443
    config.vm.network "forwarded_port", guest: 8880, host: 8880
  end

end
