# MikroTik Internet Service Address Lists Exporter

[![Release](https://img.shields.io/github/v/release/didimozg/mikrotik-internet-address-lists?display_name=tag)](https://github.com/didimozg/mikrotik-internet-address-lists/releases)
[![CI](https://img.shields.io/github/actions/workflow/status/didimozg/mikrotik-internet-address-lists/ci.yml?branch=main&label=CI)](https://github.com/didimozg/mikrotik-internet-address-lists/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/didimozg/mikrotik-internet-address-lists)](./LICENSE)

Russian documentation: [README_RU.md](./README_RU.md).

Python utility that collects IP ranges and DNS-derived addresses for popular Internet services and generates MikroTik RouterOS `.rsc` import files.

> [!IMPORTANT]
> This project reflects the maintainer's own routing, VPN, and traffic-marking preferences.
> It is not an official product of Google, Meta, Telegram, OpenAI, GitHub, Microsoft, VK, TMDB, or Let's Encrypt.
> Validate the generated lists in your own environment before using them in production.

## Features

- build one combined `.rsc` file with all managed address lists
- build separate `.rsc` files per service list
- generate only selected lists when needed
- flush existing MikroTik entries by `address-list` name before reimport
- deduplicate, normalize, and aggregate adjacent networks
- combine official sources with community sources where official static ranges do not exist

## Supported Address Lists

| Address list | Purpose |
| --- | --- |
| `g_Google` | Google |
| `m_Meta` | Meta, Facebook, Instagram, and related services |
| `z_LE` | Let's Encrypt |
| `m_tmbd` | TMDB / The Movie Database |
| `t_telegram` | Telegram |
| `y_YouTube` | YouTube |
| `i_chatgpt` | ChatGPT / OpenAI |
| `i_GitHub_Copilot` | GitHub Copilot |
| `i_VSCode_Ext` | Visual Studio Code Marketplace and extension downloads |
| `v_VK` | VK and related ecosystem services |

## How It Works

1. The script pulls official JSON or `whois` data where available.
2. For services without official static ranges, it resolves domains through DNS over HTTPS.
3. Community GitHub sources can be used to enrich coverage with CIDRs, host lists, and ready-made MikroTik feeds.
4. The collected networks are normalized, deduplicated, stripped of nested subnets, and aggregated where safe.
5. The final result is exported as RouterOS-compatible `.rsc` files.

## Requirements

- Python 3.10+
- outbound Internet access
- MikroTik RouterOS for `.rsc` import
- no third-party Python dependencies

## Quick Start

By default, the script generates:

- `internet_mikrotik_import.rsc`
- per-list files in `internet_mikrotik_import_lists/`

Run:

```powershell
python .\internet_mikrotik_ip_export.py -FlushManagedEntries
```

Import the combined file into MikroTik:

```routeros
/import file-name=internet_mikrotik_import.rsc
```

Validate the import on RouterOS 7.16+:

```routeros
/import file-name=internet_mikrotik_import.rsc verbose=yes dry-run
```

## Common Examples

Combined output only:

```powershell
python .\internet_mikrotik_ip_export.py -OutputMode all -FlushManagedEntries
```

Per-list output only:

```powershell
python .\internet_mikrotik_ip_export.py -OutputMode per-list -FlushManagedEntries
```

Only one address list:

```powershell
python .\internet_mikrotik_ip_export.py -OutputMode per-list -OnlyAddressLists t_telegram -FlushManagedEntries
```

Only Google and Meta:

```powershell
python .\internet_mikrotik_ip_export.py -SkipLe -SkipTmdb -SkipTelegram -SkipYouTube -SkipChatGPT -SkipGitHubCopilot -SkipVSCodeExtensions -SkipVk -FlushManagedEntries
```

The script accepts both PowerShell-style parameters such as `-FlushManagedEntries` and GNU-style parameters such as `--flush-managed-entries`.

## Output

- `internet_mikrotik_import.rsc`: combined file with all managed address lists
- `internet_mikrotik_import_lists/*.rsc`: individual `.rsc` files per address list

## Customization

Most practical adjustments can be made in [config.json](./config.json):

- add or remove `hosts`
- define additional `source_urls`
- extend community inputs with `community_host_urls`, `community_rsc_urls`, or `community_cidr_urls`
- add `extra_cidrs`

If you need a brand new independent `address-list`, extend the default service configuration and CLI handling in [internet_mikrotik_ip_export.py](./internet_mikrotik_ip_export.py).

## Limitations

- some services do not publish official static IP ranges
- DNS-based snapshots can change between runs
- community sources may be noisy, stale, or intentionally broad
- CDN and shared address space can overlap between services
- exact traffic classification can be affected by DoH/DoT, ECH, and shared edge infrastructure

## Project Structure

- [internet_mikrotik_ip_export.py](./internet_mikrotik_ip_export.py): main Python exporter
- [config.json](./config.json): service configuration and community sources
- `internet_mikrotik_import.rsc`: combined output example
- `internet_mikrotik_import_lists/`: per-list output examples

## License

The repository's own code is distributed under the [MIT License](./LICENSE).
External data feeds, community lists, and upstream sources remain subject to their own terms.
