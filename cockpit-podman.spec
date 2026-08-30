# SPDX-License-Identifier: LGPL-2.1-or-later
# OpenMandriva adaptation

Name:           cockpit-podman
Version:        125
Release:        1%{?dist}
Summary:        Cockpit component for Podman containers
License:        LGPL-2.1-or-later
URL:            https://github.com/cockpit-project/cockpit-podman

%if 0%{?fedora} >= 42
%define rebuild_bundle 1
%endif

Source0: https://github.com/cockpit-project/%{name}/releases/download/%{version}/%{name}-%{version}.tar.xz
Source1: https://github.com/cockpit-project/%{name}/releases/download/%{version}/%{name}-node-%{version}.tar.xz

BuildArch:      noarch
BuildRequires:  libappstream-glib
BuildRequires:  make
BuildRequires:  gettext
%if %{defined rebuild_bundle}
BuildRequires:  /usr/bin/node
BuildRequires:  nodejs-esbuild
%endif

Requires:       cockpit-bridge
Requires:       podman >= 2.0.4

%description
The Cockpit user interface for Podman containers.

%prep
%setup -q -n %{name}
%if %{defined rebuild_bundle}
%setup -q -D -T -a 1 -n %{name}
%endif

%build
%if %{defined rebuild_bundle}
rm -rf dist
NODE_ENV=production NODE_PATH=/usr/lib/node_modules:$(echo /usr/lib/node_modules_*) ./build.js
%else
%endif

%install
%make_install PREFIX=/usr
appstream-util validate-relax --nonet %{buildroot}/%{_datadir}/metainfo/*

%files
%doc README.md
%license LICENSE dist/index.js.LEGAL.txt dist/index.css.LEGAL.txt
%{_datadir}/cockpit/*
%{_datadir}/metainfo/*

%changelog
* Mon Jan 20 2025 OpenMandriva Association <http://openmandriva.org> - 125-1
- Initial OpenMandriva packaging
