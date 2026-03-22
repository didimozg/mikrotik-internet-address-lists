from __future__ import annotations

import argparse
import ipaddress
import json
import re
import socket
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TypeVar


GOOGLE_SOURCE_MAP = {
    "goog": "https://www.gstatic.com/ipranges/goog.json",
    "cloud": "https://www.gstatic.com/ipranges/cloud.json",
    "googlebot": "https://www.gstatic.com/ipranges/googlebot.json",
}

MANAGED_TAG = "managed-by=internet-mikrotik-ip-export"
DEFAULT_DOH_URL = "https://dns.google/resolve"
DEFAULT_CONFIG_PATH = Path(__file__).with_name("config.json")

DEFAULT_LE_HOSTS = (
    "letsencrypt.org",
    "www.letsencrypt.org",
    "acme-v02.api.letsencrypt.org",
    "acme-staging-v02.api.letsencrypt.org",
)

DEFAULT_TMDB_HOSTS = (
    "www.themoviedb.org",
    "api.themoviedb.org",
    "image.tmdb.org",
)

DEFAULT_TELEGRAM_HOSTS = (
    "telegram.org",
    "core.telegram.org",
    "api.telegram.org",
    "gatewayapi.telegram.org",
    "web.telegram.org",
    "my.telegram.org",
    "desktop.telegram.org",
    "t.me",
    "telegram.me",
)

DEFAULT_YOUTUBE_HOSTS = (
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "youtu.be",
    "youtubei.googleapis.com",
    "youtube.googleapis.com",
    "www.youtube-nocookie.com",
    "www.youtubeeducation.com",
    "s.ytimg.com",
    "i.ytimg.com",
)

DEFAULT_CHATGPT_HOSTS = (
    "chatgpt.com",
    "chat.openai.com",
    "openai.com",
    "api.openai.com",
    "auth.openai.com",
    "setup.auth.openai.com",
    "oaistatic.com",
    "files.oaiusercontent.com",
    "android.chat.openai.com",
    "ios.chat.openai.com",
)

DEFAULT_GITHUB_COPILOT_HOSTS = (
    "github.com",
    "api.github.com",
    "copilot-proxy.githubusercontent.com",
    "origin-tracker.githubusercontent.com",
    "api.githubcopilot.com",
    "githubcopilot.com",
)

DEFAULT_VK_HOSTS = (
    "vk.com",
    "m.vk.com",
    "vk.ru",
    "api.vk.ru",
    "oauth.vk.ru",
    "id.vk.com",
)

TELEGRAM_PROXY_CONFIG_URLS = (
    "https://core.telegram.org/getProxyConfig",
    "https://core.telegram.org/getProxyConfigV6",
)
TELEGRAM_GITHUB_CIDR_URL = "https://raw.githubusercontent.com/fernvenue/telegram-cidr-list/master/CIDR.txt"

CHATGPT_CONNECTORS_URL = "https://openai.com/chatgpt-connectors.json"
CHATGPT_COMMUNITY_RSC_URL = "https://raw.githubusercontent.com/vogster/Mikrotik-Address-List/main/chatgpt.rcs"

LE_SOURCE_URLS = (
    "https://letsencrypt.org",
    "https://acme-v02.api.letsencrypt.org/directory",
)
LE_COMMUNITY_HOST_URLS = (
    "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/letsencrypt",
)

TMDB_SOURCE_URLS = (
    "https://developer.themoviedb.org/docs/search-and-query-for-details",
    "https://developer.themoviedb.org/reference/collection-images",
)
TMDB_COMMUNITY_HOST_URLS = (
    "https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Russia/inside-raw.lst",
)

TELEGRAM_SOURCE_URLS = (
    "https://core.telegram.org/gateway/api",
    "https://core.telegram.org/getProxyConfig",
    "https://core.telegram.org/getProxyConfigV6",
)
TELEGRAM_COMMUNITY_HOST_URLS = (
    "https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Services/telegram.lst",
)

YOUTUBE_SOURCE_URLS = (
    "https://support.google.com/a/answer/6214622?hl=en-US",
    "https://support.google.com/a/answer/9012184?hl=en-US",
    "https://knowledge.workspace.google.com/admin/security/firewall-and-proxy-settings?hl=en&visit_id=639092639852714062-1208261129&rd=1",
)
YOUTUBE_COMMUNITY_RSC_URL = "https://raw.githubusercontent.com/vogster/Mikrotik-Address-List/main/youtube.rcs"
YOUTUBE_COMMUNITY_HOST_URLS = (
    "https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Services/youtube.lst",
)

CHATGPT_SOURCE_URLS = (
    "https://help.openai.com/en/articles/9247338-network-recommendations-for-chatgpt-errors-on-web-and-apps",
    CHATGPT_CONNECTORS_URL,
)
CHATGPT_COMMUNITY_HOST_URLS = (
    "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/openai",
)

GITHUB_COPILOT_SOURCE_URLS = (
    "https://docs.github.com/en/enterprise-cloud@latest/copilot/reference/copilot-allowlist-reference",
    "https://docs.github.com/en/copilot/how-tos/troubleshoot-copilot/troubleshoot-network-errors",
)
GITHUB_COPILOT_COMMUNITY_HOST_URLS = (
    "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/github-copilot",
    "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/github",
)

VSCODE_EXTENSIONS_SOURCE_URLS = (
    "https://code.visualstudio.com/docs/setup/network",
)
VSCODE_EXTENSIONS_COMMUNITY_HOST_URLS = (
    "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/microsoft-dev",
)

VK_SOURCE_URLS = (
    "https://vk.com",
    "https://vk.ru",
    "https://id.vk.com",
)
VK_COMMUNITY_HOST_URLS = (
    "https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Ukraine/inside-raw.lst",
)

META_HELP_URL = "https://www.facebook.com/help/278069664862989"

LEGACY_ARG_ALIASES = {
    "-Sources": "--sources",
    "-OutputPath": "--output-path",
    "-ListsOutputDir": "--lists-output-dir",
    "-OutputMode": "--output-mode",
    "-OnlyAddressLists": "--only-address-lists",
    "-ConfigPath": "--config-path",
    "-IPv4ListName": "--ipv4-list-name",
    "-IPv6ListName": "--ipv6-list-name",
    "-MetaIPv4ListName": "--meta-ipv4-list-name",
    "-MetaIPv6ListName": "--meta-ipv6-list-name",
    "-LeIPv4ListName": "--le-ipv4-list-name",
    "-LeIPv6ListName": "--le-ipv6-list-name",
    "-TmdbIPv4ListName": "--tmdb-ipv4-list-name",
    "-TmdbIPv6ListName": "--tmdb-ipv6-list-name",
    "-TelegramIPv4ListName": "--telegram-ipv4-list-name",
    "-TelegramIPv6ListName": "--telegram-ipv6-list-name",
    "-YouTubeIPv4ListName": "--youtube-ipv4-list-name",
    "-YouTubeIPv6ListName": "--youtube-ipv6-list-name",
    "-ChatGPTIPv4ListName": "--chatgpt-ipv4-list-name",
    "-ChatGPTIPv6ListName": "--chatgpt-ipv6-list-name",
    "-GitHubCopilotIPv4ListName": "--github-copilot-ipv4-list-name",
    "-GitHubCopilotIPv6ListName": "--github-copilot-ipv6-list-name",
    "-VSCodeExtensionsIPv4ListName": "--vscode-extensions-ipv4-list-name",
    "-VSCodeExtensionsIPv6ListName": "--vscode-extensions-ipv6-list-name",
    "-VkIPv4ListName": "--vk-ipv4-list-name",
    "-VkIPv6ListName": "--vk-ipv6-list-name",
    "-MetaAsns": "--meta-asns",
    "-MetaWhoisServer": "--meta-whois-server",
    "-SkipMeta": "--skip-meta",
    "-SkipLe": "--skip-le",
    "-SkipTmdb": "--skip-tmdb",
    "-SkipTelegram": "--skip-telegram",
    "-SkipYouTube": "--skip-youtube",
    "-SkipChatGPT": "--skip-chatgpt",
    "-SkipGitHubCopilot": "--skip-github-copilot",
    "-SkipVSCodeExtensions": "--skip-vscode-extensions",
    "-SkipVk": "--skip-vk",
    "-IncludeIPv4": "--include-ipv4",
    "-IncludeIPv6": "--include-ipv6",
    "-SplitListBySource": "--split-list-by-source",
    "-CloudScopes": "--cloud-scopes",
    "-FlushManagedEntries": "--flush-managed-entries",
}


