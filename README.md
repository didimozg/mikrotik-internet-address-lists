# MikroTik Internet Service Address Lists Exporter

> [!IMPORTANT]
> Дисклеймер: этот проект и состав адресных списков сформированы автором под личные предпочтения, личную логику маршрутизации и личные сценарии использования VPN/маркировки трафика.
> Это не официальный продукт Google, Meta, Telegram, OpenAI, GitHub, Microsoft, VK, TMDB или Let's Encrypt.
> Списки не гарантируют полноту, минимальность или абсолютную точность для любой сети и перед использованием в production их нужно проверять под свои задачи.

Python-скрипт, который собирает IP-диапазоны и DNS-адреса популярных интернет-сервисов и формирует готовые `.rsc`-файлы для импорта в MikroTik RouterOS.

Скрипт умеет:
- собирать один общий `.rsc` со всеми `address-list`
- собирать отдельные `.rsc` по каждому `address-list`
- собирать только выбранный список, например только `t_telegram`
- удалять старые записи по имени `address-list` перед добавлением новых
- убирать дубли, вложенные сети и объединять соседние подсети
- использовать официальные источники там, где они есть, и community GitHub-источники там, где официальных статических диапазонов нет

## Поддерживаемые `address-list`

| Address-list | Назначение |
| --- | --- |
| `g_Google` | Google |
| `m_Meta` | Meta, Facebook, Instagram и связанные сервисы |
| `z_LE` | Let's Encrypt |
| `m_tmbd` | TMDB / The Movie Database |
| `t_telegram` | Telegram |
| `y_YouTube` | YouTube |
| `i_chatgpt` | ChatGPT / OpenAI |
| `i_GitHub_Copilot` | GitHub Copilot |
| `i_VSCode_Ext` | Visual Studio Code Marketplace и скачивание расширений |
| `v_VK` | VK и связанные сервисы экосистемы |

## Что делает скрипт

Сценарий работы такой:

1. Скрипт забирает диапазоны из официальных JSON Google и через `whois` собирает Meta.
2. Для сервисов без официального статического списка IP он резолвит домены через DNS over HTTPS.
3. Дополнительно он может усиливать покрытие community-источниками из GitHub:
   - CIDR-списки
   - готовые MikroTik `.rsc`
   - host/domain lists
4. После этого он:
   - нормализует сети
   - удаляет дубли
   - удаляет вложенные подсети
   - агрегирует соседние сети, если это не расширяет фактическое покрытие
5. На выходе формирует RouterOS-совместимые `.rsc`.

## Почему списки могут отличаться от запуска к запуску

Некоторые сервисы публикуют официальные диапазоны, а некоторые нет. Поэтому часть списков строится из live DNS snapshot и community-источников.

Это значит:
- результат может немного меняться между запусками
- CDN и edge-ноды могут меняться
- один и тот же IP может использоваться несколькими сервисами
- некоторые списки заведомо шире, чем "только один сервис"

Именно поэтому в начале README есть дисклеймер.

## Требования

- Python 3.10+  
- внешний доступ к интернету  
- MikroTik RouterOS для импорта `.rsc`  
- сторонние Python-библиотеки не нужны, используется только standard library

## Быстрый старт

По умолчанию скрипт создаёт:
- общий файл `internet_mikrotik_import.rsc`
- отдельные файлы по каждому списку в каталоге `internet_mikrotik_import_lists`

Запуск:

```powershell
python .\internet_mikrotik_ip_export.py -FlushManagedEntries
```

Импорт общего файла в MikroTik:

```routeros
/import file-name=internet_mikrotik_import.rsc
```

Если нужно проверить импорт на RouterOS 7.16+:

```routeros
/import file-name=internet_mikrotik_import.rsc verbose=yes dry-run
```

## Основные режимы запуска

Только общий файл:

```powershell
python .\internet_mikrotik_ip_export.py -OutputMode all -FlushManagedEntries
```

Только отдельные файлы по каждому списку:

```powershell
python .\internet_mikrotik_ip_export.py -OutputMode per-list -FlushManagedEntries
```

Общий файл и отдельные файлы по спискам:

```powershell
python .\internet_mikrotik_ip_export.py -OutputMode both -FlushManagedEntries
```

Только конкретный список, например `t_telegram`:

```powershell
python .\internet_mikrotik_ip_export.py -OutputMode per-list -OnlyAddressLists t_telegram -FlushManagedEntries
```

Только общий файл, но только для одного списка:

```powershell
python .\internet_mikrotik_ip_export.py -OutputMode all -OnlyAddressLists t_telegram -OutputPath .\t_telegram_only.rsc -FlushManagedEntries
```

Другой каталог для отдельных файлов:

