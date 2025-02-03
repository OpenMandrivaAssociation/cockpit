%global debug_package %{nil}

# earliest base that the subpackages work on; this is still required as long as
# we maintain the basic/optional split, then it can be replaced with just %{version}.
%define required_base 266

%define _hardened_build 1

Name:           cockpit
Summary:        Web Console for Linux servers

License:        LGPL-2.1-or-later
URL:            https://cockpit-project.org/

Version:        332
Release:        1

# fedora does not appear to attach all the node modules needed for their
# product. git clone the repo, checkout tags/%%{version}, then git submodule update --init --recursive,
# copy out node_modules, download tar.xz from releases, then add node_modules directory to it
Source0:        https://github.com/cockpit-project/%{name}/%{name}-%{version}.tar.xz

BuildRequires: gcc
BuildRequires: gdb
BuildRequires: autoconf automake
BuildRequires: make
BuildRequires: pkgconfig(gio-unix-2.0)
BuildRequires: pkgconfig(json-glib-1.0)
BuildRequires: pkgconfig(polkit-agent-1) >= 0.105
BuildRequires: pkgconfig(libxslt)
BuildRequires: pkgconfig(pam)
BuildRequires: pkgconfig(python)
BuildRequires: pkgconfig(openssl)
# this is for runtimedir in the tls proxy ace21c8879
BuildRequires: pkgconfig(systemd) >= 235
BuildRequires: pkgconfig(gnutls) >= 3.4.3
BuildRequires: pkgconfig(zlib)
BuildRequires: pkgconfig(gssrpc) >= 1.11
BuildRequires: pkgconfig(glib-2.0) >= 2.50.0

BuildRequires: gettext >= 0.21
BuildRequires: glib-networking
BuildRequires: sed
BuildRequires: openssh-clients
BuildRequires: docbook-style-xsl
BuildRequires: krb5-server

# For documentation
BuildRequires: xmlto

# This is the "cockpit" metapackage. It should only
# Require, Suggest or Recommend other cockpit-xxx subpackages

Requires: cockpit-bridge
Requires: cockpit-ws
Requires: cockpit-system

# Optional components
Recommends: (cockpit-storaged if udisks2)
Recommends: (cockpit-packagekit if dnf)
Suggests: python-pcp

Recommends: (cockpit-networkmanager if NetworkManager)
# c-ostree is not in RHEL 8/9
Recommends: (cockpit-ostree if rpm-ostree)
Requires: subscription-manager-cockpit

BuildRequires:  python-devel
BuildRequires:  python-pip
BuildRequires:  procps-ng

%prep
%autosetup -p1 
CC=gcc
CXX=g++
LDFLAGS="%{build_ldflags} -lm"
%configure

%build
%make_build 

%check
make -j$(nproc) check