@dataclass(frozen=True)
class RawEntry:
    provider: str
    source: str
    family: str
    list_name: str
    network: ipaddress._BaseNetwork


@dataclass(frozen=True)
class FinalEntry:
    provider: str
    family: str
    list_name: str
    network: ipaddress._BaseNetwork
    source_count: int
    raw_count: int


SUMMARY_PROVIDERS = (
    ("Google", "google"),
    ("Meta", "meta"),
    ("Le", "le"),
    ("Tmdb", "tmdb"),
    ("Telegram", "telegram"),
    ("YouTube", "youtube"),
    ("ChatGPT", "chatgpt"),
    ("GitHubCopilot", "github_copilot"),
    ("VSCodeExt", "vscode_extensions"),
    ("Vk", "vk"),
)

EntryT = TypeVar("EntryT", RawEntry, FinalEntry)


def get_default_service_config() -> dict:
    return {
        "dns_resolver_url": DEFAULT_DOH_URL,
        "telegram_proxy_config_urls": list(TELEGRAM_PROXY_CONFIG_URLS),
        "services": {
            "le": {
                "hosts": list(DEFAULT_LE_HOSTS),
                "source_urls": list(LE_SOURCE_URLS),
                "community_host_urls": list(LE_COMMUNITY_HOST_URLS),
                "community_host_allow_patterns": [
                    r"^(lencr\.org|letsencrypt\.(org|com))$",
                ],
            },
            "tmdb": {
                "hosts": list(DEFAULT_TMDB_HOSTS),
                "source_urls": list(TMDB_SOURCE_URLS),
                "community_host_urls": list(TMDB_COMMUNITY_HOST_URLS),
                "community_host_allow_patterns": [
                    r"(^|\.)themoviedb\.org$",
                    r"(^|\.)tmdb\.org$",
                    r"(^|\.)tmdb\.com$",
                    r"(^|\.)tmdb-image-prod\.b-cdn\.net$",
                ],
            },
            "telegram": {
                "hosts": list(DEFAULT_TELEGRAM_HOSTS),
                "source_urls": list(TELEGRAM_SOURCE_URLS),
                "community_cidr_urls": [TELEGRAM_GITHUB_CIDR_URL],
                "community_host_urls": list(TELEGRAM_COMMUNITY_HOST_URLS),
                "community_host_allow_patterns": [
                    r"(^|\.)telegram\.org$",
                    r"(^|\.)core\.telegram\.org$",
                    r"(^|\.)api\.telegram\.org$",
                    r"(^|\.)gatewayapi\.telegram\.org$",
                    r"(^|\.)web\.telegram\.org$",
                    r"(^|\.)my\.telegram\.org$",
                    r"(^|\.)desktop\.telegram\.org$",
                    r"(^|\.)t\.me$",
                    r"(^|\.)telegram\.me$",
                    r"(^|\.)telegram-cdn\.org$",
                    r"(^|\.)cdn-telegram\.org$",
                    r"(^|\.)telegra\.ph$",
                    r"(^|\.)graph\.org$",
                    r"(^|\.)fragment\.com$",
                    r"(^|\.)contest\.com$",
                    r"(^|\.)telesco\.pe$",
                    r"(^|\.)tdesktop\.com$",
                    r"(^|\.)ton\.org$",
                    r"(^|\.)tx\.me$",
                ],
                "extra_cidrs": [
                    "95.161.64.0/20",
                    "5.28.192.0/18",
                ],
            },
            "youtube": {
                "hosts": list(DEFAULT_YOUTUBE_HOSTS),
                "source_urls": list(YOUTUBE_SOURCE_URLS),
                "community_rsc_urls": [YOUTUBE_COMMUNITY_RSC_URL],
                "community_host_urls": list(YOUTUBE_COMMUNITY_HOST_URLS),
                "community_host_allow_patterns": [
                    r"(^|\.)youtube\.com$",
                    r"(^|\.)youtu\.be$",
                    r"(^|\.)ytimg\.com$",
                    r"(^|\.)googlevideo\.com$",
                    r"(^|\.)youtubekids\.com$",
                    r"(^|\.)youtube-nocookie\.com$",
                    r"(^|\.)youtubei\.googleapis\.com$",
                    r"(^|\.)youtubeembeddedplayer\.googleapis\.com$",
                    r"(^|\.)yt3\.googleusercontent\.com$",
                ],
            },
            "chatgpt": {
                "hosts": list(DEFAULT_CHATGPT_HOSTS),
                "source_urls": ["https://help.openai.com/en/articles/9247338-network-recommendations-for-chatgpt-errors-on-web-and-apps"],
                "connector_url": CHATGPT_CONNECTORS_URL,
                "community_rsc_urls": [CHATGPT_COMMUNITY_RSC_URL],
                "community_host_urls": list(CHATGPT_COMMUNITY_HOST_URLS),
                "community_host_allow_patterns": [
                    r"(^|\.)chat\.com$",
                    r"(^|\.)chatgpt\.com$",
                    r"(^|\.)openai\.com$",
                    r"(^|\.)oaistatic\.com$",
                    r"(^|\.)oaiusercontent\.com$",
                    r"(^|\.)sora\.com$",
                    r"(^|\.)azureedge\.net$",
                    r"(^|\.)azurefd\.net$",
                    r"(^|\.)blob\.core\.windows\.net$",
                    r"(^|\.)livekit\.cloud$",
                ],
            },
            "github_copilot": {
                "hosts": list(DEFAULT_GITHUB_COPILOT_HOSTS),
                "source_urls": list(GITHUB_COPILOT_SOURCE_URLS),
                "community_host_urls": list(GITHUB_COPILOT_COMMUNITY_HOST_URLS),
                "community_host_allow_patterns": [
                    r"(^|\.)githubcopilot\.com$",
                    r"(^|\.)github\.com$",
                    r"(^|\.)api\.github\.com$",
                    r"(^|\.)githubassets\.com$",
                    r"(^|\.)githubusercontent\.com$",
                    r"(^|\.)githubapp\.com$",
                    r"(^|\.)github\.dev$",
                ],
            },
            "vscode_extensions": {
                "hosts": [
                    "marketplace.visualstudio.com",
                    "go.microsoft.com",
                    "raw.githubusercontent.com",
                    "vsmarketplacebadges.dev",
                    "vscode.download.prss.microsoft.com",
                    "download.visualstudio.microsoft.com",
                    "vscode.dev",
                    "update.code.visualstudio.com",
                ],
                "source_urls": list(VSCODE_EXTENSIONS_SOURCE_URLS),
                "community_host_urls": list(VSCODE_EXTENSIONS_COMMUNITY_HOST_URLS),
                "community_host_allow_patterns": [
                    r"(^|\.)visualstudio\.com$",
                    r"(^|\.)vsassets\.io$",
                    r"(^|\.)vscode\.dev$",
                    r"(^|\.)vscode-cdn\.net$",
                    r"(^|\.)vscode-unpkg\.net$",
                    r"(^|\.)download\.visualstudio\.microsoft\.com$",
                    r"(^|\.)vscode\.download\.prss\.microsoft\.com$",
                ],
            },
            "vk": {
                "hosts": list(DEFAULT_VK_HOSTS),
                "source_urls": list(VK_SOURCE_URLS),
                "community_host_urls": list(VK_COMMUNITY_HOST_URLS),
                "community_host_allow_patterns": [
                    r"(^|\.)vk\.com$",
                    r"(^|\.)vk\.ru$",
                    r"(^|\.)vkvideo\.ru$",
                    r"(^|\.)video\.vk\.com$",
                    r"(^|\.)clips\.vk\.com$",
                    r"(^|\.)music\.vk\.com$",
                    r"(^|\.)id\.vk\.com$",
                    r"(^|\.)oauth\.vk\.ru$",
                    r"(^|\.)api\.vk\.ru$",
                    r"(^|\.)vkontakte\.ru$",
                    r"(^|\.)vkforms\.ru$",
                    r"(^|\.)vk-apps\.com$",
                    r"(^|\.)vkplay\.live$",
                    r"(^|\.)ok\.ru$",
                    r"(^|\.)mail\.ru$",
                ],
            },
        },
    }


