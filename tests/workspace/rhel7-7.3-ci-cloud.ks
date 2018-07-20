#version=RHEL7

# System authorization information
auth --enableshadow --passalgo=sha512
# Keyboard layouts
keyboard --vckeymap=us --xlayouts='us'
# System language
lang en_US.UTF-8
# Network information
network --bootproto=dhcp --onboot=on
services --enabled=network,sshd
# Root password = redhat
rootpw --iscrypted $6$huiciYFIrulM/UtY$eeGhAip7qwY6bYXoZMa8zbY1SLWpcVIpDW7FotRkaXpnp82cuLA/8cJL9BEobyP/2HRx4D/zcDAAzomMhdCFO/
# System timezone
timezone America/New_York --isUtc
# System bootloader configuration
bootloader --location=mbr --boot-drive=vda --append="console=ttyS0,115200n8 console=tty0"

# Partition Information
zerombr
clearpart --all --initlabel
part / --size 8000 --fstype xfs --ondisk vda

reboot

# Repositories; gets wiped out by Brew
repo --name="qe-cloud" --baseurl=http://download.eng.bos.redhat.com/rcm-guest/qeos-cloud-init/7.3/latest/x86_64/os/

# Packages
%packages
@core
cloud-init
cloud-utils-growpart
%end

#
# Add custom post scripts after the base post.
#
%post --erroronfail

# make sure firstboot doesn't start
echo "RUN_FIRSTBOOT=NO" > /etc/sysconfig/firstboot

echo -n "Network fixes"
# initscripts don't like this file to be missing.
cat > /etc/sysconfig/network << EOF
NETWORKING=yes
NOZEROCONF=yes
EOF

# For cloud images, 'eth0' _is_ the predictable device name, since
# we don't want to be tied to specific virtual (!) hardware
rm -f /etc/udev/rules.d/70*
ln -s /dev/null /etc/udev/rules.d/80-net-name-slot.rules

# simple eth0 config, again not hard-coded to the build hardware
cat > /etc/sysconfig/network-scripts/ifcfg-eth0 << EOF
DEVICE="eth0"
BOOTPROTO="dhcp"
ONBOOT="yes"
TYPE="Ethernet"
USERCTL="yes"
PEERDNS="yes"
IPV6INIT="no"
PERSISTENT_DHCLIENT="1"
EOF

# workaround https://bugzilla.redhat.com/show_bug.cgi?id=966888
if ! grep -q growpart /etc/cloud/cloud.cfg; then
  sed -i 's/ - resizefs/ - growpart\n - resizefs/' /etc/cloud/cloud.cfg
fi

# allow ssh access by root
sed -i 's/disable_root: 1/disable_root: 0/' /etc/cloud/cloud.cfg
sed -i 's/ssh_pwauth:   0/ssh_pwauth:   true/' /etc/cloud/cloud.cfg

#To disable tunneled clear text passwords
sed -i 's|\(^PasswordAuthentication \)no|\1yes|' /etc/ssh/sshd_config

# machine-id should be empty, systemd generate each VM's machine-id dynamically
cat /dev/null > /etc/machine-id

# remove rhgb and quiet from kernel cmdline
sed -i -e 's/ rhgb quiet//' /boot/grub2/grub.cfg

%end

