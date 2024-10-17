Summary:        A user interface for Linux servers
Name:		cockpit
Version:	0.90
Release:	2
License:	LGPLv2+
URL:		https://cockpit-project.org/
Group:		System/Servers
Source0:	https://github.com/cockpit-project/cockpit/releases/download/%{version}/%{name}-%{version}.tar.bz2
BuildRequires:	pkgconfig(gio-unix-2.0)
BuildRequires:	pkgconfig(json-glib-1.0)
BuildRequires:	pkgconfig(polkit-agent-1) >= 0.105
BuildRequires:	pam-devel
BuildRequires:	intltool
BuildRequires:	pkgconfig(libssh2) >= 0.7
BuildRequires:	openssl-devel
BuildRequires:	zlib-devel
BuildRequires:	krb5-devel
BuildRequires:	pkgconfig(libxslt)
BuildRequires:	docbook-style-xsl
BuildRequires:	keyutils-devel
BuildRequires:	glib-networking
BuildRequires:	pkgconfig(glib-2.0)
BuildRequires:	pkgconfig(systemd)
BuildRequires:	polkit
#BuildRequires:	pcp-libs-devel
BuildRequires:	gdb
BuildRequires:	xmlto

# Mandatory components of "cockpit"
Requires:	%{name}-bridge = %{EVRD}
Requires:	%{name}-ws = %{EVRD}
Requires:	%{name}-shell = %{EVRD}
Suggests:	%{name}-pcp = %{EVRD}
Suggests:	%{name}-kubernetes = %{EVRD}

%description
Cockpit runs in a browser and can manage your network of GNU/Linux
machines.

%package bridge
Summary:	Cockpit bridge server-side component
Provides:	%{name}-daemon
Requires:	polkit

%description bridge
The Cockpit bridge component installed server side and runs commands on the
system on behalf of the web based user interface.

%package doc
Summary: Cockpit deployment and developer guide

%description doc
The Cockpit Deployment and Developer Guide shows sysadmins how to
deploy Cockpit on their machines as well as helps developers who want to
embed or extend Cockpit.

%package pcp
Summary:	Cockpit PCP integration
Requires:	%{name}-bridge = %{EVRD}
Requires:	pcp

%description pcp
Cockpit support for reading PCP metrics and loading PCP archives.

%package ws
Summary:	Cockpit Web Service
Requires:	glib-networking
Requires:	openssl
Requires(post):	rpm-helper
Requires(preun):	rpm-helper
Requires(postun):	rpm-helper

%description ws
The Cockpit Web Service listens on the network, and authenticates users.

%package shell
Summary:	Cockpit Shell user interface package
Requires:	%{name}-bridge = %{version}-%{release}
Requires:	shadow
Requires:	grep
#Requires:	libpwquality
Provides:	%{name}-assets
BuildArch:	noarch

%description shell
This package contains the Cockpit shell UI assets.

%package sosreport
Summary:	Cockpit user interface for diagnostic reports
Requires:	sos
BuildArch:	noarch

%description sosreport
The Cockpit component for creating diagnostic reports with the
sosreport tool.

%package storaged
Summary:	Cockpit user interface for storage, using Storaged
#Requires:	storaged
#Requires:	storaged-lvm2
#Requires:	device-mapper-multipath
BuildArch:	noarch

%description storaged
The Cockpit component for managing storage.  This package uses Storaged.

%prep
%setup -q

%build
%configure \
	--disable-silent-rules
	--with-cockpit-user=cockpit-ws \
	--with-branding=default

%make all

%check
make check

%install
%makeinstall_std

rm -rf %{buildroot}%{_datadir}/%{name}/playground