def ensure_string_list(value: object, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise RuntimeError(f"Поле {field_name} должно быть непустым массивом строк.")

    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise RuntimeError(f"Поле {field_name} должно содержать только непустые строки.")
        result.append(item.strip())
    return tuple(result)


def load_service_config(path: Path) -> dict:
    if not path.exists():
        default_config = json.dumps(get_default_service_config(), indent=2) + "\n"
        path.write_text(default_config, encoding="ascii")
        print(f"Создан config по умолчанию: {path}")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Некорректный JSON в config-файле {path}: {exc}") from exc

    if not isinstance(payload, dict):
        raise RuntimeError(f"Config-файл {path} должен содержать JSON-объект.")

    resolver_url = payload.get("dns_resolver_url")
    if not isinstance(resolver_url, str) or not resolver_url.strip():
        raise RuntimeError(f"Поле dns_resolver_url в {path} должно быть непустой строкой.")

    telegram_proxy_config_urls = ensure_string_list(
        payload.get("telegram_proxy_config_urls"),
        "telegram_proxy_config_urls",
    )

    services = payload.get("services")
    if not isinstance(services, dict):
        raise RuntimeError(f"Поле services в {path} должно быть JSON-объектом.")

    validated_services: dict[str, dict[str, object]] = {}
    required_services = ("le", "tmdb", "telegram", "youtube", "chatgpt", "github_copilot", "vscode_extensions", "vk")
    for service_name in required_services:
        profile = services.get(service_name)
        if not isinstance(profile, dict):
            raise RuntimeError(f"В config-файле {path} отсутствует блок services.{service_name}.")

        hosts = ensure_string_list(profile.get("hosts"), f"services.{service_name}.hosts")
        source_urls = ensure_string_list(profile.get("source_urls"), f"services.{service_name}.source_urls")

        validated_profile: dict[str, object] = {
            "hosts": hosts,
            "source_urls": source_urls,
        }

        connector_url = profile.get("connector_url")
        if service_name == "chatgpt" and connector_url is None:
            raise RuntimeError(f"Поле services.{service_name}.connector_url обязательно в config-файле {path}.")
        if connector_url is not None:
            if not isinstance(connector_url, str) or not connector_url.strip():
                raise RuntimeError(f"Поле services.{service_name}.connector_url должно быть непустой строкой.")
            validated_profile["connector_url"] = connector_url.strip()

        community_rsc_urls = profile.get("community_rsc_urls")
        if community_rsc_urls is not None:
            validated_profile["community_rsc_urls"] = ensure_string_list(
                community_rsc_urls,
                f"services.{service_name}.community_rsc_urls",
            )

        community_cidr_urls = profile.get("community_cidr_urls")
        if community_cidr_urls is not None:
            validated_profile["community_cidr_urls"] = ensure_string_list(
                community_cidr_urls,
                f"services.{service_name}.community_cidr_urls",
            )

        community_host_urls = profile.get("community_host_urls")
        if community_host_urls is not None:
            validated_profile["community_host_urls"] = ensure_string_list(
                community_host_urls,
                f"services.{service_name}.community_host_urls",
            )

        community_host_allow_patterns = profile.get("community_host_allow_patterns")
        if community_host_allow_patterns is not None:
            validated_profile["community_host_allow_patterns"] = ensure_string_list(
                community_host_allow_patterns,
                f"services.{service_name}.community_host_allow_patterns",
            )

        extra_cidrs = profile.get("extra_cidrs")
        if extra_cidrs is not None:
            validated_profile["extra_cidrs"] = ensure_string_list(
                extra_cidrs,
                f"services.{service_name}.extra_cidrs",
            )

        validated_services[service_name] = validated_profile

    return {
        "dns_resolver_url": resolver_url.strip(),
        "telegram_proxy_config_urls": telegram_proxy_config_urls,
        "services": validated_services,
    }


def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)


def fetch_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read().decode("utf-8", "replace")


def query_whois(server: str, query: str) -> str:
    with socket.create_connection((server, 43), timeout=30) as sock:
        sock.sendall((query + "\r\n").encode("ascii"))
        chunks: list[bytes] = []
        while True:
            data = sock.recv(65535)
            if not data:
                break
            chunks.append(data)
    return b"".join(chunks).decode("utf-8", "replace")


def resolve_public_ips(hostname: str, want_ipv4: bool, want_ipv6: bool, resolver_url: str) -> list[ipaddress._BaseAddress]:
    addresses: set[ipaddress._BaseAddress] = set()
    query_types: list[str] = []
    if want_ipv4:
        query_types.append("A")
    if want_ipv6:
        query_types.append("AAAA")

    for query_type in query_types:
        url = resolver_url + "?" + urllib.parse.urlencode({"name": hostname, "type": query_type})
        try:
            payload = fetch_json(url)
        except Exception:
            payload = {}

        for answer in payload.get("Answer", []):
            if answer.get("type") not in (1, 28):
                continue

            try:
                address = ipaddress.ip_address(answer["data"])
            except ValueError:
                continue

            if address.is_global:
                addresses.add(address)

    if addresses:
        return sorted(addresses, key=lambda item: (item.version, int(item)))

    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return []

    for info in infos:
        try:
            address = ipaddress.ip_address(info[4][0])
        except ValueError:
            continue

        if address.version == 4 and not want_ipv4:
            continue
        if address.version == 6 and not want_ipv6:
            continue
        if address.is_global:
            addresses.add(address)

    return sorted(addresses, key=lambda item: (item.version, int(item)))


def networks_from_addresses(addresses: list[ipaddress._BaseAddress]) -> list[ipaddress._BaseNetwork]:
    networks: list[ipaddress._BaseNetwork] = []
    for address in addresses:
        prefix_length = 32 if address.version == 4 else 128
        networks.append(ipaddress.ip_network(f"{address}/{prefix_length}", strict=False))
    return networks


