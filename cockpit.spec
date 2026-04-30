#
# Copyright (C) 2014-2020 Red Hat, Inc.
# SPDX-License-Identifier: LGPL-2.1-or-later
#
# OpenMandriva adaptation based on Fedora spec
# https://github.com/cockpit-project/cockpit/blob/main/tools/cockpit.spec
#

%define required_base 266

%define _hardened_build 1
%define __lib lib

# Exclude Fedora-specific versioned ELF symbol provides and python3 path
# OpenMandriva uses package-name Requires instead
%global __requires_exclude ^(/usr/sbin/python3|libjson-glib-1\.0\.so\.0\(libjson-glib|libgnutls\.so\.30\(GNUTLS|libgssapi_krb5\.so\.2\(gssapi_krb5|libsystemd\.so\.0\(LIBSYSTEMD)

# OpenMandriva: no SELinux by default
%if 0%{?omv}
%define with_selinux 0
%else
%define with_selinux 1
%endif

# OpenMandriva: no nodejs-esbuild in repos yet → use prebuilt JS bundle
%if 0%{?omv}
%define rebuild_bundle 0
%else
%if 0%{?fedora} >= 42
%{!?rebuild_bundle: %define rebuild_bundle 1}
%endif
%endif

%if 0%{?rhel}
%define bundle_docs 1
%endif

%define pamconfdir %{_sysconfdir}/pam.d
%define pamconfig tools/cockpit.pam

%if %{defined _pamdir}
%define pamdir %{_pamdir}
%else
%define pamdir %{_libdir}/security
%endif

%define enable_multihost 1
%if 0%{?omv} == 0
%if 0%{?fedora} >= 41 || 0%{?rhel} >= 10
%define enable_multihost 0
%endif
%endif

%if 0%{?with_selinux}
%define selinuxtype targeted
%define selinux_configure_arg --enable-selinux-policy=%{selinuxtype}
%endif

Name:           cockpit
Summary:        Web Console for Linux servers
License:        LGPL-2.1-or-later AND GPL-3.0-or-later AND MIT AND CC-BY-SA-3.0 AND BSD-3-Clause
URL:            https://cockpit-project.org/

Version:        360.1
Release:        1%{?dist}
Source0:        https://github.com/cockpit-project/cockpit/releases/download/%{version}/cockpit-%{version}.tar.xz
%if 0%{?rebuild_bundle}
Source1:        https://github.com/cockpit-project/cockpit/releases/download/%{version}/cockpit-node-%{version}.tar.xz
%endif
Source2:        omv-logo.png
Source3:        omv-branding.css

BuildRequires: gcc
BuildRequires: pkgconfig(gio-unix-2.0)
BuildRequires: pkgconfig(json-glib-1.0)
BuildRequires: pkgconfig(polkit-agent-1) >= 0.105
%if 0%{?omv}
BuildRequires: lib64pam-devel
%else
BuildRequires: pam-devel
%endif
BuildRequires: autoconf automake
BuildRequires: make
BuildRequires: python3-devel
BuildRequires: gettext >= 0.21
BuildRequires: pkgconfig(openssl)
BuildRequires: pkgconfig(gnutls) >= 3.4.3
BuildRequires: pkgconfig(zlib)
BuildRequires: pkgconfig(krb5-gssapi)
BuildRequires: glib-networking
BuildRequires: sed
BuildRequires: glib2-devel >= 2.68.0
BuildRequires: pkgconfig(libsystemd) >= 235
BuildRequires: openssh-clients
BuildRequires: krb5-server
BuildRequires: gdb

%if 0%{?rebuild_bundle}
BuildRequires: nodejs
BuildRequires: %{_bindir}/node
BuildRequires: nodejs-esbuild
%endif

%if !%{defined bundle_docs}
BuildRequires: asciidoctor
%endif

%if 0%{?with_selinux}
BuildRequires: selinux-policy
BuildRequires: selinux-policy-devel
%endif

BuildRequires: python3-pip
%if 0%{?omv} == 0 && 0%{?rhel} == 0
BuildRequires: procps-ng
BuildRequires: python3-pytest-asyncio
BuildRequires: python3-pytest-timeout
%endif

Requires: cockpit-bridge
Requires: cockpit-ws
Requires: cockpit-system

Recommends: (cockpit-storaged if udisks2)
Recommends: (cockpit-packagekit if dnf)
Recommends: (cockpit-networkmanager if NetworkManager)
%if 0%{?omv} == 0
Recommends: (cockpit-ostree if rpm-ostree)
Suggests: cockpit-selinux
%endif
Suggests: python3-pcp


%prep
%setup -q -n cockpit-%{version}
%if 0%{?rebuild_bundle}
%setup -q -D -T -a 1 -n cockpit-%{version}
%endif


%build
%if 0%{?rebuild_bundle}
rm -rf dist
NODE_ENV=production NODE_PATH=/usr/lib/node_modules:$(echo /usr/lib/node_modules_*) ./build.js
%endif

%configure \
    %{?selinux_configure_arg} \
    --with-pamdir='%{pamdir}' \
%if %{enable_multihost}
    --enable-multihost \
%endif
%if %{defined bundle_docs}
    --disable-doc \
%endif

%make_build


%check
%if 0%{?omv}
# skip make check on OpenMandriva — unit tests require full systemd session
%else
make -j$(nproc) check
%endif


%install
%make_install

# OpenMandriva branding
install -d %{buildroot}%{_datadir}/cockpit/branding/openmandriva
install -p -m 644 %{SOURCE2} %{buildroot}%{_datadir}/cockpit/branding/openmandriva/logo.png
install -p -m 644 %{SOURCE3} %{buildroot}%{_datadir}/cockpit/branding/openmandriva/branding.css

mkdir -p $RPM_BUILD_ROOT%{pamconfdir}
install -p -m 644 %{pamconfig} $RPM_BUILD_ROOT%{pamconfdir}/cockpit

rm -f %{buildroot}/%{_libdir}/cockpit/*.so
install -D -p -m 644 AUTHORS README.md %{buildroot}%{_docdir}/cockpit/

%if %{defined bundle_docs}
%define docbundledir %{_builddir}/%{name}-%{version}/doc/output/html
install -d %{buildroot}%{_docdir}/cockpit/guide
cp -rp %{docbundledir}/* %{buildroot}%{_docdir}/cockpit/guide/
%define manbundledir %{_builddir}/%{name}-%{version}/doc/output/man
for section in 1 5 8; do
  for manpage in %{manbundledir}/*.${section}; do
    install -D -p -m 644 "$manpage" %{buildroot}%{_mandir}/man${section}/$(basename "$manpage")
  done
done
%endif

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

echo '%dir %{_datadir}/cockpit/selinux' > selinux.list
find %{buildroot}%{_datadir}/cockpit/selinux -type f >> selinux.list

echo '%dir %{_datadir}/cockpit/static' > static.list
echo '%dir %{_datadir}/cockpit/static/fonts' >> static.list
find %{buildroot}%{_datadir}/cockpit/static -type f >> static.list

sed -i "s|%{buildroot}||" *.list

%if 0%{?omv}
rm -rf %{buildroot}%{_datadir}/cockpit/selinux || true
%endif

rm -rf %{buildroot}/usr/src/debug


# -------------------------------------------------------------------------------
# Sub-packages

%description
The Cockpit Web Console enables users to administer GNU/Linux servers using a
web browser.

It offers network configuration, log inspection, diagnostic reports,
interactive command-line sessions, and more.


%files
%license LICENSES/LGPL-2.1.txt
%{_docdir}/cockpit/AUTHORS
%{_docdir}/cockpit/README.md
%{_datadir}/metainfo/org.cockpit_project.cockpit.appdata.xml
%{_datadir}/icons/hicolor/128x128/apps/cockpit.png
%doc %{_mandir}/man1/cockpit.1.gz


%package bridge
Summary: Cockpit bridge server-side component
BuildArch: noarch

%description bridge
The Cockpit bridge component installed server side and runs commands on the
system on behalf of the web based user interface.

%files bridge -f base.list
%license LICENSES/GPL-3.0.txt
%doc %{_mandir}/man1/cockpit-bridge.1.gz
%{_bindir}/cockpit-bridge
%{_libexecdir}/cockpit-askpass
%{python3_sitelib}/%{name}*


%package doc
Summary: Cockpit deployment and developer guide
BuildArch: noarch

%description doc
The Cockpit Deployment and Developer Guide.

%files doc
%license LICENSES/LGPL-2.1.txt
%exclude %{_docdir}/cockpit/AUTHORS
%exclude %{_docdir}/cockpit/README.md
%{_docdir}/cockpit


%package system
Summary: Cockpit admin interface package for configuring and troubleshooting a system
BuildArch: noarch
Requires: cockpit-bridge >= %{version}-%{release}
Requires: shadow-utils
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
%license LICENSES/LGPL-2.1.txt
%dir %{_datadir}/cockpit/shell/images


%package ws
Summary: Cockpit Web Service
Requires: openssl
Requires: glib2 >= 2.68.0
%if 0%{?omv}
Requires: lib64json-glib1.0_0
Requires: lib64gnutls30
Requires: lib64gssapi_krb5_2
Requires: lib64systemd0
%endif
Recommends: sscg >= 2.3
Recommends: system-logos
Suggests: sssd-dbus >= 2.6.2
Suggests: python3
Obsoletes: cockpit-tests < 331

%global __requires_exclude_from ^%{_libexecdir}/cockpit-client$

%description ws
The Cockpit Web Service listens on the network, and authenticates users.

%files ws -f static.list
%license LICENSES/LGPL-2.1.txt
%doc %{_mandir}/man1/cockpit-desktop.1.gz
%doc %{_mandir}/man5/cockpit.conf.5.gz
%doc %{_mandir}/man8/cockpit-ws.8.gz
%doc %{_mandir}/man8/cockpit-tls.8.gz
%doc %{_mandir}/man8/pam_ssh_add.8.gz
%dir %{_sysconfdir}/cockpit
%config(noreplace) %{_sysconfdir}/cockpit/ws-certs.d
%config(noreplace) %{pamconfdir}/cockpit
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
%{pamdir}/pam_ssh_add.so
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
%if 0%{?omv}
%dir %{_datadir}/cockpit/branding/openmandriva
%{_datadir}/cockpit/branding/openmandriva/logo.png
%{_datadir}/cockpit/branding/openmandriva/branding.css
%endif

%post ws
if [ "$1" = 1 ]; then
    mkdir -p /etc/motd.d /etc/issue.d
    ln -s ../../run/cockpit/issue /etc/motd.d/cockpit
    ln -s ../../run/cockpit/issue /etc/issue.d/cockpit.issue
    printf "# List of users which are not allowed to login to Cockpit\n" > /etc/cockpit/disallowed-users
    printf "root\n" >> /etc/cockpit/disallowed-users
    chmod 644 /etc/cockpit/disallowed-users
fi

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
test -f %{_bindir}/firewall-cmd && firewall-cmd --reload --quiet || true

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
%license LICENSES/LGPL-2.1.txt
%{_datadir}/metainfo/org.cockpit_project.cockpit_kdump.metainfo.xml


%package sosreport
Summary: Cockpit user interface for diagnostic reports
Requires: cockpit-bridge >= %{required_base}
Requires: cockpit-shell >= %{required_base}
Requires: sos
BuildArch: noarch

%description sosreport
The Cockpit component for creating diagnostic reports with sosreport.

%files sosreport -f sosreport.list
%license LICENSES/LGPL-2.1.txt
%{_datadir}/metainfo/org.cockpit_project.cockpit_sosreport.metainfo.xml
%{_datadir}/icons/hicolor/64x64/apps/cockpit-sosreport.png


%package networkmanager
Summary: Cockpit user interface for networking, using NetworkManager
Requires: cockpit-bridge >= %{required_base}
Requires: cockpit-shell >= %{required_base}
Requires: NetworkManager >= 1.6
Recommends: NetworkManager-team
BuildArch: noarch

%description networkmanager
The Cockpit component for managing networking. This package uses NetworkManager.

%files networkmanager -f networkmanager.list
%license LICENSES/LGPL-2.1.txt
%{_datadir}/metainfo/org.cockpit_project.cockpit_networkmanager.metainfo.xml


%package -n cockpit-storaged
Summary: Cockpit user interface for storage, using udisks
Requires: cockpit-shell >= %{required_base}
Requires: udisks2 >= 2.9
Recommends: udisks2-lvm2 >= 2.9
Recommends: udisks2-iscsi >= 2.9
Recommends: device-mapper-multipath
Recommends: clevis-luks
Requires: %{__python3}
Requires: python3-dbus
BuildArch: noarch

%description -n cockpit-storaged
The Cockpit component for managing storage. This package uses udisks.

%files -n cockpit-storaged -f storaged.list
%license LICENSES/LGPL-2.1.txt
%{_datadir}/metainfo/org.cockpit_project.cockpit_storaged.metainfo.xml

%post storaged
if [ "$1" = 2 ] && [ -d /var/lib/cockpit/btrfs ]; then
    rm -rf --one-file-system /var/lib/cockpit/btrfs || true
fi


%package -n cockpit-packagekit
Summary: Cockpit user interface for packages
BuildArch: noarch
Requires: cockpit-bridge >= %{required_base}
Requires: PackageKit
Recommends: python3-tracer
Requires: polkit

%description -n cockpit-packagekit
The Cockpit components for installing OS updates and Cockpit add-ons,
via PackageKit.

%files -n cockpit-packagekit -f packagekit.list
%license LICENSES/LGPL-2.1.txt


%if 0%{?omv} == 0

%package selinux
Summary: Cockpit SELinux package
Requires: cockpit-bridge >= %{required_base}
Requires: cockpit-shell >= %{required_base}
Requires: setroubleshoot-server >= 3.3.3
BuildArch: noarch

%description selinux
Cockpit user interface integration with setroubleshoot to diagnose and
resolve SELinux issues.

%files selinux -f selinux.list
%license LICENSES/LGPL-2.1.txt
%{_datadir}/metainfo/org.cockpit_project.cockpit_selinux.metainfo.xml


%define selinuxtype targeted

%package ws-selinux
Summary: SELinux security policy for cockpit-ws
Conflicts: %{name}-ws < 337-1.2025
Requires(post): selinux-policy-%{selinuxtype} >= %{_selinux_policy_version}
Requires(post): libselinux-utils
Requires(post): policycoreutils

%description ws-selinux
SELinux policy module for the cockpit-ws package.

%files ws-selinux
%license LICENSES/LGPL-2.1.txt
%{_datadir}/selinux/packages/%{selinuxtype}/%{name}.pp.bz2
%{_mandir}/man8/%{name}_session_selinux.8cockpit.*
%{_mandir}/man8/%{name}_ws_selinux.8cockpit.*
%ghost %{_selinux_store_path}/%{selinuxtype}/active/modules/200/%{name}

%pre ws-selinux
%selinux_relabel_pre -s %{selinuxtype}

%post ws-selinux
%selinux_modules_install -s %{selinuxtype} %{_datadir}/selinux/packages/%{selinuxtype}/%{name}.pp.bz2
%selinux_relabel_post -s %{selinuxtype}

%postun ws-selinux
%selinux_modules_uninstall -s %{selinuxtype} %{name}
%selinux_relabel_post -s %{selinuxtype}

%endif


%changelog
* Mon Jan 20 2025 OpenMandriva Association <http://openmandriva.org> - 360.1-1
- Initial OpenMandriva packaging, adapted from Fedora spec
- Disabled SELinux policy (not default on OpenMandriva)
- Adjusted BuildRequires for OpenMandriva package naming
- Skipped JS bundle rebuild (no nodejs-esbuild in repos yet)