%install
%make_install
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/pam.d
install -p -m 644 tools/cockpit.pam $RPM_BUILD_ROOT%{_sysconfdir}/pam.d/cockpit
rm -f %{buildroot}/%{_libdir}/cockpit/*.so
install -D -p -m 644 AUTHORS COPYING README.md %{buildroot}%{_docdir}/cockpit/

# Build the package lists for resource packages
# cockpit-bridge is the basic dependency for all cockpit-* packages, so centrally own the page directory
echo '%dir %{_datadir}/cockpit' > base.list
echo '%dir %{_datadir}/cockpit/base1' >> base.list
find %{buildroot}%{_datadir}/cockpit/base1 -type f -o -type l >> base.list
echo '%{_sysconfdir}/cockpit/machines.d' >> base.list
echo %{buildroot}%{_datadir}/polkit-1/actions/org.cockpit-project.cockpit-bridge.policy >> base.list

echo '%dir %{_datadir}/cockpit/shell' >> system.list
find %{buildroot}%{_datadir}/cockpit/shell -type f >> system.list

echo '%dir %{_datadir}/cockpit/systemd' >> system.list
find %{buildroot}%{_datadir}/cockpit/systemd -type f >> system.list

echo '%dir %{_datadir}/cockpit/users' >> system.list
find %{buildroot}%{_datadir}/cockpit/users -type f >> system.list

echo '%dir %{_datadir}/cockpit/metrics' >> system.list
find %{buildroot}%{_datadir}/cockpit/metrics -type f >> system.list

echo '%dir %{_datadir}/cockpit/kdump' > kdump.list
find %{buildroot}%{_datadir}/cockpit/kdump -type f >> kdump.list

echo '%dir %{_datadir}/cockpit/sosreport' > sosreport.list
find %{buildroot}%{_datadir}/cockpit/sosreport -type f >> sosreport.list

echo '%dir %{_datadir}/cockpit/storaged' > storaged.list
find %{buildroot}%{_datadir}/cockpit/storaged -type f >> storaged.list

echo '%dir %{_datadir}/cockpit/networkmanager' > networkmanager.list
find %{buildroot}%{_datadir}/cockpit/networkmanager -type f >> networkmanager.list

echo '%dir %{_datadir}/cockpit/packagekit' > packagekit.list
find %{buildroot}%{_datadir}/cockpit/packagekit -type f >> packagekit.list

echo '%dir %{_datadir}/cockpit/apps' >> packagekit.list
find %{buildroot}%{_datadir}/cockpit/apps -type f >> packagekit.list

echo '%dir %{_datadir}/cockpit/static' > static.list
echo '%dir %{_datadir}/cockpit/static/fonts' >> static.list
find %{buildroot}%{_datadir}/cockpit/static -type f >> static.list

sed -i "s|%{buildroot}||" *.list

# remove selinux stuff
rm -r %buildroot/%_datadir/cockpit/selinux
rm -r %buildroot/%_datadir/metainfo/org.cockpit_project.cockpit_selinux.metainfo.xml

# -------------------------------------------------------------------------------
# Sub-packages

%description
The Cockpit Web Console enables users to administer GNU/Linux servers using a
web browser.

It offers network configuration, log inspection, diagnostic reports, SELinux
troubleshooting, interactive command-line sessions, and more.

%files
%doc %{_mandir}/man1/cockpit.1.zst
%{_docdir}/cockpit/AUTHORS
%{_docdir}/cockpit/COPYING
%{_docdir}/cockpit/README.md
%{_datadir}/metainfo/org.cockpit_project.cockpit.appdata.xml
%{_datadir}/icons/hicolor/128x128/apps/cockpit.png


%package bridge
Summary: Cockpit bridge server-side component
Requires: glib-networking

%description bridge
The Cockpit bridge component installed server side and runs commands on the
system on behalf of the web based user interface.

%files bridge -f base.list
%doc %{_mandir}/man1/cockpit-bridge.1.zst
%{_bindir}/cockpit-bridge
%{_libexecdir}/cockpit-askpass
%{python3_sitelib}/%{name}*

%package doc
Summary: Cockpit deployment and developer guide
BuildArch: noarch

%description doc
The Cockpit Deployment and Developer Guide shows sysadmins how to
deploy Cockpit on their machines as well as helps developers who want to
embed or extend Cockpit.

%files doc
%exclude %{_docdir}/cockpit/AUTHORS
%exclude %{_docdir}/cockpit/COPYING
%exclude %{_docdir}/cockpit/README.md
%{_docdir}/cockpit

%package system
Summary: Cockpit admin interface package for configuring and troubleshooting a system
BuildArch: noarch
Requires: cockpit-bridge >= %{version}-%{release}
%if !0%{?suse_version}
Requires: shadow-utils
%endif
Requires: grep
Requires: /usr/bin/pwscore
Requires: /usr/bin/date
Provides: cockpit-shell = %{version}-%{release}
Provides: cockpit-systemd = %{version}-%{release}
Provides: cockpit-tuned = %{version}-%{release}
Provides: cockpit-users = %{version}-%{release}



%description system
This package contains the Cockpit shell and system configuration interfaces.

%files system -f system.list
%dir %{_datadir}/cockpit/shell/images

%package ws
Summary: Cockpit Web Service
Requires: glib-networking
Requires: openssl
Requires: glib2 >= 2.50.0
Recommends: sscg >= 2.3
Recommends: system-logos
Suggests: sssd-dbus >= 2.6.2
# for cockpit-desktop
Suggests: python
Obsoletes: cockpit-tests < %{version}

# prevent hard python3 dependency for cockpit-desktop, it falls back to other browsers
%global __requires_exclude_from ^%{_libexecdir}/cockpit-client$

%description ws
The Cockpit Web Service listens on the network, and authenticates users.

If sssd-dbus is installed, you can enable client certificate/smart card
authentication via sssd/FreeIPA.

%files ws -f static.list
%doc %{_mandir}/man1/cockpit-desktop.1.zst
%doc %{_mandir}/man5/cockpit.conf.5.zst
%doc %{_mandir}/man8/cockpit-ws.8.zst
%doc %{_mandir}/man8/cockpit-tls.8.zst
%doc %{_mandir}/man8/pam_ssh_add.8.zst
%dir %{_sysconfdir}/cockpit
%config(noreplace) %{_sysconfdir}/cockpit/ws-certs.d
%config(noreplace) %{_sysconfdir}/pam.d/cockpit
# created in %post, so that users can rm the files
%ghost %{_sysconfdir}/issue.d/cockpit.issue
%ghost %{_sysconfdir}/motd.d/cockpit
%ghost %attr(0644, root, root) %{_sysconfdir}/cockpit/disallowed-users
%dir %{_datadir}/cockpit/issue
%{_datadir}/cockpit/issue/update-issue
%{_datadir}/cockpit/issue/inactive.issue
%{_unitdir}/cockpit.service
%{_unitdir}/cockpit-issue.service
%{_unitdir}/cockpit.socket
%{_unitdir}/cockpit-session-socket-user.service
%{_unitdir}/cockpit-session.socket
%{_unitdir}/cockpit-session@.service
%{_unitdir}/cockpit-wsinstance-http.socket
%{_unitdir}/cockpit-wsinstance-http.service
%{_unitdir}/cockpit-wsinstance-https-factory.socket
%{_unitdir}/cockpit-wsinstance-https-factory@.service
%{_unitdir}/cockpit-wsinstance-https@.socket
%{_unitdir}/cockpit-wsinstance-https@.service
%{_unitdir}/cockpit-wsinstance-socket-user.service
%{_unitdir}/system-cockpithttps.slice
%{_prefix}/%{__lib}/tmpfiles.d/cockpit-ws.conf
%{_libdir}/security/pam*.so
%{_libexecdir}/cockpit-ws
%{_libexecdir}/cockpit-wsinstance-factory
%{_libexecdir}/cockpit-tls
%{_libexecdir}/cockpit-client
%{_libexecdir}/cockpit-client.ui
%{_libexecdir}/cockpit-desktop
%{_libexecdir}/cockpit-certificate-ensure
%{_libexecdir}/cockpit-certificate-helper
%{_libexecdir}/cockpit-session
%{_datadir}/cockpit/branding

%post ws
# set up dynamic motd/issue symlinks on first-time install; don't bring them back on upgrades if admin removed them
# disable root login on first-time install; so existing installations aren't changed
if [ "$1" = 1 ]; then
    mkdir -p /etc/motd.d /etc/issue.d
    ln -s ../../run/cockpit/issue /etc/motd.d/cockpit
    ln -s ../../run/cockpit/issue /etc/issue.d/cockpit.issue
    printf "# List of users which are not allowed to login to Cockpit\n" > /etc/cockpit/disallowed-users
    printf "root\n" >> /etc/cockpit/disallowed-users
    chmod 644 /etc/cockpit/disallowed-users
fi

# on upgrades, adjust motd/issue links to changed target if they still exist (changed in 331)
if [ "$1" = 2 ]; then
    if [ "$(readlink /etc/motd.d/cockpit 2>/dev/null)" = "../../run/cockpit/motd" ]; then
        ln -sfn ../../run/cockpit/issue /etc/motd.d/cockpit
    fi
    if [ "$(readlink /etc/issue.d/cockpit.issue 2>/dev/null)" = "../../run/cockpit/motd" ]; then
        ln -sfn ../../run/cockpit/issue /etc/issue.d/cockpit.issue
    fi
fi

%tmpfiles_create cockpit-ws.conf
%systemd_post cockpit.socket cockpit.service
# firewalld only partially picks up changes to its services files without this
test -f %{_bindir}/firewall-cmd && firewall-cmd --reload --quiet || true

# check for deprecated PAM config
if test -f %{_sysconfdir}/pam.d/cockpit &&  grep -q pam_cockpit_cert %{_sysconfdir}/pam.d/cockpit; then
    echo '**** WARNING:'
    echo '**** WARNING: pam_cockpit_cert is a no-op and will be removed in a'
    echo '**** WARNING: future release; remove it from your /etc/pam.d/cockpit.'
    echo '**** WARNING:'
fi

# remove obsolete system user on upgrade (replaced with DynamicUser in version 330)
if getent passwd cockpit-wsinstance >/dev/null; then
    userdel cockpit-wsinstance
fi

%preun ws
%systemd_preun cockpit.socket cockpit.service

%postun ws
%systemd_postun_with_restart cockpit.socket cockpit.service

%package kdump
Summary: Cockpit user interface for kernel crash dumping
Requires: cockpit-bridge >= %{required_base}
Requires: cockpit-shell >= %{required_base}
Requires: /usr/bin/kdumpctl
BuildArch: noarch
 
%description kdump
The Cockpit component for configuring kernel crash dumping.
 
%files kdump -f kdump.list
%{_datadir}/metainfo/org.cockpit_project.cockpit_kdump.metainfo.xml
 
%package sosreport
Summary: Cockpit user interface for diagnostic reports
Requires: cockpit-bridge >= %{required_base}
Requires: cockpit-shell >= %{required_base}
Requires: sos
BuildArch: noarch
 
%description sosreport
The Cockpit component for creating diagnostic reports with the
sosreport tool.
 
%files sosreport -f sosreport.list
%{_datadir}/metainfo/org.cockpit_project.cockpit_sosreport.metainfo.xml
%{_datadir}/icons/hicolor/64x64/apps/cockpit-sosreport.png
 
%package networkmanager
Summary: Cockpit user interface for networking, using NetworkManager
Requires: cockpit-bridge >= %{required_base}
Requires: cockpit-shell >= %{required_base}
Requires: NetworkManager >= 1.6
# Optional components
Recommends: NetworkManager-team
BuildArch: noarch
 
%description networkmanager
The Cockpit component for managing networking.  This package uses NetworkManager.
 
%files networkmanager -f networkmanager.list
%{_datadir}/metainfo/org.cockpit_project.cockpit_networkmanager.metainfo.xml

%package -n cockpit-storaged
Summary: Cockpit user interface for storage, using udisks
Requires: cockpit-shell >= %{required_base}
Requires: udisks2 >= 2.9
Recommends: udisks2-lvm2 >= 2.9
Recommends: udisks2-iscsi >= 2.9
Recommends: device-mapper-multipath
Recommends: clevis-luks
Requires: python
Requires: python-dbus
BuildArch: noarch

%description -n cockpit-storaged
The Cockpit component for managing storage.  This package uses udisks.

%files -n cockpit-storaged -f storaged.list
%{_datadir}/metainfo/org.cockpit_project.cockpit_storaged.metainfo.xml

%post storaged

# version 332 moved the btrfs temp mounts db to /run
if [ "$1" = 2 ] && [ -d /var/lib/cockpit/btrfs ]; then
    rm -rf --one-file-system  /var/lib/cockpit/btrfs || true
fi

%package -n cockpit-packagekit
Summary: Cockpit user interface for packages
BuildArch: noarch
Requires: cockpit-bridge >= %{required_base}
Requires: PackageKit
Recommends: python-tracer
# HACK: https://bugzilla.redhat.com/show_bug.cgi?id=1800468
Requires: polkit

%description -n cockpit-packagekit
The Cockpit components for installing OS updates and Cockpit add-ons,
via PackageKit.

%files -n cockpit-packagekit -f packagekit.list