def get_google_entries(args: argparse.Namespace) -> tuple[list[RawEntry], list[str]]:
    entries: list[RawEntry] = []
    header_lines: list[str] = []

    for source in args.sources:
        source_url = GOOGLE_SOURCE_MAP[source]
        print(f"Загрузка {source} из {source_url}")
        payload = fetch_json(source_url)

        header_lines.append(f"# Google source {source}: {source_url}")
        header_lines.append(f"# Google source {source} creationTime: {payload.get('creationTime', '')}")
        header_lines.append(f"# Google source {source} syncToken: {payload.get('syncToken', '')}")

        prefixes = payload.get("prefixes", [])
        if source == "cloud" and args.cloud_scopes:
            allowed_scopes = set(args.cloud_scopes)
            prefixes = [item for item in prefixes if item.get("scope") in allowed_scopes]

        for prefix in prefixes:
            list_name_v4 = args.ipv4_list_name if not args.split_list_by_source else f"{args.ipv4_list_name}_{source.upper()}"
            list_name_v6 = args.ipv6_list_name if not args.split_list_by_source else f"{args.ipv6_list_name}_{source.upper()}"

            if args.include_ipv4 and prefix.get("ipv4Prefix"):
                entries.append(
                    RawEntry(
                        provider="google",
                        source=source,
                        family="ipv4",
                        list_name=list_name_v4,
                        network=ipaddress.ip_network(prefix["ipv4Prefix"], strict=False),
                    )
                )

            if args.include_ipv6 and prefix.get("ipv6Prefix"):
                entries.append(
                    RawEntry(
                        provider="google",
                        source=source,
                        family="ipv6",
                        list_name=list_name_v6,
                        network=ipaddress.ip_network(prefix["ipv6Prefix"], strict=False),
                    )
                )

    if args.cloud_scopes:
        header_lines.append("# Cloud scopes filter: " + ", ".join(sorted(set(args.cloud_scopes))))

    return entries, header_lines


def get_meta_entries(args: argparse.Namespace) -> tuple[list[RawEntry], list[str]]:
    if args.skip_meta:
        return [], []

    entries: list[RawEntry] = []
    asns = sorted(set(args.meta_asns))
    retrieved_at = datetime.now().astimezone().isoformat(sep=" ", timespec="seconds")

    for asn in asns:
        query = f"-i origin {asn}"
        print(f"Загрузка meta из {args.meta_whois_server} по запросу {query}")
        response = query_whois(args.meta_whois_server, query)

        for line in response.splitlines():
            match_v4 = re.match(r"^\s*route:\s*(\S+)", line)
            match_v6 = re.match(r"^\s*route6:\s*(\S+)", line)

            if args.include_ipv4 and match_v4:
                entries.append(
                    RawEntry(
                        provider="meta",
                        source=asn,
                        family="ipv4",
                        list_name=args.meta_ipv4_list_name,
                        network=ipaddress.ip_network(match_v4.group(1), strict=False),
                    )
                )

            if args.include_ipv6 and match_v6:
                entries.append(
                    RawEntry(
                        provider="meta",
                        source=asn,
                        family="ipv6",
                        list_name=args.meta_ipv6_list_name,
                        network=ipaddress.ip_network(match_v6.group(1), strict=False),
                    )
                )

    if not entries:
        raise RuntimeError("Не удалось получить ни одного префикса Meta.")

    header_lines = [
        f"# Meta help: {META_HELP_URL}",
        f"# Meta whois server: {args.meta_whois_server}",
        "# Meta ASN query: " + ", ".join(asns),
        f"# Meta retrieved at: {retrieved_at}",
    ]
    return entries, header_lines


def resolve_dns_profile(
    provider: str,
    source: str,
    hosts: tuple[str, ...],
    resolver_url: str,
    list_name_v4: str,
    list_name_v6: str,
    want_ipv4: bool,
    want_ipv6: bool,
) -> list[RawEntry]:
    entries: list[RawEntry] = []

    for host in hosts:
        print(f"Резолв {provider} host {host} через DNS over HTTPS")
        addresses = resolve_public_ips(host, want_ipv4, want_ipv6, resolver_url)
        if not addresses:
            print(f"Предупреждение: не удалось получить публичные IP для {host}", file=sys.stderr)
            continue

        for network in networks_from_addresses(addresses):
            list_name = list_name_v4 if network.version == 4 else list_name_v6
            family = "ipv4" if network.version == 4 else "ipv6"
            entries.append(
                RawEntry(
                    provider=provider,
                    source=source,
                    family=family,
                    list_name=list_name,
                    network=network,
                )
            )

    return entries


def parse_telegram_proxy_config(args: argparse.Namespace) -> list[RawEntry]:
    entries: list[RawEntry] = []

    proxy_config_urls = args.service_config["telegram_proxy_config_urls"]
    for url in proxy_config_urls:
        print(f"Загрузка telegram proxy config из {url}")
        content = fetch_text(url)
        for line in content.splitlines():
            match = re.search(r"proxy_for\s+\S+\s+\[?([0-9a-fA-F\.:]+)\]?:\d+;", line)
            if not match:
                continue

            address = ipaddress.ip_address(match.group(1))
            if address.version == 4 and not args.include_ipv4:
                continue
            if address.version == 6 and not args.include_ipv6:
                continue
            if not address.is_global:
                continue

            prefix_length = 32 if address.version == 4 else 128
            network = ipaddress.ip_network(f"{address}/{prefix_length}", strict=False)
            list_name = args.telegram_ipv4_list_name if address.version == 4 else args.telegram_ipv6_list_name
            family = "ipv4" if address.version == 4 else "ipv6"
            entries.append(
                RawEntry(
                    provider="telegram",
                    source="telegram_proxy_config",
                    family=family,
                    list_name=list_name,
                    network=network,
                )
            )

    return entries


def get_chatgpt_connector_entries(args: argparse.Namespace, connector_url: str) -> tuple[list[RawEntry], list[str]]:
    print(f"Загрузка ChatGPT connectors из {connector_url}")

    try:
        payload = fetch_json(connector_url)
    except Exception as exc:
        print(f"Предупреждение: не удалось загрузить ChatGPT connectors: {exc}", file=sys.stderr)
        return (
            [],
            [
                f"# ChatGPT connectors source: {connector_url}",
                f"# ChatGPT connectors error: {exc}",
            ],
        )

    entries: list[RawEntry] = []
    for prefix in payload.get("prefixes", []):
        if args.include_ipv4 and prefix.get("ipv4Prefix"):
            entries.append(
                RawEntry(
                    provider="chatgpt",
                    source="chatgpt_connectors",
                    family="ipv4",
                    list_name=args.chatgpt_ipv4_list_name,
                    network=ipaddress.ip_network(prefix["ipv4Prefix"], strict=False),
                )
            )

        if args.include_ipv6 and prefix.get("ipv6Prefix"):
            entries.append(
                RawEntry(
                    provider="chatgpt",
                    source="chatgpt_connectors",
                    family="ipv6",
                    list_name=args.chatgpt_ipv6_list_name,
                    network=ipaddress.ip_network(prefix["ipv6Prefix"], strict=False),
                )
            )

    header_lines = [
        f"# ChatGPT connectors source: {connector_url}",
        f"# ChatGPT connectors creationTime: {payload.get('creationTime', '')}",
    ]
    if payload.get("syncToken"):
        header_lines.append(f"# ChatGPT connectors syncToken: {payload.get('syncToken', '')}")

    return entries, header_lines