```powershell
python .\internet_mikrotik_ip_export.py -OutputMode both -ListsOutputDir .\mikrotik_lists -FlushManagedEntries
```

Только Google и Meta:

```powershell
python .\internet_mikrotik_ip_export.py -SkipLe -SkipTmdb -SkipTelegram -SkipYouTube -SkipChatGPT -SkipGitHubCopilot -SkipVSCodeExtensions -SkipVk -FlushManagedEntries
```

Только Google Cloud и только IPv4:

```powershell
python .\internet_mikrotik_ip_export.py -Sources cloud -SkipMeta -SkipLe -SkipTmdb -SkipTelegram -SkipYouTube -SkipChatGPT -SkipGitHubCopilot -SkipVSCodeExtensions -SkipVk -IncludeIPv4 -FlushManagedEntries
```

Скрипт понимает оба стиля параметров:
- PowerShell-совместимый: `-FlushManagedEntries`, `-OnlyAddressLists`, `-ConfigPath`
- GNU-стиль: `--flush-managed-entries`, `--only-address-lists`, `--config-path`

## Что создаётся на выходе

- `internet_mikrotik_import.rsc`  
  общий файл со всеми `address-list`

- `internet_mikrotik_import_lists\*.rsc`  
  отдельные `.rsc` по каждому списку:
  - `g_Google.rsc`
  - `m_Meta.rsc`
  - `z_LE.rsc`
  - `m_tmbd.rsc`
  - `t_telegram.rsc`
  - `y_YouTube.rsc`
  - `i_chatgpt.rsc`
  - `i_GitHub_Copilot.rsc`
  - `i_VSCode_Ext.rsc`
  - `v_VK.rsc`

## Важное поведение

Если используется `-FlushManagedEntries`, скрипт удаляет все старые записи из целевых `address-list` по имени списка, а не только свои записи по `comment`.

Это удобно для полного обновления, но важно помнить:
- если в этих же списках были ручные записи, они тоже будут удалены
- лучше держать автоматически управляемые списки отдельно от ручных

## Как расширить списки под свои нужды

### 1. Самый простой способ: править `config.json`

В [config.json](./config.json) можно:
- добавлять и убирать `hosts`
- добавлять дополнительные `source_urls`
- подключать community-источники через:
  - `community_host_urls`
  - `community_host_allow_patterns`
  - `community_rsc_urls`
  - `community_cidr_urls`
- добавлять `extra_cidrs`

Это подходит, если нужно:
- расширить существующий профиль
- добавить новые домены в текущий список
- усилить список community-источниками
- сузить список, убрав лишние домены или community feed

### 2. Если нужно расширить уже существующий список

Примеры:
- добавить новые домены VK Видео, VK Play, Mail.ru, OK.ru в `v_VK`
- добавить дополнительные YouTube CDN hostname в `y_YouTube`
- усилить Telegram ещё одним raw CIDR-источником
- добавить ещё endpoint'ы VS Code Marketplace

Обычно для этого достаточно поправить `config.json` и запустить скрипт заново.

### 3. Если нужен новый независимый `address-list`

Например, если вы захотите сделать новый отдельный список вроде:
- `d_Discord`
- `x_XTwitter`
- `n_Notion`
- `c_Claude`

То сейчас одного `config.json` недостаточно. Нужно будет:

1. добавить новый профиль в `get_default_service_config()`
2. включить его в `required_services`
3. добавить CLI-аргументы для имени нового `address-list`
4. добавить сборку этого профиля в `get_service_entries()`
5. при желании добавить статистику в `SUMMARY_PROVIDERS`

Если нужно, это можно сделать по аналогии с уже существующими профилями `telegram`, `youtube`, `chatgpt`, `vk` и т.д.

### 4. Хорошая практика при расширении

- по возможности сначала использовать официальные источники
- community-источники использовать как усиление, а не как единственную истину
- обязательно ставить фильтры `community_host_allow_patterns`, чтобы не затащить мусорные или рекламные домены
- проверять готовый `.rsc` в lab-среде или через `dry-run`
- помнить, что часть сервисов работает через CDN и shared infrastructure

## Использованные GitHub-наработки и благодарности

В проекте используются или учитываются наработки следующих GitHub-авторов и проектов:

- [fernvenue](https://github.com/fernvenue)  
  репозиторий: [fernvenue/telegram-cidr-list](https://github.com/fernvenue/telegram-cidr-list)  
  используется для Telegram CIDR-источников

- [vogster](https://github.com/vogster)  
  репозиторий: [vogster/Mikrotik-Address-List](https://github.com/vogster/Mikrotik-Address-List)  
  используется как community `.rsc`-источник для `i_chatgpt` и `y_YouTube`

- [v2fly](https://github.com/v2fly)  
  репозиторий: [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community)  
  используется как community host/domain source для `z_LE`, `i_chatgpt`, `i_GitHub_Copilot`, `i_VSCode_Ext`

- [itdoginfo](https://github.com/itdoginfo)  
  репозиторий: [itdoginfo/allow-domains](https://github.com/itdoginfo/allow-domains)  
  используется как community host/domain source для `m_tmbd`, `t_telegram`, `y_YouTube`, `v_VK`

- [iamwildtuna](https://github.com/iamwildtuna)  
  gist: [Telegram infrastructure gist](https://gist.github.com/iamwildtuna/7772b7c84a11bf6e1385f23096a73a15)  
  использовался как дополнительный справочный источник по Telegram

Спасибо авторам за их открытые наработки.

Важно:
- этот скрипт лицензируется отдельно под MIT
- upstream-данные, community-списки и чужие репозитории продолжают жить по их собственным лицензиям и условиям использования

## Официальные и внешние источники данных

### Официальные и первичные источники

- `https://www.gstatic.com/ipranges/goog.json`
- `https://www.gstatic.com/ipranges/cloud.json`
- `https://www.gstatic.com/ipranges/googlebot.json`
- `https://www.facebook.com/help/278069664862989`
- `whois.radb.net` c запросом `-i origin AS32934`
- `https://letsencrypt.org`
- `https://acme-v02.api.letsencrypt.org/directory`
- `https://developer.themoviedb.org/docs/search-and-query-for-details`
- `https://developer.themoviedb.org/reference/collection-images`
- `https://core.telegram.org/gateway/api`
- `https://core.telegram.org/getProxyConfig`
- `https://core.telegram.org/getProxyConfigV6`
- `https://support.google.com/a/answer/6214622?hl=en-US`
- `https://support.google.com/a/answer/9012184?hl=en-US`
- `https://knowledge.workspace.google.com/admin/security/firewall-and-proxy-settings?hl=en&visit_id=639092639852714062-1208261129&rd=1`
- `https://help.openai.com/en/articles/9247338-network-recommendations-for-chatgpt-errors-on-web-and-apps`
- `https://openai.com/chatgpt-connectors.json`
- `https://docs.github.com/en/enterprise-cloud@latest/copilot/reference/copilot-allowlist-reference`
- `https://docs.github.com/en/copilot/how-tos/troubleshoot-copilot/troubleshoot-network-errors`
- `https://code.visualstudio.com/docs/setup/network`
- `https://vk.com`
- `https://vk.ru`
- `https://id.vk.com`
- `https://dns.google/resolve`

### Community GitHub-источники

- `https://github.com/fernvenue/telegram-cidr-list`
- `https://raw.githubusercontent.com/fernvenue/telegram-cidr-list/master/CIDR.txt`
- `https://github.com/vogster/Mikrotik-Address-List`
- `https://raw.githubusercontent.com/vogster/Mikrotik-Address-List/main/chatgpt.rcs`
- `https://raw.githubusercontent.com/vogster/Mikrotik-Address-List/main/youtube.rcs`
- `https://github.com/v2fly/domain-list-community`
- `https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/letsencrypt`
- `https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/openai`
- `https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/github-copilot`
- `https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/github`
- `https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/microsoft-dev`
- `https://github.com/itdoginfo/allow-domains`
- `https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Services/telegram.lst`
- `https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Services/youtube.lst`
- `https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Russia/inside-raw.lst`
- `https://raw.githubusercontent.com/itdoginfo/allow-domains/main/Ukraine/inside-raw.lst`
- `https://gist.github.com/iamwildtuna/7772b7c84a11bf6e1385f23096a73a15`

## Ограничения

- часть сервисов не публикует официальный статический список IP-диапазонов
- часть адресов получается через DNS snapshot, а это всегда временная картинка
- community-источники могут содержать шум, устаревшие данные или домены шире нужного сервиса
- один IP может относиться к нескольким сервисам одновременно
- некоторые приложения могут использовать DoH/DoT, ECH, shared CDN и другие механизмы, которые усложняют точную адресную маршрутизацию

Если задача чувствительная, лучше рассматривать эти списки как рабочую практическую основу, а не как "математически идеальную" классификацию трафика.

## Структура проекта

- [internet_mikrotik_ip_export.py](./internet_mikrotik_ip_export.py) — основной Python-скрипт
- [config.json](./config.json) — конфигурация сервисов и community-источников
- `internet_mikrotik_import.rsc` — общий результат
- `internet_mikrotik_import_lists/` — отдельные `.rsc` по каждому списку

## Лицензия

Собственный код этого проекта выкладывается под лицензией [MIT](./LICENSE).

Это относится к самому скрипту и его коду.
Внешние данные, community-списки и upstream-репозитории не пере-лицензируются этим README и продолжают использоваться по их собственным условиям.
