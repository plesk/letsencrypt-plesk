# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.box = "plesk/plesk-12.5"

  config.vm.provider "virtualbox" do |v|
    # hard links are not supported - could not prepare build
    config.vm.network "private_network", type: "dhcp"
    config.vm.synced_folder ".", "/vagrant", type: "nfs"
  end

  config.vm.provision "shell", path: "tools/plesk-vagrant.sh"
  config.vm.provider "virtualbox" do |v|
    v.memory = 1024
  end
  config.vm.network "forwarded_port", guest: 80, host: 1080
  config.vm.network "forwarded_port", guest: 433, host: 10443
  # Plesk ports
  config.vm.network "forwarded_port", guest: 8443, host: 8443
  config.vm.network "forwarded_port", guest: 8880, host: 8880

end