def get_rsc_source_entries(
    provider: str,
    source: str,
    source_url: str,
    list_name_v4: str,
    list_name_v6: str,
    want_ipv4: bool,
    want_ipv6: bool,
) -> tuple[list[RawEntry], list[str]]:
    print(f"Загрузка {provider} rsc source из {source_url}")

    try:
        content = fetch_text(source_url)
    except Exception as exc:
        print(f"Предупреждение: не удалось загрузить {provider} rsc source: {exc}", file=sys.stderr)
        return [], [f"# {provider} rsc source: {source_url}", f"# {provider} rsc error: {exc}"]

    entries: list[RawEntry] = []
    for line in content.splitlines():
        match = re.search(r"\baddress=([0-9a-fA-F\.:/]+)", line)
        if not match:
            continue

        try:
            network = ipaddress.ip_network(match.group(1), strict=False)
        except ValueError:
            continue

        if network.version == 4 and not want_ipv4:
            continue
        if network.version == 6 and not want_ipv6:
            continue

        list_name = list_name_v4 if network.version == 4 else list_name_v6
        family = "ipv4" if network.version == 4 else "ipv6"
        entries.append(
            RawEntry(
                provider=provider,
                source=source,
                family=family,
                list_name=list_name,
                network=network,
            )
        )

    return entries, [f"# {provider} rsc source: {source_url}"]


def get_cidr_text_source_entries(
    provider: str,
    source: str,
    source_url: str,
    list_name_v4: str,
    list_name_v6: str,
    want_ipv4: bool,
    want_ipv6: bool,
) -> tuple[list[RawEntry], list[str]]:
    print(f"Загрузка {provider} cidr source из {source_url}")

    try:
        content = fetch_text(source_url)
    except Exception as exc:
        print(f"Предупреждение: не удалось загрузить {provider} cidr source: {exc}", file=sys.stderr)
        return [], [f"# {provider} cidr source: {source_url}", f"# {provider} cidr error: {exc}"]

    entries: list[RawEntry] = []
    for token in re.findall(r"[0-9a-fA-F\.:]+/\d{1,3}", content):
        try:
            network = ipaddress.ip_network(token, strict=False)
        except ValueError:
            continue

        if network.version == 4 and not want_ipv4:
            continue
        if network.version == 6 and not want_ipv6:
            continue

        list_name = list_name_v4 if network.version == 4 else list_name_v6
        family = "ipv4" if network.version == 4 else "ipv6"
        entries.append(
            RawEntry(
                provider=provider,
                source=source,
                family=family,
                list_name=list_name,
                network=network,
            )
        )

    return entries, [f"# {provider} cidr source: {source_url}"]


def extract_host_candidates(content: str, allow_patterns: tuple[str, ...]) -> tuple[str, ...]:
    compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in allow_patterns]
    hosts: list[str] = []
    seen: set[str] = set()

    for raw_line in content.splitlines():
        if "@ads" in raw_line:
            continue
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue

        token = line.split()[0].strip()
        if not token:
            continue

        if ":" in token:
            prefix, value = token.split(":", 1)
            if prefix not in {"full", "domain", "host"}:
                continue
            candidate = value.strip()
        else:
            candidate = token

        candidate = candidate.lower().rstrip(".")
        if "." not in candidate:
            continue
        if not re.fullmatch(r"[a-z0-9.-]+", candidate):
            continue
        if candidate.startswith(".") or ".." in candidate:
            continue
        if compiled_patterns and not any(pattern.search(candidate) for pattern in compiled_patterns):
            continue
        if candidate in seen:
            continue

        seen.add(candidate)
        hosts.append(candidate)

    return tuple(hosts)


def get_host_text_source_entries(
    provider: str,
    source: str,
    source_url: str,
    resolver_url: str,
    list_name_v4: str,
    list_name_v6: str,
    want_ipv4: bool,
    want_ipv6: bool,
    allow_patterns: tuple[str, ...],
) -> tuple[list[RawEntry], list[str]]:
    print(f"Загрузка {provider} host source из {source_url}")

    try:
        content = fetch_text(source_url)
    except Exception as exc:
        print(f"Предупреждение: не удалось загрузить {provider} host source: {exc}", file=sys.stderr)
        return [], [f"# {provider} host source: {source_url}", f"# {provider} host error: {exc}"]

    hosts = extract_host_candidates(content, allow_patterns)
    if not hosts:
        return [], [f"# {provider} host source: {source_url}", f"# {provider} host extracted-hosts: 0"]

    entries = resolve_dns_profile(
        provider=provider,
        source=source,
        hosts=hosts,
        resolver_url=resolver_url,
        list_name_v4=list_name_v4,
        list_name_v6=list_name_v6,
        want_ipv4=want_ipv4,
        want_ipv6=want_ipv6,
    )

    header_lines = [
        f"# {provider} host source: {source_url}",
        f"# {provider} host extracted-hosts: {len(hosts)}",
    ]
    if allow_patterns:
        header_lines.append(f"# {provider} host filters: {', '.join(allow_patterns)}")

    return entries, header_lines


def get_direct_cidr_entries(
    provider: str,
    source: str,
    cidrs: tuple[str, ...],
    list_name_v4: str,
    list_name_v6: str,
    want_ipv4: bool,
    want_ipv6: bool,
) -> list[RawEntry]:
    entries: list[RawEntry] = []
    for cidr in cidrs:
        network = ipaddress.ip_network(cidr, strict=False)
        if network.version == 4 and not want_ipv4:
            continue
        if network.version == 6 and not want_ipv6:
            continue

        list_name = list_name_v4 if network.version == 4 else list_name_v6
        family = "ipv4" if network.version == 4 else "ipv6"
        entries.append(
            RawEntry(
                provider=provider,
                source=source,
                family=family,
                list_name=list_name,
                network=network,
            )
        )
    return entries


def append_profile_community_sources(
    entries: list[RawEntry],
    header_lines: list[str],
    profile: dict[str, object],
    provider: str,
    list_name_v4: str,
    list_name_v6: str,
    resolver_url: str,
    want_ipv4: bool,
    want_ipv6: bool,
) -> None:
    for community_cidr_url in profile.get("community_cidr_urls", ()):
        cidr_entries, cidr_headers = get_cidr_text_source_entries(
            provider=provider,
            source=f"{provider}_community_cidr",
            source_url=community_cidr_url,
            list_name_v4=list_name_v4,
            list_name_v6=list_name_v6,
            want_ipv4=want_ipv4,
            want_ipv6=want_ipv6,
        )
        entries.extend(cidr_entries)
        header_lines.extend(cidr_headers)

    for community_rsc_url in profile.get("community_rsc_urls", ()):
        rsc_entries, rsc_headers = get_rsc_source_entries(
            provider=provider,
            source=f"{provider}_community_rsc",
            source_url=community_rsc_url,
            list_name_v4=list_name_v4,
            list_name_v6=list_name_v6,
            want_ipv4=want_ipv4,
            want_ipv6=want_ipv6,
        )
        entries.extend(rsc_entries)
        header_lines.extend(rsc_headers)

    allow_patterns = profile.get("community_host_allow_patterns", ())
    for community_host_url in profile.get("community_host_urls", ()):
        host_entries, host_headers = get_host_text_source_entries(
            provider=provider,
            source=f"{provider}_community_hosts",
            source_url=community_host_url,
            resolver_url=resolver_url,
            list_name_v4=list_name_v4,
            list_name_v6=list_name_v6,
            want_ipv4=want_ipv4,
            want_ipv6=want_ipv6,
            allow_patterns=allow_patterns,
        )
        entries.extend(host_entries)
        header_lines.extend(host_headers)

    extra_cidrs = profile.get("extra_cidrs", ())
    if extra_cidrs:
        entries.extend(
            get_direct_cidr_entries(
                provider=provider,
                source=f"{provider}_extra_cidrs",
                cidrs=extra_cidrs,
                list_name_v4=list_name_v4,
                list_name_v6=list_name_v6,
                want_ipv4=want_ipv4,
                want_ipv6=want_ipv6,
            )
        )
        header_lines.append(f"# {provider} extra CIDRs: " + ", ".join(extra_cidrs))