mkdir -p %{buildroot}%{_sysconfdir}/pam.d
install -p -m 644 tools/cockpit.pam %{buildroot}%{_sysconfdir}/pam.d/cockpit
rm -f %{buildroot}/%{_libdir}/cockpit/*.so
install -p -m 644 AUTHORS COPYING README.md %{buildroot}%{_docdir}/%{name}/

# This is not yet packaged
rm -rf %{buildroot}%{_datadir}/%{name}/registry

# Build the package lists for resource packages
echo '%dir %{_datadir}/%{name}/base1' > shell.list
find %{buildroot}%{_datadir}/%{name}/base1 -type f >> shell.list

echo '%dir %{_datadir}/%{name}/dashboard' >> shell.list
find %{buildroot}%{_datadir}/%{name}/dashboard -type f >> shell.list

echo '%dir %{_datadir}/%{name}/domain' >> shell.list
find %{buildroot}%{_datadir}/%{name}/domain -type f >> shell.list

echo '%dir %{_datadir}/%{name}/shell' >> shell.list
find %{buildroot}%{_datadir}/%{name}/shell -type f >> shell.list

echo '%dir %{_datadir}/%{name}/system' >> shell.list
find %{buildroot}%{_datadir}/%{name}/system -type f >> shell.list

echo '%dir %{_datadir}/%{name}/users' >> shell.list
find %{buildroot}%{_datadir}/%{name}/users -type f >> shell.list

echo '%dir %{_datadir}/%{name}/sosreport' > sosreport.list
find %{buildroot}%{_datadir}/%{name}/sosreport -type f >> sosreport.list

echo '%dir %{_datadir}/%{name}/subscriptions' > subscriptions.list
find %{buildroot}%{_datadir}/%{name}/subscriptions -type f >> subscriptions.list

echo '%dir %{_datadir}/%{name}/storage' > storaged.list
find %{buildroot}%{_datadir}/%{name}/storage -type f >> storaged.list

echo '%dir %{_datadir}/%{name}/network' > networkmanager.list
find %{buildroot}%{_datadir}/%{name}/network -type f >> networkmanager.list

echo '%dir %{_datadir}/%{name}/ostree' > ostree.list
find %{buildroot}%{_datadir}/%{name}/ostree -type f >> ostree.list

# Not yet packaged
rm -rf %{buildroot}%{_datadir}/%{name}/tuned

%ifarch x86_64 armv7hl
echo '%dir %{_datadir}/%{name}/docker' > docker.list
find %{buildroot}%{_datadir}/%{name}/docker -type f >> docker.list
%else
rm -rf %{buildroot}/%{_datadir}/%{name}/docker
touch docker.list
%endif

%ifarch x86_64
echo '%dir %{_datadir}/%{name}/kubernetes' > kubernetes.list
find %{buildroot}%{_datadir}/%{name}/kubernetes -type f >> kubernetes.list
%else
rm -rf %{buildroot}/%{_datadir}/%{name}/kubernetes
touch kubernetes.list
%endif

sed -i "s|%{buildroot}||" *.list

# Build the package lists for debug package, and move debug files to installed locations
find %{buildroot}/usr/src/debug%{_datadir}/%{name} -type f -o -type l > debug.list
sed -i "s|%{buildroot}/usr/src/debug||" debug.list
tar -C %{buildroot}/usr/src/debug -cf - . | tar -C %{buildroot} -xf -
rm -rf %{buildroot}/usr/src/debug


%define find_debug_info %{_rpmconfigdir}/find-debuginfo.sh %{?_missing_build_ids_terminate_build:--strict-build-id} %{?_include_minidebuginfo:-m} %{?_find_debuginfo_dwz_opts} %{?_find_debuginfo_opts} "%{_builddir}/%{?buildsubdir}"

# Redefine how debug info is built to slip in our extra debug files
%define __debug_install_post   \
   %{find_debug_info} \
   cat debug.list >> %{_builddir}/%{?buildsubdir}/debugfiles.list \
%{nil}


%pre ws
getent group cockpit-ws >/dev/null || groupadd -r cockpit-ws
getent passwd cockpit-ws >/dev/null || useradd -r -g cockpit-ws -d / -s /sbin/nologin -c "User for cockpit-ws" cockpit-ws

%post ws
%systemd_post cockpit.socket
# firewalld only partially picks up changes to its services files without this
test -f %{_bindir}/firewall-cmd && firewall-cmd --reload --quiet || true

%preun ws
%systemd_preun cockpit.socket

%postun ws
%systemd_postun_with_restart cockpit.socket

%post pcp
( cd %{_localstatedir}/lib/pcp/pmns && ./Rebuild -du )
/usr/share/pcp/lib/pmlogger reload

%files
%doc AUTHORS COPYING README.md
%dir %{_datadir}/%{name}
%{_datadir}/appdata/cockpit.appdata.xml
%{_datadir}/applications/cockpit.desktop
%{_datadir}/pixmaps/cockpit.png
%{_mandir}/man1/cockpit.1.*

%files bridge

%{_bindir}/cockpit-bridge
%attr(4755, -, -) %{_libexecdir}/cockpit-polkit
%{_libdir}/security/pam_reauthorize.so
%{_mandir}/man1/cockpit-bridge.1.*

%files doc
%{_docdir}/%{name}

%files pcp
%{_libexecdir}/cockpit-pcp
%{_localstatedir}/lib/pcp/config/pmlogconf/tools/cockpit


%files ws

%config(noreplace) %{_sysconfdir}/%{name}
%config(noreplace) %{_sysconfdir}/pam.d/cockpit
%{_unitdir}/cockpit.service
%{_unitdir}/cockpit.socket
%{_prefix}/lib/firewalld/services/cockpit.xml
%{_sbindir}/remotectl
%{_libdir}/security/pam_ssh_add.so
%{_libexecdir}/cockpit-ws
%{_libexecdir}/cockpit-stub
%attr(4750, root, cockpit-ws) %{_libexecdir}/cockpit-session
%attr(775, -, wheel) %{_localstatedir}/lib/%{name}
%{_datadir}/%{name}/static
%{_datadir}/%{name}/branding
%{_mandir}/man5/cockpit.conf.5.*
%{_mandir}/man8/cockpit-ws.8.*
%{_mandir}/man8/remotectl.8.*
%{_mandir}/man8/pam_ssh_add.8.*

%files shell -f shell.list

%files sosreport -f sosreport.list

%files storaged -f storaged.list