def get_service_entries(args: argparse.Namespace) -> tuple[list[RawEntry], list[str]]:
    service_config = args.service_config
    profiles = service_config["services"]
    resolver_url = service_config["dns_resolver_url"]
    entries: list[RawEntry] = []
    header_lines = [f"# DNS over HTTPS resolver: {resolver_url}"]

    if not args.skip_le:
        profile = profiles["le"]
        append_profile_community_sources(
            entries=entries,
            header_lines=header_lines,
            profile=profile,
            provider="le",
            list_name_v4=args.le_ipv4_list_name,
            list_name_v6=args.le_ipv6_list_name,
            resolver_url=resolver_url,
            want_ipv4=args.include_ipv4,
            want_ipv6=args.include_ipv6,
        )
        entries.extend(
            resolve_dns_profile(
                provider="le",
                source="le_dns",
                hosts=profile["hosts"],
                resolver_url=resolver_url,
                list_name_v4=args.le_ipv4_list_name,
                list_name_v6=args.le_ipv6_list_name,
                want_ipv4=args.include_ipv4,
                want_ipv6=args.include_ipv6,
            )
        )
        header_lines.append("# LE hosts: " + ", ".join(profile["hosts"]))
        for url in profile["source_urls"]:
            header_lines.append(f"# LE source: {url}")

    if not args.skip_tmdb:
        profile = profiles["tmdb"]
        append_profile_community_sources(
            entries=entries,
            header_lines=header_lines,
            profile=profile,
            provider="tmdb",
            list_name_v4=args.tmdb_ipv4_list_name,
            list_name_v6=args.tmdb_ipv6_list_name,
            resolver_url=resolver_url,
            want_ipv4=args.include_ipv4,
            want_ipv6=args.include_ipv6,
        )
        entries.extend(
            resolve_dns_profile(
                provider="tmdb",
                source="tmdb_dns",
                hosts=profile["hosts"],
                resolver_url=resolver_url,
                list_name_v4=args.tmdb_ipv4_list_name,
                list_name_v6=args.tmdb_ipv6_list_name,
                want_ipv4=args.include_ipv4,
                want_ipv6=args.include_ipv6,
            )
        )
        header_lines.append("# TMDB hosts: " + ", ".join(profile["hosts"]))
        for url in profile["source_urls"]:
            header_lines.append(f"# TMDB source: {url}")

    if not args.skip_telegram:
        profile = profiles["telegram"]
        append_profile_community_sources(
            entries=entries,
            header_lines=header_lines,
            profile=profile,
            provider="telegram",
            list_name_v4=args.telegram_ipv4_list_name,
            list_name_v6=args.telegram_ipv6_list_name,
            resolver_url=resolver_url,
            want_ipv4=args.include_ipv4,
            want_ipv6=args.include_ipv6,
        )

        entries.extend(
            resolve_dns_profile(
                provider="telegram",
                source="telegram_dns",
                hosts=profile["hosts"],
                resolver_url=resolver_url,
                list_name_v4=args.telegram_ipv4_list_name,
                list_name_v6=args.telegram_ipv6_list_name,
                want_ipv4=args.include_ipv4,
                want_ipv6=args.include_ipv6,
            )
        )
        entries.extend(parse_telegram_proxy_config(args))
        header_lines.append("# Telegram hosts: " + ", ".join(profile["hosts"]))
        for url in profile["source_urls"]:
            header_lines.append(f"# Telegram source: {url}")

    if not args.skip_youtube:
        profile = profiles["youtube"]
        append_profile_community_sources(
            entries=entries,
            header_lines=header_lines,
            profile=profile,
            provider="youtube",
            list_name_v4=args.youtube_ipv4_list_name,
            list_name_v6=args.youtube_ipv6_list_name,
            resolver_url=resolver_url,
            want_ipv4=args.include_ipv4,
            want_ipv6=args.include_ipv6,
        )
        entries.extend(
            resolve_dns_profile(
                provider="youtube",
                source="youtube_dns",
                hosts=profile["hosts"],
                resolver_url=resolver_url,
                list_name_v4=args.youtube_ipv4_list_name,
                list_name_v6=args.youtube_ipv6_list_name,
                want_ipv4=args.include_ipv4,
                want_ipv6=args.include_ipv6,
            )
        )
        header_lines.append("# YouTube hosts: " + ", ".join(profile["hosts"]))
        for url in profile["source_urls"]:
            header_lines.append(f"# YouTube source: {url}")

    if not args.skip_chatgpt:
        profile = profiles["chatgpt"]
        append_profile_community_sources(
            entries=entries,
            header_lines=header_lines,
            profile=profile,
            provider="chatgpt",
            list_name_v4=args.chatgpt_ipv4_list_name,
            list_name_v6=args.chatgpt_ipv6_list_name,
            resolver_url=resolver_url,
            want_ipv4=args.include_ipv4,
            want_ipv6=args.include_ipv6,
        )

        chatgpt_connector_entries, chatgpt_connector_headers = get_chatgpt_connector_entries(
            args,
            profile["connector_url"],
        )
        entries.extend(chatgpt_connector_entries)
        header_lines.extend(chatgpt_connector_headers)
        entries.extend(
            resolve_dns_profile(
                provider="chatgpt",
                source="chatgpt_dns",
                hosts=profile["hosts"],
                resolver_url=resolver_url,
                list_name_v4=args.chatgpt_ipv4_list_name,
                list_name_v6=args.chatgpt_ipv6_list_name,
                want_ipv4=args.include_ipv4,
                want_ipv6=args.include_ipv6,
            )
        )
        header_lines.append("# ChatGPT hosts: " + ", ".join(profile["hosts"]))
        for url in profile["source_urls"]:
            header_lines.append(f"# ChatGPT source: {url}")

    if not args.skip_github_copilot:
        profile = profiles["github_copilot"]
        append_profile_community_sources(
            entries=entries,
            header_lines=header_lines,
            profile=profile,
            provider="github_copilot",
            list_name_v4=args.github_copilot_ipv4_list_name,
            list_name_v6=args.github_copilot_ipv6_list_name,
            resolver_url=resolver_url,
            want_ipv4=args.include_ipv4,
            want_ipv6=args.include_ipv6,
        )
        entries.extend(
            resolve_dns_profile(
                provider="github_copilot",
                source="github_copilot_dns",
                hosts=profile["hosts"],
                resolver_url=resolver_url,
                list_name_v4=args.github_copilot_ipv4_list_name,
                list_name_v6=args.github_copilot_ipv6_list_name,
                want_ipv4=args.include_ipv4,
                want_ipv6=args.include_ipv6,
            )
        )
        header_lines.append("# GitHub Copilot hosts: " + ", ".join(profile["hosts"]))
        for url in profile["source_urls"]:
            header_lines.append(f"# GitHub Copilot source: {url}")

    if not args.skip_vscode_extensions:
        profile = profiles["vscode_extensions"]
        append_profile_community_sources(
            entries=entries,
            header_lines=header_lines,
            profile=profile,
            provider="vscode_extensions",
            list_name_v4=args.vscode_extensions_ipv4_list_name,
            list_name_v6=args.vscode_extensions_ipv6_list_name,
            resolver_url=resolver_url,
            want_ipv4=args.include_ipv4,
            want_ipv6=args.include_ipv6,
        )
        entries.extend(
            resolve_dns_profile(
                provider="vscode_extensions",
                source="vscode_extensions_dns",
                hosts=profile["hosts"],
                resolver_url=resolver_url,
                list_name_v4=args.vscode_extensions_ipv4_list_name,
                list_name_v6=args.vscode_extensions_ipv6_list_name,
                want_ipv4=args.include_ipv4,
                want_ipv6=args.include_ipv6,
            )
        )
        header_lines.append("# VS Code Extensions hosts: " + ", ".join(profile["hosts"]))
        for url in profile["source_urls"]:
            header_lines.append(f"# VS Code Extensions source: {url}")

    if not args.skip_vk:
        profile = profiles["vk"]
        append_profile_community_sources(
            entries=entries,
            header_lines=header_lines,
            profile=profile,
            provider="vk",
            list_name_v4=args.vk_ipv4_list_name,
            list_name_v6=args.vk_ipv6_list_name,
            resolver_url=resolver_url,
            want_ipv4=args.include_ipv4,
            want_ipv6=args.include_ipv6,
        )
        entries.extend(
            resolve_dns_profile(
                provider="vk",
                source="vk_dns",
                hosts=profile["hosts"],
                resolver_url=resolver_url,
                list_name_v4=args.vk_ipv4_list_name,
                list_name_v6=args.vk_ipv6_list_name,
                want_ipv4=args.include_ipv4,
                want_ipv6=args.include_ipv6,
            )
        )
        header_lines.append("# VK hosts: " + ", ".join(profile["hosts"]))
        for url in profile["source_urls"]:
            header_lines.append(f"# VK source: {url}")

    return entries, header_lines


def optimize_entries(entries: list[RawEntry]) -> list[FinalEntry]:
    optimized: list[FinalEntry] = []
    grouped: dict[tuple[str, str], list[RawEntry]] = defaultdict(list)

    for entry in entries:
        grouped[(entry.list_name, entry.family)].append(entry)

    for (list_name, family), group_entries in grouped.items():
        raw_networks = [entry.network for entry in group_entries]
        collapsed = sorted(
            ipaddress.collapse_addresses(raw_networks),
            key=lambda network: (network.version, int(network.network_address), network.prefixlen),
        )

        for network in collapsed:
            matching_entries = [entry for entry in group_entries if entry.network.subnet_of(network)]
            providers = sorted({entry.provider for entry in matching_entries})
            provider = providers[0] if len(providers) == 1 else "mixed"
            sources = {entry.source for entry in matching_entries}

            optimized.append(
                FinalEntry(
                    provider=provider,
                    family=family,
                    list_name=list_name,
                    network=network,
                    source_count=len(sources),
                    raw_count=len(matching_entries),
                )
            )

    return sorted(
        optimized,
        key=lambda entry: (entry.family, entry.list_name, entry.network.version, int(entry.network.network_address), entry.network.prefixlen),
    )


def get_comment(entry: FinalEntry) -> str:
    parts = [MANAGED_TAG, f"list={entry.list_name}"]
    if entry.raw_count > 1:
        parts.append(f"aggregated={entry.raw_count}")
    if entry.source_count > 1:
        parts.append(f"source-count={entry.source_count}")
    return ";".join(parts)


def format_remove_lines(list_names: list[str], family: str) -> list[str]:
    path_prefix = "/ip firewall address-list" if family == "ipv4" else "/ipv6 firewall address-list"
    lines = [path_prefix]
    for list_name in sorted(set(list_names)):
        lines.append(f':foreach id in=[find where list="{list_name}"] do={{ remove $id }}')
    return lines


def format_add_line(entry: FinalEntry) -> str:
    return (
        f':if ([:len [find where list="{entry.list_name}" and address="{entry.network.with_prefixlen}"]] = 0) '
        f'do={{ add list="{entry.list_name}" address={entry.network.with_prefixlen} comment="{get_comment(entry)}" }}'
    )


def build_output_header(now_local: str, header_lines: list[str], raw_count: int, optimized_count: int, mode_label: str) -> list[str]:
    return [
        "# Internet service IP ranges export for MikroTik",
        f"# Generated at: {now_local}",
        f"# Output mode: {mode_label}",
        f"# Optimization raw-prefixes: {raw_count}",
        f"# Optimization final-prefixes: {optimized_count}",
        f"# Optimization saved-prefixes: {raw_count - optimized_count}",
        *header_lines,
    ]


def render_all_output(
    optimized_entries: list[FinalEntry],
    header_lines: list[str],
    now_local: str,
    flush_managed_entries: bool,
) -> list[str]:
    output_lines = build_output_header(
        now_local=now_local,
        header_lines=header_lines,
        raw_count=sum(entry.raw_count for entry in optimized_entries),
        optimized_count=len(optimized_entries),
        mode_label="all",
    )
    ipv4_entries = [entry for entry in optimized_entries if entry.family == "ipv4"]
    ipv6_entries = [entry for entry in optimized_entries if entry.family == "ipv6"]

    if flush_managed_entries:
        if ipv4_entries:
            output_lines.extend(format_remove_lines([entry.list_name for entry in ipv4_entries], "ipv4"))
        if ipv6_entries:
            output_lines.extend(format_remove_lines([entry.list_name for entry in ipv6_entries], "ipv6"))

    if ipv4_entries:
        output_lines.append("/ip firewall address-list")
        for entry in ipv4_entries:
            output_lines.append(format_add_line(entry))

    if ipv6_entries:
        output_lines.append("/ipv6 firewall address-list")
        for entry in ipv6_entries:
            output_lines.append(format_add_line(entry))

    return output_lines


def render_per_list_output(
    list_name: str,
    optimized_entries: list[FinalEntry],
    header_lines: list[str],
    now_local: str,
    flush_managed_entries: bool,
) -> list[str]:
    output_lines = build_output_header(
        now_local=now_local,
        header_lines=header_lines,
        raw_count=sum(entry.raw_count for entry in optimized_entries),
        optimized_count=len(optimized_entries),
        mode_label=f"per-list:{list_name}",
    )
    output_lines.append(f"# Address-list file: {list_name}")

    ipv4_entries = [entry for entry in optimized_entries if entry.family == "ipv4"]
    ipv6_entries = [entry for entry in optimized_entries if entry.family == "ipv6"]

    if ipv4_entries:
        output_lines.append("/ip firewall address-list")
        if flush_managed_entries:
            output_lines.extend(format_remove_lines([list_name], "ipv4")[1:])
        for entry in ipv4_entries:
            output_lines.append(format_add_line(entry))

    if ipv6_entries:
        output_lines.append("/ipv6 firewall address-list")
        if flush_managed_entries:
            output_lines.extend(format_remove_lines([list_name], "ipv6")[1:])
        for entry in ipv6_entries:
            output_lines.append(format_add_line(entry))

    return output_lines


def sanitize_list_filename(list_name: str) -> str:
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", list_name)
    return safe_name or "address_list"


def get_lists_output_dir(output_path: Path, lists_output_dir: str | None) -> Path:
    if lists_output_dir:
        return Path(lists_output_dir)
    return output_path.with_name(f"{output_path.stem}_lists")


def write_output_file(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="ascii")


def filter_entries_by_list_names(entries: list[EntryT], only_list_names: set[str] | None) -> list[EntryT]:
    if not only_list_names:
        return entries
    return [entry for entry in entries if entry.list_name in only_list_names]


def count_provider(entries: list[RawEntry] | list[FinalEntry], provider: str, family: str) -> int:
    return sum(1 for entry in entries if entry.provider == provider and entry.family == family)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export service IP ranges to MikroTik .rsc")
    parser.add_argument("--sources", nargs="+", default=["goog", "cloud"], choices=sorted(GOOGLE_SOURCE_MAP))
    parser.add_argument("--output-path", default=str(Path(__file__).with_name("internet_mikrotik_import.rsc")))
    parser.add_argument("--lists-output-dir")
    parser.add_argument("--output-mode", choices=("all", "per-list", "both"), default="both")
    parser.add_argument("--only-address-lists", nargs="+")
    parser.add_argument("--config-path", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--ipv4-list-name", default="g_Google")
    parser.add_argument("--ipv6-list-name", default="g_Google")
    parser.add_argument("--meta-ipv4-list-name", default="m_Meta")
    parser.add_argument("--meta-ipv6-list-name", default="m_Meta")
    parser.add_argument("--le-ipv4-list-name", default="z_LE")
    parser.add_argument("--le-ipv6-list-name", default="z_LE")
    parser.add_argument("--tmdb-ipv4-list-name", default="m_tmbd")
    parser.add_argument("--tmdb-ipv6-list-name", default="m_tmbd")
    parser.add_argument("--telegram-ipv4-list-name", default="t_telegram")
    parser.add_argument("--telegram-ipv6-list-name", default="t_telegram")
    parser.add_argument("--youtube-ipv4-list-name", default="y_YouTube")
    parser.add_argument("--youtube-ipv6-list-name", default="y_YouTube")
    parser.add_argument("--chatgpt-ipv4-list-name", default="i_chatgpt")
    parser.add_argument("--chatgpt-ipv6-list-name", default="i_chatgpt")
    parser.add_argument("--github-copilot-ipv4-list-name", default="i_GitHub_Copilot")
    parser.add_argument("--github-copilot-ipv6-list-name", default="i_GitHub_Copilot")
    parser.add_argument("--vscode-extensions-ipv4-list-name", default="i_VSCode_Ext")
    parser.add_argument("--vscode-extensions-ipv6-list-name", default="i_VSCode_Ext")
    parser.add_argument("--vk-ipv4-list-name", default="v_VK")
    parser.add_argument("--vk-ipv6-list-name", default="v_VK")
    parser.add_argument("--meta-asns", nargs="+", default=["AS32934"])
    parser.add_argument("--meta-whois-server", default="whois.radb.net")
    parser.add_argument("--cloud-scopes", nargs="+")
    parser.add_argument("--skip-meta", action="store_true")
    parser.add_argument("--skip-le", action="store_true")
    parser.add_argument("--skip-tmdb", action="store_true")
    parser.add_argument("--skip-telegram", action="store_true")
    parser.add_argument("--skip-youtube", action="store_true")
    parser.add_argument("--skip-chatgpt", action="store_true")
    parser.add_argument("--skip-github-copilot", action="store_true")
    parser.add_argument("--skip-vscode-extensions", action="store_true")
    parser.add_argument("--skip-vk", action="store_true")
    parser.add_argument("--include-ipv4", action="store_true")
    parser.add_argument("--include-ipv6", action="store_true")
    parser.add_argument("--split-list-by-source", action="store_true")
    parser.add_argument("--flush-managed-entries", action="store_true")
    return parser


def normalize_legacy_args(argv: list[str]) -> list[str]:
    normalized: list[str] = []
    for arg in argv:
        if "=" in arg:
            option, value = arg.split("=", 1)
            mapped_option = LEGACY_ARG_ALIASES.get(option, option)
            normalized.append(f"{mapped_option}={value}")
            continue
        normalized.append(LEGACY_ARG_ALIASES.get(arg, arg))
    return normalized


def main() -> int:
    parser = build_parser()
    args = parser.parse_args(normalize_legacy_args(sys.argv[1:]))

    if not args.include_ipv4 and not args.include_ipv6:
        args.include_ipv4 = True
        args.include_ipv6 = True

    args.service_config = load_service_config(Path(args.config_path))

    google_entries, google_headers = get_google_entries(args)
    meta_entries, meta_headers = get_meta_entries(args)
    service_entries, service_headers = get_service_entries(args)

    all_raw_entries = google_entries + meta_entries + service_entries
    if not all_raw_entries:
        raise RuntimeError("После фильтрации не осталось ни одного IP-префикса.")

    optimized_entries = optimize_entries(all_raw_entries)
    only_list_names = set(args.only_address_lists or [])
    if only_list_names:
        available_list_names = {entry.list_name for entry in optimized_entries}
        missing_list_names = sorted(only_list_names - available_list_names)
        if missing_list_names:
            raise RuntimeError(
                "Не найдены запрошенные address-list после фильтрации: " + ", ".join(missing_list_names)
            )
        all_raw_entries = filter_entries_by_list_names(all_raw_entries, only_list_names)
        optimized_entries = filter_entries_by_list_names(optimized_entries, only_list_names)

    now_local = datetime.now().astimezone().isoformat(sep=" ", timespec="seconds")
    common_header_lines = google_headers + meta_headers + service_headers
    output_path = Path(args.output_path)
    lists_output_dir = get_lists_output_dir(output_path, args.lists_output_dir)

    summary: dict[str, str | int] = {}

    if args.output_mode in {"all", "both"}:
        output_lines = render_all_output(
            optimized_entries=optimized_entries,
            header_lines=common_header_lines,
            now_local=now_local,
            flush_managed_entries=args.flush_managed_entries,
        )
        write_output_file(output_path, output_lines)
        summary["OutputPath"] = str(output_path)

    if args.output_mode in {"per-list", "both"}:
        grouped_entries: dict[str, list[FinalEntry]] = defaultdict(list)
        for entry in optimized_entries:
            grouped_entries[entry.list_name].append(entry)

        for list_name, list_entries in grouped_entries.items():
            list_file_path = lists_output_dir / f"{sanitize_list_filename(list_name)}.rsc"
            per_list_lines = render_per_list_output(
                list_name=list_name,
                optimized_entries=list_entries,
                header_lines=common_header_lines,
                now_local=now_local,
                flush_managed_entries=args.flush_managed_entries,
            )
            write_output_file(list_file_path, per_list_lines)

        summary["ListsOutputDir"] = str(lists_output_dir)
        summary["ListFilesGenerated"] = len(grouped_entries)

    for label, provider in SUMMARY_PROVIDERS:
        summary[f"{label}IPv4Raw"] = count_provider(all_raw_entries, provider, "ipv4")
        summary[f"{label}IPv4Optimized"] = count_provider(optimized_entries, provider, "ipv4")
        summary[f"{label}IPv6Raw"] = count_provider(all_raw_entries, provider, "ipv6")
        summary[f"{label}IPv6Optimized"] = count_provider(optimized_entries, provider, "ipv6")

    summary["TotalRaw"] = len(all_raw_entries)
    summary["TotalOptimized"] = len(optimized_entries)
    summary["SavedEntries"] = len(all_raw_entries) - len(optimized_entries)

    for key, value in summary.items():
        print(f"{key:20}: {value}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        raise SystemExit(1)
