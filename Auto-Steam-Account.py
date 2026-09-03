from __future__ import annotations
import json
import logging
import os
import random
import shutil
import re
import threading
import time
import uuid
import zipfile
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Tuple
import requests
try:
    from tg_bot import CBT as _CBT
except Exception:
    _CBT = None
try:
    from telebot import types as tg_types
except Exception:
    tg_types = None
NAME = 'Auto Steam Account (Dim4n4ik Shop)'
VERSION = '1.0.2'
DESCRIPTION = 'Авто-закупка и выдача Steam-аккаунтов, а также выдача почт из локальных баз на FunPay'
CREDITS = '@dmitry_mak09, @tinechelovec'
UUID = '6e8ff163-7a2c-4510-b6a9-f41c3d8edc6d'
_CBT_PLUGIN_SETTINGS = getattr(_CBT, 'PLUGIN_SETTINGS', None) if _CBT else None
CBT_SETTINGS = f'{_CBT_PLUGIN_SETTINGS}:{UUID}:0' if _CBT_PLUGIN_SETTINGS is not None else ''
SETTINGS_PAGE = False
ORIGINAL_AUTHOR_URL = 'https://t.me/dmitry_mak09'
CREATOR_URL = 'https://t.me/tinechelovec'
GROUP_URL = 'https://t.me/dev_thc_chat'
CHANNEL_URL = 'https://t.me/by_thc'
GITHUB_URL = 'https://github.com/tinechelovec/FPC-Auto-Steam-Account'
GITHUB_REPO = 'tinechelovec/FPC-Auto-Steam-Account'
SHOP_BOT_URL = 'https://t.me/dim4n4ikshop_bot?start=ref7202094913'
MAIL_BOT_URL = 'https://t.me/dim4n4ikemail_bot?start=ref7202094913'
SHOP_CHAT_URL = 'https://t.me/berloga_dim4n4ik'
SHOP_SITE_URL = 'https://dim4n4ik.shop'
INSTRUCTION_URL = 'https://teletype.media/@tinechelovec/Auto-Steam-Account'
ALT_INSTRUCTION_URL = 'https://github.com/tinechelovec/FPC-Auto-Steam-Account/blob/main/instructions.md'
CB_PLUGINS_LIST_OPEN = f"{getattr(_CBT, 'PLUGINS_LIST', '44')}:0" if _CBT else '44:0'
logger = logging.getLogger('FPC.dim4n4ik_shop')
LP = '[d4shop]'
BASE_DIR = os.getcwd()
LEGACY_STORAGE_DIR = os.path.join('storage', 'dim4n4ik_shop')
STORAGE_DIR = os.path.join('storage', 'plugins', 'dim4n4ik_shop')
_PREVIOUS_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PREVIOUS_LEGACY_STORAGE_DIR = os.path.join(_PREVIOUS_BASE_DIR, 'storage', 'dim4n4ik_shop')
_PREVIOUS_STORAGE_DIR = os.path.join(_PREVIOUS_BASE_DIR, 'storage', 'plugins', 'dim4n4ik_shop')
DATABASES_DIR = os.path.join(STORAGE_DIR, 'databases')
LOG_DIR = os.path.join(STORAGE_DIR, 'logs')
BACKUPS_DIR = os.path.join(STORAGE_DIR, 'backups')
CONFIG_FILE = os.path.join(STORAGE_DIR, 'settings.json')
BINDINGS_FILE = os.path.join(STORAGE_DIR, 'bindings.json')
PENDING_FILE = os.path.join(STORAGE_DIR, 'pending_orders.json')
PROCESSED_FILE = os.path.join(STORAGE_DIR, 'processed_orders.json')
ORDER_LOG_FILE = os.path.join(STORAGE_DIR, 'order_log.json')
STATS_FILE = os.path.join(STORAGE_DIR, 'stats.json')
AUTO_DISABLED_FILE = os.path.join(STORAGE_DIR, 'auto_disabled_lots.json')
DATABASES_META_FILE = os.path.join(STORAGE_DIR, 'databases.json')
MIGRATION_FILE = os.path.join(STORAGE_DIR, 'migration.json')
LOG_FILE = os.path.join(LOG_DIR, 'plugin.log')
DEFAULT_BUYER_MESSAGES: Dict[str, str] = {'payment_received': '➖➖➖➖➖➖➖➖\n✅ Оплата получена! Выдаю товар, обычно это занимает меньше минуты…\n➖➖➖➖➖➖➖➖', 'goods_header': '🚨🚨🚨 ИНСТРУКЦИЯ ПО ВХОДУ В ПОЧТУ 🚨🚨🚨\n\n📧 Вход в почту: https://outlook.office.com/mail/\nДанные форматом:\nлогин стим:пароль стим:почта:пароль от почты\n\n‼️ Для входа в почту используйте ПОСЛЕДНИЕ два значения (после 2-го двоеточия) ‼️\n\n📎 Видеоинструкция гугл диск — https://drive.google.com/file/d/1iIi7BW6eI8Yl4q465jUD-J0BgVqUXcUd/view?usp=sharing', 'goods_footer': '🙏 Проверьте товар и подтвердите заказ:\n{order_url}\n⭐ Будем рады отзыву!\n➖➖➖➖➖➖➖➖', 'refund': '➖➖➖➖➖➖➖➖\n😔 К сожалению, выдать товар по заказу #{order_id} не получилось.\n💸 Деньги возвращены. Приносим извинения!\n➖➖➖➖➖➖➖➖', 'delay': '➖➖➖➖➖➖➖➖\n⏳ Возникла задержка с выдачей заказа #{order_id}.\nПродавец уже уведомлён и решит вопрос в ближайшее время.\n➖➖➖➖➖➖➖➖'}
LEGACY_DEFAULT_GOODS_HEADER = '✅ Ваш товар по заказу #{order_id}:'
BUYER_MESSAGE_LABELS = {'payment_received': 'Оплата получена', 'goods_header': 'Заголовок выдачи', 'goods_footer': 'После выдачи', 'refund': 'Возврат денег', 'delay': 'Задержка / ручная проверка'}
DEFAULT_CONFIG: Dict[str, Any] = {'api_key': '', 'base_url': 'https://api.dim4n4ik.shop', 'plugin_enabled': True, 'auto_refund_enabled': False, 'low_balance_threshold_rub': 100.0, 'balance_check_interval_min': 10, 'notifications_enabled': True, 'notify_new_order': True, 'notify_success': True, 'notify_failure': True, 'notify_errors': True, 'notify_low_balance': True, 'notify_out_of_stock': True, 'buyer_messages': dict(DEFAULT_BUYER_MESSAGES), 'hidden_categories': None, 'auto_lots_by_stock': True, 'fp_auto_buffer': 25, 'fp_auto_sync_sec': 60, 'loss_protection': True, 'loss_min_margin_percent': 0, 'match_by_title': False, 'lot_cache': [], 'ignored_lot_ids': [], 'mail_catalog_migrated': False}
DEFAULT_STATS: Dict[str, Any] = {'total_orders': 0, 'total_failed': 0, 'total_qty': 0, 'total_revenue_rub': 0.0, 'total_cost_rub': 0.0, 'items': {}, 'last_order_at': ''}
_STORAGE_TYPES = {'settings.json': dict, 'bindings.json': dict, 'pending_orders.json': dict, 'processed_orders.json': dict, 'order_log.json': list, 'stats.json': dict, 'auto_disabled_lots.json': dict, 'databases.json': dict}
FUNPAY_ORDER_QTY_MAX = 10
def _raw_json(path: Path, expected=None):
    try:
        with path.open('r', encoding='utf-8') as f:
            value = json.load(f)
        if expected is not None and not isinstance(value, expected):
            return None
        return value
    except Exception:
        return None
def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    with tmp.open('w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    with tmp.open('r', encoding='utf-8') as f:
        json.load(f)
    os.replace(tmp, path)
def _migration_settings_real(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    for key, default in DEFAULT_CONFIG.items():
        if key not in value:
            continue
        current = value.get(key)
        if key == 'buyer_messages':
            if isinstance(current, dict) and any(str(current.get(k, '')) != str(v) for k, v in DEFAULT_BUYER_MESSAGES.items() if k in current):
                return True
        elif key == 'lot_cache':
            if current:
                return True
        elif current != default and current not in (None, '', [], {}):
            return True
        elif key == 'api_key' and current:
            return True
    return bool(value.get('api_key'))
def _migration_merge_settings(value: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(DEFAULT_CONFIG)
    merged['buyer_messages'] = dict(DEFAULT_BUYER_MESSAGES)
    for key, item in value.items():
        if key in merged:
            merged[key] = item
    messages = dict(DEFAULT_BUYER_MESSAGES)
    raw_messages = value.get('buyer_messages')
    if isinstance(raw_messages, dict):
        messages.update({str(k): str(v) for k, v in raw_messages.items() if k in messages})
        if str(raw_messages.get('goods_header') or '') == LEGACY_DEFAULT_GOODS_HEADER:
            messages['goods_header'] = DEFAULT_BUYER_MESSAGES['goods_header']
    merged['buyer_messages'] = messages
    if not isinstance(merged.get('lot_cache'), list):
        merged['lot_cache'] = []
    return merged
def _migration_normalize_binding(value: Any) -> Dict[str, Any]:
    b = dict(value) if isinstance(value, dict) else {}
    mode = str(b.get('delivery_mode') or 'api').lower()
    if mode not in ('api', 'database'):
        mode = 'api'
    try:
        qty = max(1, min(FUNPAY_ORDER_QTY_MAX, int(b.get('qty_per_unit', b.get('qty', 1)) or 1)))
    except Exception:
        qty = 1
    target_raw = b.get('fp_stock_target')
    if target_raw is None:
        target_raw = 25 if b.get('fp_auto') else 0
    try:
        target = max(0, min(500, int(target_raw or 0)))
    except Exception:
        target = 0
    b['delivery_mode'] = mode
    b['qty_per_unit'] = qty
    b['qty'] = qty
    b['fp_stock_target'] = target
    b['fp_auto'] = target > 0
    b['enabled'] = bool(b.get('enabled', True))
    b['database_id'] = str(b.get('database_id') or '') if mode == 'database' else ''
    return b
def _migration_prepare(name: str, value: Any) -> Any:
    if name == 'settings.json':
        return _migration_merge_settings(value if isinstance(value, dict) else {})
    if name == 'bindings.json':
        return {str(k): _migration_normalize_binding(v) for k, v in (value.items() if isinstance(value, dict) else [])}
    if name == 'databases.json':
        if isinstance(value, dict) and isinstance(value.get('databases'), list):
            return value
        return {'schema': 1, 'databases': []}
    return value
def _migration_merge_initial_settings(legacy: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
    legacy_norm = _migration_merge_settings(legacy)
    current_norm = _migration_merge_settings(current)
    if str(current.get('api_key') or '').strip():
        return current_norm
    merged = dict(current_norm)
    for key, default in DEFAULT_CONFIG.items():
        legacy_value = legacy_norm.get(key)
        current_value = current_norm.get(key)
        if key == 'buyer_messages':
            messages = dict(legacy_norm.get(key) or DEFAULT_BUYER_MESSAGES)
            raw_current = current.get(key)
            if isinstance(raw_current, dict):
                messages.update({str(k): str(v) for k, v in raw_current.items() if k in DEFAULT_BUYER_MESSAGES})
            merged[key] = messages
            continue
        if key == 'lot_cache':
            if not current_value and legacy_value:
                merged[key] = legacy_value
            continue
        current_is_default = current_value == default or current_value in (None, '', [], {})
        legacy_is_meaningful = legacy_value != default and legacy_value not in (None, '', [], {})
        if current_is_default and legacy_is_meaningful:
            merged[key] = legacy_value
    return _migration_merge_settings(merged)
def _storage_source_dirs() -> List[Path]:
    target = Path(STORAGE_DIR).resolve()
    result = []
    for raw in (_PREVIOUS_STORAGE_DIR, LEGACY_STORAGE_DIR, _PREVIOUS_LEGACY_STORAGE_DIR):
        try:
            path = Path(raw)
            if path.resolve() == target:
                continue
            if any(path.resolve() == item.resolve() for item in result):
                continue
            result.append(path)
        except Exception:
            continue
    return result
def _ensure_storage_layout() -> List[str]:
    errors = []
    for raw in (STORAGE_DIR, DATABASES_DIR, LOG_DIR, BACKUPS_DIR):
        try:
            Path(raw).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f'{raw}: {e}')
    return errors
def _early_storage_migration() -> Dict[str, Any]:
    report = {'schema': 2, 'ok': True, 'timestamp': datetime.now().isoformat(timespec='seconds'), 'target_path': STORAGE_DIR, 'migrated_files': [], 'replaced_files': [], 'sources': [], 'errors': []}
    layout_errors = _ensure_storage_layout()
    if layout_errors:
        report['ok'] = False
        report['errors'].extend(layout_errors)
        logger.warning(f"{LP} storage layout unavailable: {' | '.join(layout_errors)}")
        return report
    try:
        new = Path(STORAGE_DIR)
        backups = Path(BACKUPS_DIR)
        marker_path = Path(MIGRATION_FILE)
        existing_marker = _raw_json(marker_path, dict)
        first_migration = existing_marker is None
        stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        backup_dir = backups / f'pre-migration-{stamp}'
        sources = []
        for source in _storage_source_dirs():
            try:
                if source.is_dir():
                    sources.append(source)
                    report['sources'].append(str(source))
            except Exception as e:
                report['errors'].append(f'{source}: {e}')
        for name, expected in _STORAGE_TYPES.items():
            current_path = new / name
            current = _raw_json(current_path, expected)
            candidates = []
            for source in sources:
                source_path = source / name
                value = _raw_json(source_path, expected)
                if value is None:
                    continue
                try:
                    mtime = source_path.stat().st_mtime
                except Exception:
                    mtime = 0
                candidates.append((mtime, value, source_path))
            candidates.sort(key=lambda row: row[0], reverse=True)
            legacy = candidates[0][1] if candidates else None
            payload = None
            if current is None and legacy is not None:
                payload = _migration_prepare(name, legacy)
                report['migrated_files'].append(name)
            elif current is not None:
                if name == 'settings.json' and first_migration and isinstance(legacy, dict):
                    payload = _migration_merge_initial_settings(legacy, current)
                elif name in ('settings.json', 'bindings.json'):
                    payload = _migration_prepare(name, current)
                if payload == current:
                    payload = None
            if payload is not None:
                try:
                    if current_path.exists():
                        backup_dir.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(current_path, backup_dir / name)
                        report['replaced_files'].append(name)
                    _atomic_write_json(current_path, payload)
                except Exception as e:
                    report['ok'] = False
                    report['errors'].append(f'{name}: {e}')
        if first_migration:
            for source in sources:
                try:
                    for src in source.iterdir():
                        if not src.is_file() or src.name in _STORAGE_TYPES:
                            continue
                        dst = new / src.name
                        if dst.exists():
                            continue
                        try:
                            shutil.copy2(src, dst)
                            report['migrated_files'].append(src.name)
                        except Exception as e:
                            report['errors'].append(f'{src.name}: {e}')
                except Exception as e:
                    report['errors'].append(f'{source}: {e}')
        try:
            _atomic_write_json(marker_path, report)
        except Exception as e:
            report['ok'] = False
            report['errors'].append(f'migration marker: {e}')
        if report['errors']:
            logger.warning(f"{LP} storage migration completed with warnings: {' | '.join(report['errors'][:5])}")
        return report
    except Exception as e:
        report['ok'] = False
        report['errors'].append(str(e))
        logger.warning(f'{LP} storage migration skipped safely: {e}')
        return report
def _log_event(event: str, level: int=logging.INFO, **fields: Any) -> None:
    parts = [f'event={str(event or "event").replace(chr(10), " ")[:80]}']
    for key, value in fields.items():
        if value is None:
            continue
        name = str(key or 'field')[:60]
        if any(token in name.lower() for token in ('api_key', 'token', 'password', 'content_b64', 'mafile_b64')):
            text = '***'
        else:
            text = str(value).replace('\r', ' ').replace('\n', ' ')[:240]
        parts.append(f'{name}={text}')
    logger.log(level, f'{LP} ' + ' '.join(parts))
def _close_file_logging(target_path: Optional[str]=None) -> None:
    target = os.path.normcase(str(Path(target_path or LOG_FILE).resolve())) if (target_path or LOG_FILE) else ''
    for handler in list(logger.handlers):
        if not isinstance(handler, logging.FileHandler):
            continue
        current = os.path.normcase(str(Path(getattr(handler, 'baseFilename', '') or '').resolve()))
        if target and current != target:
            continue
        try:
            handler.acquire()
            try:
                if getattr(handler, 'stream', None):
                    handler.flush()
                logger.removeHandler(handler)
                handler.close()
            finally:
                handler.release()
        except Exception:
            try:
                logger.removeHandler(handler)
                handler.close()
            except Exception:
                pass
def _configure_file_logging() -> None:
    try:
        if _ensure_storage_layout():
            return
        target = os.path.normcase(str(Path(LOG_FILE).resolve()))
        for handler in list(logger.handlers):
            if isinstance(handler, logging.FileHandler) and os.path.normcase(str(Path(getattr(handler, 'baseFilename', '') or '').resolve())) == target:
                return
        handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
        logger.addHandler(handler)
        _log_event('logging_ready', path=target)
    except Exception as e:
        logger.warning(f'{LP} file logging disabled: {e}')
cardinal = None
bot = None
admin_chat_id: Optional[int] = None
shop_client: Optional['ShopClient'] = None
_config: Dict[str, Any] = {}
_bindings: Dict[str, Dict[str, Any]] = {}
_pending: Dict[str, Dict[str, Any]] = {}
_processed: Dict[str, float] = {}
_seen: set = set()
_rejected: Dict[str, float] = {}
_config_lock = threading.RLock()
_bindings_lock = threading.RLock()
_orders_lock = threading.RLock()
_stats_lock = threading.RLock()
_database_lock = threading.RLock()
_maintenance_lock = threading.RLock()
_stop_event = threading.Event()
_waiting: Dict[int, Dict[str, Any]] = {}
_last_balance_kop: Optional[int] = None
_last_balance_ts: float = 0.0
_low_balance_alerted = False
_oos_alerted: set = set()
_catalog_cache: Dict[str, Any] = {'ts': 0.0, 'items': []}
_auto_disabled: Dict[str, Any] = {}
_ok_strikes: Dict[str, int] = {}
_grp_select: Dict[int, Dict[str, Any]] = {}
_db_product_idx: List[int] = []
AUTO_LOT_CATEGORIES = (89, 1350, 938)
_last_lot_discovery_ts = 0.0
_last_lot_discovery_report: Dict[str, Any] = {'found': 0, 'errors': 0, 'category_counts': {89: 0, 1350: 0, 938: 0}}
_lot_create_lock = threading.Lock()
_update_lock = threading.Lock()
MSG_SEP = '➖➖➖➖➖➖➖➖'
BUYER_MSG_LIMIT = 900
BUYER_MSG_MAX_LINES = 10
API_QTY_MAX = 100
MAIL_PRODUCT_TITLE = 'Почты Hotmail / Outlook'
TAG_RE = re.compile('d4s:(\\d+)')
ORDER_PAID_RE = re.compile('оплатил(?:а)? заказ\\s*#([A-Za-z0-9]+)')
INVISIBLE_RE = re.compile('[\u2061\u200b\u200c\u200d\ufeff]')
def load_json(path: str, default: Any) -> Any:
    primary = Path(path)
    backup = Path(path + '.bak')
    primary_error = None
    if primary.exists():
        try:
            with primary.open('r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            primary_error = e
            logger.warning(f'{LP} load_json {primary.name}: {e}')
    if backup.exists():
        try:
            with backup.open('r', encoding='utf-8') as f:
                restored = json.load(f)
            if primary.exists() and primary_error is not None:
                stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
                corrupt = primary.with_name(primary.name + f'.corrupt.{stamp}')
                try:
                    os.replace(primary, corrupt)
                except Exception:
                    pass
            try:
                _atomic_write_json(primary, restored)
                logger.warning(f'{LP} {primary.name} restored from backup')
            except Exception as e:
                logger.warning(f'{LP} cannot restore {primary.name} from backup: {e}')
            return restored
        except Exception as e:
            logger.warning(f'{LP} load_json {backup.name}: {e}')
    return default
def save_json(path: str, data: Any) -> None:
    primary = Path(path)
    backup = Path(path + '.bak')
    try:
        if primary.exists():
            try:
                with primary.open('r', encoding='utf-8') as f:
                    json.load(f)
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(primary, backup)
            except Exception:
                pass
        _atomic_write_json(primary, data)
    except Exception as e:
        logger.error(f'{LP} save_json {primary.name}: {e}')
def cfg_get(key: str) -> Any:
    with _config_lock:
        return _config.get(key, DEFAULT_CONFIG.get(key))
def cfg_set(key: str, value: Any) -> None:
    with _config_lock:
        _config[key] = value
        save_json(CONFIG_FILE, _config)
def _buyer_messages() -> Dict[str, str]:
    merged = dict(DEFAULT_BUYER_MESSAGES)
    raw = cfg_get('buyer_messages')
    if isinstance(raw, dict):
        merged.update({str(k): str(v) for k, v in raw.items() if k in merged})
    return merged
def _buyer_message(key: str, **values: Any) -> str:
    template = _buyer_messages().get(key, DEFAULT_BUYER_MESSAGES.get(key, ''))
    context = {'order_id': '', 'order_url': '', 'product_title': '', 'qty': '', 'reason': ''}
    context.update({k: str(v) for k, v in values.items()})
    try:
        return template.format(**context)
    except Exception:
        return DEFAULT_BUYER_MESSAGES.get(key, '').format(**context)
def _reset_api_runtime() -> None:
    global shop_client, _last_balance_kop, _last_balance_ts, _low_balance_alerted
    shop_client = None
    _last_balance_kop = None
    _last_balance_ts = 0.0
    _low_balance_alerted = False
    _catalog_cache['ts'] = 0.0
    _catalog_cache['items'] = []
def _clear_api_key() -> None:
    cfg_set('api_key', '')
    _reset_api_runtime()
def _normalize_binding(value: Any) -> Dict[str, Any]:
    b = _migration_normalize_binding(value)
    if b.get('delivery_mode') == 'database' and not b.get('database_id'):
        b['delivery_mode'] = 'api'
    return b
def _normalize_bindings(value: Any) -> Dict[str, Dict[str, Any]]:
    if not isinstance(value, dict):
        return {}
    return {str(k): _normalize_binding(v) for k, v in value.items() if isinstance(v, dict)}
def _database_inventory_path(database_id: str) -> Path:
    clean = re.sub('[^A-Za-z0-9_-]', '', str(database_id or ''))[:64]
    if not clean:
        raise ValueError('Некорректный ID базы')
    return Path(DATABASES_DIR) / f'{clean}.json'
def _load_databases_meta() -> Dict[str, Any]:
    with _database_lock:
        path = Path(DATABASES_META_FILE)
        raw = load_json(DATABASES_META_FILE, None)
        if not isinstance(raw, dict) or not isinstance(raw.get('databases'), list):
            if path.exists():
                try:
                    stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
                    os.replace(path, path.with_name(path.name + f'.corrupt.{stamp}'))
                except Exception:
                    pass
            raw = {'schema': 1, 'databases': []}
            save_json(DATABASES_META_FILE, raw)
        clean = []
        for item in raw.get('databases', []):
            if not isinstance(item, dict) or not item.get('id'):
                continue
            row = dict(item)
            row['id'] = str(row['id'])
            row['name'] = str(row.get('name') or row['id'])[:80]
            try:
                row['product_id'] = int(row.get('product_id'))
            except Exception:
                continue
            row['product_title'] = str(row.get('product_title') or f"товар {row['product_id']}")[:160]
            row['total_added'] = max(0, int(row.get('total_added', 0) or 0))
            row['total_sold'] = max(0, int(row.get('total_sold', 0) or 0))
            row['created_at'] = str(row.get('created_at') or _now_str())
            row['updated_at'] = str(row.get('updated_at') or row['created_at'])
            clean.append(row)
        normalized = {'schema': 1, 'databases': clean}
        if normalized != raw:
            save_json(DATABASES_META_FILE, normalized)
        return normalized
def _save_databases_meta(value: Dict[str, Any]) -> None:
    with _database_lock:
        save_json(DATABASES_META_FILE, {'schema': 1, 'databases': list(value.get('databases', []))})
def _database_by_id(database_id: str) -> Optional[Dict[str, Any]]:
    meta = _load_databases_meta()
    for item in meta['databases']:
        if str(item.get('id')) == str(database_id):
            return dict(item)
    return None
def _empty_database_inventory() -> Dict[str, Any]:
    return {'available': [], 'reserved': {}, 'history': []}
def _load_database_inventory(database_id: str) -> Dict[str, Any]:
    with _database_lock:
        path = _database_inventory_path(database_id)
        if not path.exists():
            return _empty_database_inventory()
        raw = _raw_json(path, dict)
        if raw is None:
            raise ValueError('Файл базы повреждён')
        available = raw.get('available') if isinstance(raw.get('available'), list) else []
        reserved = raw.get('reserved') if isinstance(raw.get('reserved'), dict) else {}
        history = raw.get('history') if isinstance(raw.get('history'), list) else []
        clean_reserved = {}
        for order_id, values in reserved.items():
            if isinstance(values, list):
                clean_reserved[str(order_id)] = [str(v) for v in values if str(v)]
        return {'available': [str(v) for v in available if str(v)], 'reserved': clean_reserved, 'history': [x for x in history[-100:] if isinstance(x, dict)]}
def _save_database_inventory(database_id: str, value: Dict[str, Any]) -> None:
    with _database_lock:
        payload = {'available': [str(v) for v in value.get('available', []) if str(v)], 'reserved': {str(k): [str(v) for v in vals if str(v)] for k, vals in (value.get('reserved', {}) or {}).items() if isinstance(vals, list)}, 'history': [x for x in (value.get('history', []) or [])[-100:] if isinstance(x, dict)]}
        _atomic_write_json(_database_inventory_path(database_id), payload)
def _validate_database_name(name: str, ignore_id: str='') -> str:
    clean = re.sub(r'\s+', ' ', str(name or '')).strip()[:80]
    if len(clean) < 2:
        raise ValueError('Название базы должно быть от 2 до 80 символов')
    meta = _load_databases_meta()
    for item in meta['databases']:
        if str(item.get('id')) != str(ignore_id) and str(item.get('name', '')).casefold() == clean.casefold():
            raise ValueError('База с таким названием уже существует')
    return clean
def _create_database(name: str, product_id: int, product_title: str) -> Dict[str, Any]:
    with _database_lock:
        clean = _validate_database_name(name)
        pid = int(product_id)
        if pid <= 0:
            raise ValueError('Некорректный product_id')
        meta = _load_databases_meta()
        database_id = uuid.uuid4().hex[:12]
        now = _now_str()
        item = {'id': database_id, 'name': clean, 'product_id': pid, 'product_title': str(product_title or f'товар {pid}')[:160], 'created_at': now, 'updated_at': now, 'total_added': 0, 'total_sold': 0}
        _save_database_inventory(database_id, _empty_database_inventory())
        meta['databases'].append(item)
        _save_databases_meta(meta)
        return dict(item)
def _is_mail_database(db: Any) -> bool:
    return isinstance(db, dict) and str(db.get('source_type') or '').lower() == 'mail'
def _mail_database_by_lot(lot_id: str) -> Optional[Dict[str, Any]]:
    for db in _load_databases_meta().get('databases', []):
        if _is_mail_database(db) and str(db.get('source_lot_id') or '') == str(lot_id):
            return dict(db)
    return None
def _create_mail_database(lot_id: str) -> Dict[str, Any]:
    existing = _mail_database_by_lot(lot_id)
    if existing:
        return existing
    with _database_lock:
        existing = _mail_database_by_lot(lot_id)
        if existing:
            return existing
        name = _validate_database_name(f'Почты LOT {lot_id}')
        meta = _load_databases_meta()
        database_id = uuid.uuid4().hex[:12]
        now = _now_str()
        item = {'id': database_id, 'name': name, 'product_id': 0, 'product_title': MAIL_PRODUCT_TITLE, 'source_type': 'mail', 'source_lot_id': str(lot_id), 'created_at': now, 'updated_at': now, 'total_added': 0, 'total_sold': 0}
        _save_database_inventory(database_id, _empty_database_inventory())
        meta['databases'].append(item)
        _save_databases_meta(meta)
        return dict(item)
def _rename_database(database_id: str, name: str) -> Dict[str, Any]:
    with _database_lock:
        clean = _validate_database_name(name, database_id)
        meta = _load_databases_meta()
        for item in meta['databases']:
            if str(item.get('id')) == str(database_id):
                item['name'] = clean
                item['updated_at'] = _now_str()
                _save_databases_meta(meta)
                return dict(item)
    raise ValueError('База не найдена')
def _database_references(database_id: str) -> List[str]:
    with _bindings_lock:
        return [str(lot_id) for lot_id, b in _bindings.items() if str(b.get('delivery_mode') or '') == 'database' and str(b.get('database_id') or '') == str(database_id)]
def _delete_database(database_id: str) -> bool:
    refs = _database_references(database_id)
    if refs:
        raise ValueError('База используется лотами: ' + ', '.join(refs[:10]))
    reserved = _database_reserved_count(database_id)
    if reserved:
        raise ValueError(f'В базе есть зарезервированные аккаунты: {reserved}')
    with _orders_lock:
        pending_refs = [str(oid) for oid, od in _pending.items() if str(od.get('database_id') or '') == str(database_id)]
    if pending_refs:
        raise ValueError('База используется незавершёнными заказами: ' + ', '.join(pending_refs[:10]))
    with _database_lock:
        meta = _load_databases_meta()
        before = len(meta['databases'])
        meta['databases'] = [x for x in meta['databases'] if str(x.get('id')) != str(database_id)]
        if len(meta['databases']) == before:
            return False
        _save_databases_meta(meta)
        path = _database_inventory_path(database_id)
        if path.exists():
            path.unlink()
        return True
def _database_stock(database_id: str) -> int:
    try:
        return len(_load_database_inventory(database_id).get('available', []))
    except Exception:
        return 0
def _database_reserved_count(database_id: str) -> int:
    try:
        inv = _load_database_inventory(database_id)
        return sum(len(v) for v in inv.get('reserved', {}).values())
    except Exception:
        return 0
def _import_database_items(database_id: str, values: List[str], source: str='manual_text') -> Dict[str, Any]:
    db = _database_by_id(database_id)
    if not db:
        raise ValueError('База не найдена')
    with _database_lock:
        inv = _load_database_inventory(database_id)
        existing = set(inv.get('available', []))
        for reserved_values in inv.get('reserved', {}).values():
            existing.update(str(v) for v in reserved_values if str(v))
        added = []
        skipped = 0
        for raw in values:
            value = str(raw or '').strip().lstrip('\ufeff')
            if not value or value in existing:
                skipped += 1
                continue
            existing.add(value)
            added.append(value)
        if added:
            inv['available'].extend(added)
            inv['history'].append({'ts': _now_str(), 'event': 'manual_import', 'source': str(source or 'manual_text')[:40], 'qty': len(added), 'skipped': skipped})
            _save_database_inventory(database_id, inv)
            meta = _load_databases_meta()
            for item in meta['databases']:
                if str(item.get('id')) == str(database_id):
                    item['total_added'] = int(item.get('total_added', 0) or 0) + len(added)
                    item['updated_at'] = _now_str()
                    break
            _save_databases_meta(meta)
        return {'ok': True, 'added': len(added), 'skipped': skipped, 'available': len(inv.get('available', []))}
def _reserve_database_items(database_id: str, order_id: str, qty: int) -> List[str]:
    with _database_lock:
        inv = _load_database_inventory(database_id)
        order_key = str(order_id)
        existing = inv['reserved'].get(order_key)
        if existing:
            return list(existing)
        need = max(1, int(qty))
        if len(inv['available']) < need:
            raise ShopApiError(409, 'database_stock', 'Недостаточно аккаунтов в выбранной базе', {'available': len(inv['available'])})
        values = list(inv['available'][:need])
        inv['available'] = inv['available'][need:]
        inv['reserved'][order_key] = values
        inv['history'].append({'ts': _now_str(), 'event': 'reserve', 'order_id': order_key, 'qty': len(values)})
        _save_database_inventory(database_id, inv)
        return values
def _commit_database_reservation(database_id: str, order_id: str) -> int:
    with _database_lock:
        inv = _load_database_inventory(database_id)
        values = list(inv['reserved'].pop(str(order_id), []) or [])
        if not values:
            return 0
        inv['history'].append({'ts': _now_str(), 'event': 'sold', 'order_id': str(order_id), 'qty': len(values)})
        _save_database_inventory(database_id, inv)
        meta = _load_databases_meta()
        for item in meta['databases']:
            if str(item.get('id')) == str(database_id):
                item['total_sold'] = int(item.get('total_sold', 0) or 0) + len(values)
                item['updated_at'] = _now_str()
                break
        _save_databases_meta(meta)
        return len(values)
def _release_database_reservation(database_id: str, order_id: str) -> int:
    with _database_lock:
        inv = _load_database_inventory(database_id)
        values = list(inv['reserved'].pop(str(order_id), []) or [])
        if not values:
            return 0
        inv['available'] = values + inv['available']
        inv['history'].append({'ts': _now_str(), 'event': 'release', 'order_id': str(order_id), 'qty': len(values)})
        _save_database_inventory(database_id, inv)
        return len(values)
def _replenish_database(database_id: str, qty: int) -> Dict[str, Any]:
    db = _database_by_id(database_id)
    if not db:
        raise ValueError('База не найдена')
    if _is_mail_database(db):
        raise ValueError('Почтовая база пополняется только текстом или файлом')
    qty = max(1, int(qty))
    if qty > API_QTY_MAX:
        raise ValueError(f'Максимум {API_QTY_MAX} за одну закупку')
    client = _get_client()
    if client is None:
        raise ValueError('API-ключ не задан')
    stock = _product_stock(int(db['product_id']), max_age=0)
    if stock < qty:
        raise ValueError(f'В магазине доступно только {stock} шт.')
    idem = f"db-{database_id}-{int(time.time() * 1000)}-{random.randint(1000, 9999)}"
    response = client.create_order(int(db['product_id']), qty, idem)
    _catalog_cache['ts'] = 0.0
    _catalog_cache['items'] = []
    items = response.get('items') or []
    if any(str(item.get('type') or '').lower() == 'file' for item in items if isinstance(item, dict)):
        raise ValueError('API вернул файловый товар, база принимает только текст')
    values = [str(item.get('value')) for item in items if isinstance(item, dict) and item.get('value')]
    if len(values) != qty:
        raise ValueError(f'API вернул {len(values)} текстовых позиций вместо {qty}; база не изменена')
    with _database_lock:
        inv = _load_database_inventory(database_id)
        inv['available'].extend(values)
        inv['history'].append({'ts': _now_str(), 'event': 'replenish', 'qty': len(values), 'shop_order_id': response.get('order_id')})
        _save_database_inventory(database_id, inv)
        meta = _load_databases_meta()
        for item in meta['databases']:
            if str(item.get('id')) == str(database_id):
                item['total_added'] = int(item.get('total_added', 0) or 0) + len(values)
                item['updated_at'] = _now_str()
                break
        _save_databases_meta(meta)
    return {'ok': True, 'qty': len(values), 'order_id': response.get('order_id'), 'cost_kop': int(response.get('cost_kop', 0) or 0), 'available': _database_stock(database_id)}
def _persistent_backup_files() -> List[Path]:
    root = Path(STORAGE_DIR)
    result = []
    for name in _STORAGE_TYPES:
        path = root / name
        if path.exists() and path.is_file():
            result.append(path)
    for path in sorted(Path(DATABASES_DIR).glob('*.json')):
        if path.is_file():
            result.append(path)
    return result
def _create_config_backup(reason: str='manual') -> str:
    with _maintenance_lock:
        Path(BACKUPS_DIR).mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        safe_reason = re.sub('[^A-Za-z0-9_-]', '-', str(reason or 'backup'))[:32] or 'backup'
        final = Path(BACKUPS_DIR) / f'dim4n4ik-shop-{safe_reason}-{stamp}.zip'
        tmp = final.with_suffix('.zip.tmp')
        with zipfile.ZipFile(tmp, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            for path in _persistent_backup_files():
                if path.parent == Path(DATABASES_DIR):
                    arc = f'databases/{path.name}'
                else:
                    arc = path.name
                zf.write(path, arc)
        os.replace(tmp, final)
        return str(final)
def _backup_member_expected(name: str):
    clean = name.replace('\\', '/')
    if clean in _STORAGE_TYPES:
        return _STORAGE_TYPES[clean]
    if clean.startswith('databases/') and clean.endswith('.json') and '/' not in clean[len('databases/'):]:
        return dict
    return None
def _validate_backup_archive(path: str) -> Dict[str, Any]:
    try:
        valid = []
        with zipfile.ZipFile(path, 'r') as zf:
            for info in zf.infolist():
                name = info.filename.replace('\\', '/')
                if name.startswith('/') or '..' in Path(name).parts:
                    return {'ok': False, 'error': 'Недопустимый путь внутри архива'}
                expected = _backup_member_expected(name)
                if expected is None:
                    continue
                raw = zf.read(info)
                value = json.loads(raw.decode('utf-8'))
                if not isinstance(value, expected):
                    return {'ok': False, 'error': f'Некорректный тип {name}'}
                valid.append(name)
        if not valid:
            return {'ok': False, 'error': 'В архиве нет данных Dim4n4ik Shop'}
        return {'ok': True, 'files': valid}
    except Exception as e:
        return {'ok': False, 'error': str(e)[:300]}
def _restore_backup_archive(path: str) -> Dict[str, Any]:
    check = _validate_backup_archive(path)
    if not check.get('ok'):
        return check
    pre = _create_config_backup('pre-import')
    restored = []
    try:
        with zipfile.ZipFile(path, 'r') as zf:
            for name in check['files']:
                raw = zf.read(name)
                if name.startswith('databases/'):
                    target = Path(DATABASES_DIR) / Path(name).name
                else:
                    target = Path(STORAGE_DIR) / name
                tmp = target.with_name(target.name + '.import.tmp')
                target.parent.mkdir(parents=True, exist_ok=True)
                with tmp.open('wb') as f:
                    f.write(raw)
                    f.flush()
                    os.fsync(f.fileno())
                expected = _backup_member_expected(name)
                if _raw_json(tmp, expected) is None:
                    tmp.unlink(missing_ok=True)
                    raise ValueError(f'Проверка после записи не прошла: {name}')
                os.replace(tmp, target)
                restored.append(name)
        return {'ok': True, 'restored': restored, 'backup': pre}
    except Exception as e:
        return {'ok': False, 'error': str(e)[:300], 'backup': pre, 'restored': restored}
def _latest_valid_backup() -> Optional[str]:
    for path in sorted(Path(BACKUPS_DIR).glob('*.zip'), reverse=True):
        if _validate_backup_archive(str(path)).get('ok'):
            return str(path)
    return None
def _check_restore_storage() -> Dict[str, Any]:
    invalid = []
    for name, expected in _STORAGE_TYPES.items():
        path = Path(STORAGE_DIR) / name
        if not path.exists() or _raw_json(path, expected) is None:
            invalid.append(name)
    if not invalid:
        return {'ok': True, 'invalid': [], 'restored': []}
    backup = _latest_valid_backup()
    if not backup:
        return {'ok': False, 'invalid': invalid, 'restored': [], 'error': 'Нет подходящей резервной копии'}
    check = _validate_backup_archive(backup)
    restored = []
    with zipfile.ZipFile(backup, 'r') as zf:
        for name in invalid:
            if name not in check.get('files', []):
                continue
            raw = zf.read(name)
            target = Path(STORAGE_DIR) / name
            tmp = target.with_name(target.name + '.repair.tmp')
            with tmp.open('wb') as f:
                f.write(raw)
                f.flush()
                os.fsync(f.fileno())
            if _raw_json(tmp, _STORAGE_TYPES[name]) is None:
                tmp.unlink(missing_ok=True)
                continue
            os.replace(tmp, target)
            restored.append(name)
    remaining = [name for name in invalid if name not in restored]
    return {'ok': not remaining, 'invalid': remaining, 'restored': restored, 'backup': backup}
def _send_document(chat_id, path: str, caption: str='') -> bool:
    if not bot or not Path(path).is_file():
        return False
    try:
        with open(path, 'rb') as f:
            bot.send_document(int(chat_id), f, caption=caption or None, parse_mode='HTML')
        return True
    except Exception as e:
        logger.error(f'{LP} send document: {e}')
        return False
def _save_bindings() -> None:
    with _bindings_lock:
        normalized = _normalize_bindings(_bindings)
        _bindings.clear()
        _bindings.update(normalized)
        save_json(BINDINGS_FILE, _bindings)
def _save_orders_state() -> None:
    with _orders_lock:
        save_json(PENDING_FILE, _pending)
        save_json(PROCESSED_FILE, _processed)
def _append_order_log(entry: Dict[str, Any]) -> None:
    log = load_json(ORDER_LOG_FILE, [])
    if not isinstance(log, list):
        log = []
    log.append(entry)
    save_json(ORDER_LOG_FILE, log[-300:])
def _load_stats() -> Dict[str, Any]:
    stats = load_json(STATS_FILE, None)
    if not isinstance(stats, dict):
        stats = dict(DEFAULT_STATS)
    for k, v in DEFAULT_STATS.items():
        stats.setdefault(k, v if not isinstance(v, dict) else {})
    return stats
def _record_sale(product_id: int, title: str, qty: int, revenue_rub: float, cost_rub: float) -> None:
    with _stats_lock:
        stats = _load_stats()
        stats['total_orders'] += 1
        stats['total_qty'] += qty
        stats['total_revenue_rub'] = round(stats['total_revenue_rub'] + revenue_rub, 2)
        stats['total_cost_rub'] = round(stats['total_cost_rub'] + cost_rub, 2)
        item = stats['items'].setdefault(str(product_id), {'title': title, 'orders': 0, 'qty': 0})
        item['title'] = title
        item['orders'] += 1
        item['qty'] += qty
        stats['last_order_at'] = _now_str()
        save_json(STATS_FILE, stats)
def _record_fail() -> None:
    with _stats_lock:
        stats = _load_stats()
        stats['total_failed'] += 1
        save_json(STATS_FILE, stats)
def _now_str() -> str:
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
def _fmt_rub_kop(kop: Optional[int]) -> str:
    if kop is None:
        return '?'
    return f'{kop / 100:.2f}'.rstrip('0').rstrip('.') + ' ₽'
def _mask_key(key: str) -> str:
    if not key:
        return '❌ не задан'
    return f'rk_live_...{key[-4:]}' if len(key) > 4 else 'rk_live_***'
def _norm_title(s: str) -> str:
    return re.sub('[^\\wа-яё]', '', (s or '').lower())
def _clean_text(s: str) -> str:
    return INVISIBLE_RE.sub('', s or '').strip()
def _parse_price(raw: Any) -> float:
    try:
        if isinstance(raw, (int, float)):
            return float(raw)
        s = re.sub('[^\\d.,]', '', str(raw or '')).replace(',', '.')
        return float(s) if s else 0.0
    except Exception:
        return 0.0
def _tg_send(chat_id, text: str, reply_markup=None) -> None:
    if not bot or not chat_id:
        return
    try:
        bot.send_message(int(chat_id), text, parse_mode='HTML', reply_markup=reply_markup, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f'{LP} tg send error: {e}')
def _tg_edit(chat_id, message_id, text: str, reply_markup=None) -> None:
    if not bot or not chat_id or (not message_id):
        return
    try:
        bot.edit_message_text(text, int(chat_id), int(message_id), parse_mode='HTML', reply_markup=reply_markup, disable_web_page_preview=True)
    except Exception:
        _tg_send(chat_id, text, reply_markup)
def _make_kb(rows: List[List[Tuple[str, str]]]):
    if not tg_types:
        return None
    kb = tg_types.InlineKeyboardMarkup()
    for row in rows:
        kb.row(*[tg_types.InlineKeyboardButton(text, callback_data=data) for text, data in row])
    return kb
def _is_authorized(user_id) -> bool:
    try:
        auth = getattr(getattr(cardinal, 'telegram', None), 'authorized_users', None)
        if isinstance(auth, dict):
            return user_id in auth or int(user_id) in auth
    except Exception:
        pass
    return True
NOTIFY_KEYS = {'new_order': 'notify_new_order', 'success': 'notify_success', 'failure': 'notify_failure', 'error': 'notify_errors', 'low_balance': 'notify_low_balance', 'out_of_stock': 'notify_out_of_stock'}
def _notify_admin(text: str, keyboard=None, etype: Optional[str]=None) -> None:
    if etype:
        if not cfg_get('notifications_enabled'):
            return
        key = NOTIFY_KEYS.get(etype)
        if key and (not cfg_get(key)):
            return
    if admin_chat_id:
        _tg_send(admin_chat_id, text, keyboard)
def _fp_send(chat_id, text: str, buyer_username: Optional[str]=None) -> bool:
    if cardinal is None:
        return False
    cid = None
    try:
        cid = int(chat_id)
    except Exception:
        pass
    if cid is None and buyer_username:
        try:
            chat = cardinal.account.get_chat_by_name(buyer_username, True)
            if chat:
                cid = int(chat.id)
        except Exception as e:
            logger.error(f'{LP} get_chat_by_name({buyer_username}): {e}')
    if cid is None:
        logger.error(f'{LP} нет chat_id для отправки покупателю')
        return False
    for attempt in range(3):
        try:
            cardinal.account.send_message(cid, text)
            return True
        except Exception as e:
            logger.warning(f'{LP} fp send attempt {attempt + 1}: {e}')
            time.sleep(2 * (attempt + 1))
    return False
def _mark_order_delivered(order_id: str) -> None:
    oid = str(order_id)
    with _orders_lock:
        current = _pending.get(oid)
        if current is not None:
            current['step'] = 'delivered'
            current['delivered_at'] = time.time()
        _processed[oid] = time.time()
        _save_orders_state()
    _log_event('order_delivered_marker', order_id=oid)
def _send_goods(order_id: str, chat_id, buyer_username: Optional[str], values: List[str], product_title: str='', qty: int=0) -> Dict[str, Any]:
    order_url = f'https://funpay.com/orders/{order_id}/'
    header = _buyer_message('goods_header', order_id=order_id, order_url=order_url, product_title=product_title, qty=qty)
    chunks: List[str] = []
    cur: List[str] = []
    cur_len = 0
    for v in values:
        v = str(v).strip()
        if not v:
            continue
        if cur and (cur_len + len(v) + 1 > BUYER_MSG_LIMIT or len(cur) >= BUYER_MSG_MAX_LINES):
            chunks.append('\n'.join(cur))
            cur, cur_len = ([], 0)
        cur.append(v)
        cur_len += len(v) + 1
    if cur:
        chunks.append('\n'.join(cur))
    header_sent = _fp_send(chat_id, header, buyer_username)
    goods_messages: List[str] = list(chunks)
    results = []
    for ch in goods_messages:
        results.append(_fp_send(chat_id, ch, buyer_username))
        if len(goods_messages) > 1:
            time.sleep(0.5)
    goods_sent = bool(results) and all(results)
    goods_partial = any(results) and not goods_sent
    if goods_sent:
        _mark_order_delivered(str(order_id))
    footer = _buyer_message('goods_footer', order_id=order_id, order_url=order_url, product_title=product_title, qty=qty)
    footer_sent = _fp_send(chat_id, footer, buyer_username) if goods_sent else False
    _log_event('funpay_delivery', order_id=order_id, goods_messages=len(goods_messages), goods_sent=goods_sent, goods_partial=goods_partial, header_sent=header_sent, footer_sent=footer_sent)
    return {'goods_sent': goods_sent, 'goods_partial': goods_partial, 'header_sent': bool(header_sent), 'footer_sent': bool(footer_sent), 'goods_messages': len(goods_messages)}
def _try_refund(order_id: str) -> bool:
    try:
        cardinal.account.refund(str(order_id))
        logger.info(f'{LP} #{order_id} возврат выполнен')
        return True
    except Exception as e:
        logger.error(f'{LP} #{order_id} refund error: {e}')
        return False
class ShopApiError(Exception):
    def __init__(self, http: int, code: str, message: str, extra: Optional[dict]=None):
        super().__init__(f'{code}: {message}')
        self.http = http
        self.code = code
        self.message = message
        self.extra = extra or {}
class ShopNetworkError(Exception):
    pass
class ShopClient:
    def __init__(self, api_key: str, base_url: str='https://api.dim4n4ik.shop'):
        self.api_key = (api_key or '').strip()
        self.base_url = (base_url or 'https://api.dim4n4ik.shop').rstrip('/')
    def _request(self, method: str, path: str, body: Optional[dict]=None, idem_key: Optional[str]=None, timeout: int=30, max_attempts: int=5) -> dict:
        url = self.base_url + path
        headers = {'Authorization': f'Bearer {self.api_key}', 'Accept': 'application/json', 'User-Agent': f'dim4n4ikshop-cardinal/{VERSION}'}
        if idem_key:
            headers['Idempotency-Key'] = idem_key
        last_net: Optional[Exception] = None
        for attempt in range(1, max_attempts + 1):
            started = time.monotonic()
            try:
                r = requests.request(method, url, json=body, headers=headers, timeout=timeout)
                _log_event('api_request', method=method, path=path, status=r.status_code, attempt=attempt, ms=int((time.monotonic() - started) * 1000))
            except (requests.Timeout, requests.ConnectionError) as e:
                last_net = e
                _log_event('api_network_error', level=logging.WARNING, method=method, path=path, attempt=attempt, error=type(e).__name__, ms=int((time.monotonic() - started) * 1000))
                logger.warning(f'{LP} api network {method} {path} attempt {attempt}: {e}')
                time.sleep(min(2 * attempt + random.uniform(0, 1), 15))
                continue
            except requests.RequestException as e:
                last_net = e
                _log_event('api_request_error', level=logging.WARNING, method=method, path=path, attempt=attempt, error=type(e).__name__, ms=int((time.monotonic() - started) * 1000))
                time.sleep(2)
                continue
            if r.status_code == 200:
                try:
                    return r.json()
                except ValueError:
                    raise ShopApiError(200, 'bad_json', 'Некорректный JSON в ответе API')
            err: Dict[str, Any] = {}
            try:
                err = (r.json() or {}).get('error') or {}
            except ValueError:
                pass
            code = err.get('code') or f'http_{r.status_code}'
            message = err.get('message') or (r.text or '')[:200]
            if r.status_code == 429 and code != 'quota_exceeded':
                try:
                    wait = min(int(r.headers.get('Retry-After', '2')), 30)
                except Exception:
                    wait = 2 * attempt
                time.sleep(wait)
                continue
            if code == 'in_progress':
                time.sleep(3)
                continue
            if r.status_code >= 500:
                time.sleep(min(2 * attempt, 10))
                continue
            raise ShopApiError(r.status_code, code, message, err)
        if last_net is not None:
            raise ShopNetworkError(str(last_net))
        raise ShopNetworkError('превышено число попыток запроса к API')
    def ping(self) -> dict:
        return self._request('GET', '/v1/ping', timeout=15, max_attempts=2)
    def get_catalog(self) -> List[dict]:
        data = self._request('GET', '/v1/catalog', timeout=30)
        return data if isinstance(data, list) else []
    def get_balance_kop(self) -> int:
        return int(self._request('GET', '/v1/balance', timeout=30).get('balance_kop', 0))
    def create_order(self, product_id: int, qty: int, idem_key: str) -> dict:
        return self._request('POST', '/v1/orders', body={'product_id': int(product_id), 'qty': int(qty)}, idem_key=idem_key, timeout=200, max_attempts=4)
    def get_order(self, order_id: int) -> dict:
        return self._request('GET', f'/v1/orders/{int(order_id)}', timeout=60)
def _get_client() -> Optional[ShopClient]:
    global shop_client
    key = cfg_get('api_key')
    base = (cfg_get('base_url') or 'https://api.dim4n4ik.shop').rstrip('/')
    if not key:
        return None
    if shop_client is None or shop_client.api_key != key or shop_client.base_url != base:
        shop_client = ShopClient(key, base)
    return shop_client
def _get_catalog_cached(max_age: float=60.0) -> List[dict]:
    client = _get_client()
    if client is None:
        return []
    now = time.time()
    if now - _catalog_cache['ts'] < max_age and _catalog_cache['items']:
        return _catalog_cache['items']
    items = client.get_catalog()
    _catalog_cache['ts'] = now
    _catalog_cache['items'] = items
    return items
def _refresh_balance() -> Optional[int]:
    global _last_balance_kop, _last_balance_ts
    client = _get_client()
    if client is None:
        return None
    bal = client.get_balance_kop()
    _last_balance_kop = bal
    _last_balance_ts = time.time()
    return bal
NO_CATEGORY = 'Без категории'
NO_GROUP = 'Без группы'
MAIL_CAT_RE = re.compile('почт|e-?mail|outlook|hotmail', re.IGNORECASE)
_cat_idx: List[str] = []
_allcat_idx: List[str] = []
_grp_idx: List[str] = []
def _cat_name(it: dict) -> str:
    return it.get('category') or NO_CATEGORY
def _auto_hidden_categories(catalog: List[dict]) -> List[str]:
    return []
def _hidden_categories(catalog: List[dict]) -> set:
    hidden = cfg_get('hidden_categories')
    if not cfg_get('mail_catalog_migrated'):
        if isinstance(hidden, (list, tuple, set)):
            cleaned = [str(x) for x in hidden if not MAIL_CAT_RE.search(str(x))]
            if cleaned != list(hidden):
                cfg_set('hidden_categories', cleaned)
                hidden = cleaned
        cfg_set('mail_catalog_migrated', True)
    if hidden is None:
        hidden = _auto_hidden_categories(catalog)
        cfg_set('hidden_categories', hidden)
    return set(hidden)
def _is_text_kind(it: dict) -> bool:
    return str(it.get('kind') or 'text').lower() in ('text', 'steam')
def _visible_catalog(catalog: Optional[List[dict]]=None) -> List[dict]:
    if catalog is None:
        catalog = _get_catalog_cached()
    hidden = _hidden_categories(catalog)
    return [it for it in catalog if _cat_name(it) not in hidden and _is_text_kind(it)]
def _ordered_categories(items: List[dict]) -> List[str]:
    seen: List[str] = []
    for it in items:
        c = _cat_name(it)
        if c not in seen:
            seen.append(c)
    return seen
def _binding_groups() -> List[str]:
    with _bindings_lock:
        groups = {b.get('group') or '' for b in _bindings.values()}
    return sorted((g for g in groups if g))
def _rename_group(old: str, new: str) -> int:
    n = 0
    with _bindings_lock:
        for b in _bindings.values():
            if (b.get('group') or '') == old:
                b['group'] = new
                n += 1
        if n:
            _save_bindings()
    return n
def _sync_lot(lot_id: str, product_id: int) -> Tuple[Optional[str], bool, Optional[str]]:
    try:
        lf = cardinal.account.get_lot_fields(int(lot_id))
    except Exception as e:
        return (None, False, f'не удалось прочитать лот: {e}')
    title = (getattr(lf, 'title_ru', '') or getattr(lf, 'title_en', '') or '').strip()
    tag = f'd4s:{product_id}'
    changed = False
    try:
        desc_ru = getattr(lf, 'description_ru', '') or ''
        if tag not in desc_ru:
            base = TAG_RE.sub('', desc_ru).rstrip()
            lf.description_ru = base + ('\n\n' if base else '') + tag
            changed = True
        desc_en = getattr(lf, 'description_en', '') or ''
        if desc_en and tag not in desc_en:
            base = TAG_RE.sub('', desc_en).rstrip()
            lf.description_en = base + ('\n\n' if base else '') + tag
            changed = True
        if changed:
            cardinal.account.save_lot(lf)
    except Exception as e:
        return (title or None, False, f'тег не вписан: {e}')
    return (title or None, changed, None)
def _parse_lot_ids(text: str) -> List[str]:
    ids: List[str] = []
    for tok in re.split('[\\s,;]+', (text or '').strip()):
        if not tok:
            continue
        m = re.search('id=(\\d+)', tok)
        lot_id = m.group(1) if m else tok if tok.isdigit() else None
        if lot_id and lot_id not in ids:
            ids.append(lot_id)
    return ids
def _set_lot_active(lot_id: str, active: bool) -> bool:
    for attempt in range(3):
        try:
            lf = cardinal.account.get_lot_fields(int(lot_id))
            if bool(getattr(lf, 'active', None)) == active:
                return True
            lf.active = active
            cardinal.account.save_lot(lf)
            return True
        except Exception as e:
            logger.warning(f'{LP} set_lot_active({lot_id},{active}) attempt {attempt + 1}: {e}')
            time.sleep(3 * (attempt + 1))
    return False
STUB_SECRET = 'Оплачено ✅ Ваш аккаунт придёт в этот чат в течение минуты.'
FP_AUTO_BUFFER = 25
def _fp_buffer() -> int:
    try:
        return max(1, int(cfg_get('fp_auto_buffer') or FP_AUTO_BUFFER))
    except Exception:
        return FP_AUTO_BUFFER
def _binding_qty_per_unit(binding: Dict[str, Any]) -> int:
    try:
        return max(1, int(binding.get('qty_per_unit', binding.get('qty', 1)) or 1))
    except Exception:
        return 1
def _binding_stock_target(binding: Dict[str, Any]) -> int:
    raw = binding.get('fp_stock_target')
    if raw is None:
        raw = _fp_buffer() if binding.get('fp_auto') else 0
    try:
        return max(0, min(500, int(raw or 0)))
    except Exception:
        return 0
def _binding_source_stock(binding: Dict[str, Any], max_age: float=60.0) -> int:
    mode = str(binding.get('delivery_mode') or 'api')
    if mode == 'database':
        database_id = str(binding.get('database_id') or '')
        if not database_id:
            return 0
        return _database_stock(database_id)
    try:
        return _product_stock(int(binding.get('product_id')), max_age=max_age)
    except Exception:
        return 0
def _binding_effective_stock(binding: Dict[str, Any], max_age: float=60.0) -> int:
    return max(0, _binding_source_stock(binding, max_age=max_age) // _binding_qty_per_unit(binding))
def _binding_effective_stock_cached(binding: Dict[str, Any]) -> Optional[int]:
    if str(binding.get('delivery_mode') or 'api') == 'database':
        return max(0, _database_stock(str(binding.get('database_id') or '')) // _binding_qty_per_unit(binding))
    try:
        pid = int(binding.get('product_id'))
    except Exception:
        return None
    for item in list(_catalog_cache.get('items') or []):
        try:
            if int(item.get('id', -1)) == pid:
                return max(0, int(item.get('in_stock', 0)) // _binding_qty_per_unit(binding))
        except Exception:
            continue
    return None
def _sync_binding_stock(lot_id: str, binding: Dict[str, Any]) -> Tuple[bool, int]:
    effective = _binding_effective_stock(binding, max_age=30.0)
    limit = _binding_stock_target(binding)
    target = min(effective, limit) if limit > 0 else 0
    for attempt in range(4):
        try:
            lf = cardinal.account.get_lot_fields(int(lot_id))
            cur = len(getattr(lf, 'secrets', None) or [])
            if target >= 1:
                if getattr(lf, 'auto_delivery', False) and cur == target and getattr(lf, 'active', True):
                    return (True, target)
                lf.auto_delivery = True
                lf.secrets = [STUB_SECRET] * target
                lf.active = True
            else:
                if limit > 0:
                    lf.auto_delivery = False
                    lf.secrets = []
                if bool(cfg_get('auto_lots_by_stock')) and effective <= 0:
                    lf.active = False
            cardinal.account.save_lot(lf)
            return (True, target)
        except Exception as e:
            if target > 1 and 'слишком длинн' in str(e).lower():
                target = max(1, target // 2)
                time.sleep(1)
                continue
            logger.warning(f'{LP} sync binding stock({lot_id}) attempt {attempt + 1}: {e}')
            time.sleep(2 * (attempt + 1))
    return (False, target)
def _sync_fp_stock(lot_id: str, product_id: int) -> Tuple[bool, int]:
    with _bindings_lock:
        existing = dict(_bindings.get(str(lot_id)) or {})
    if existing:
        return _sync_binding_stock(str(lot_id), _normalize_binding(existing))
    binding = {'delivery_mode': 'api', 'product_id': int(product_id), 'qty_per_unit': 1, 'fp_stock_target': _fp_buffer(), 'fp_auto': True}
    return _sync_binding_stock(str(lot_id), binding)
def _disable_fp_autodelivery(lot_id: str) -> bool:
    for attempt in range(3):
        try:
            lf = cardinal.account.get_lot_fields(int(lot_id))
            lf.auto_delivery = False
            lf.secrets = []
            cardinal.account.save_lot(lf)
            return True
        except Exception as e:
            logger.warning(f'{LP} disable_fp_ad({lot_id}) attempt {attempt + 1}: {e}')
            time.sleep(2 * (attempt + 1))
    return False
def _product_stock(product_id: int, max_age: float=60.0) -> int:
    try:
        for it in _get_catalog_cached(max_age=max_age):
            if int(it.get('id', -1)) == int(product_id):
                return int(it.get('in_stock', 0))
    except Exception:
        pass
    return 0
def _product_price_kop(product_id: int, max_age: float=60.0) -> int:
    try:
        for it in _get_catalog_cached(max_age=max_age):
            if int(it.get('id', -1)) == int(product_id):
                return int(it.get('price_kop', 0))
    except Exception:
        pass
    return 0
def _delete_lot_fp(lot_id: str) -> bool:
    for attempt in range(3):
        try:
            cardinal.account.delete_lot(int(lot_id))
            return True
        except Exception as e:
            logger.warning(f'{LP} delete_lot({lot_id}) attempt {attempt + 1}: {e}')
            time.sleep(2 * (attempt + 1))
    return False
def _save_auto_disabled() -> None:
    save_json(AUTO_DISABLED_FILE, _auto_disabled)
def _apply_lot_sync(lot_id: str, product_id: int) -> str:
    title, wrote, err = _sync_lot(lot_id, product_id)
    if title:
        with _bindings_lock:
            if lot_id in _bindings:
                _bindings[lot_id]['lot_name'] = title
                _save_bindings()
    parts = []
    parts.append(f'🏷 Название: «{title}»' if title else '⚠️ Название не прочиталось')
    if wrote:
        parts.append(f'✍️ Тег <code>d4s:{product_id}</code> вписан в описание лота')
    elif not err:
        parts.append('✔️ Тег уже в описании')
    if err:
        parts.append(f'⚠️ {err}\nВпишите тег <code>d4s:{product_id}</code> в описание вручную')
    return '\n'.join(parts)
_FLAG_RE = re.compile('[\\U0001F1E6-\\U0001F1FF]{2}')
def _country_pair(src_product: str, dst_product: str) -> Tuple[Optional[str], Optional[str]]:
    def toks(s: str) -> List[str]:
        return [t for t in re.split('\\s+', _FLAG_RE.sub('', s or '').strip()) if t]
    st, dt = (toks(src_product), toks(dst_product))
    common = {w.lower() for w in st} & {w.lower() for w in dt}
    sd = [w for w in st if w.lower() not in common]
    dd = [w for w in dt if w.lower() not in common]
    def pick(lst: List[str]) -> Optional[str]:
        cand = [w for w in lst if any((ch.isalpha() for ch in w))]
        return max(cand, key=len) if cand else lst[0] if lst else None
    return (pick(sd), pick(dd))
def _region_field_for_lot(source_lot_id: str, src_country: str, dst_country: str) -> Tuple[Optional[str], Optional[str]]:
    if not src_country or not dst_country:
        return (None, None)
    try:
        resp = cardinal.account.method('get', f'lots/offerEdit?offer={source_lot_id}', {}, {}, raise_not_200=True)
        html_txt = resp.content.decode()
    except Exception as e:
        logger.warning(f'{LP} region form fetch({source_lot_id}): {e}')
        return (None, None)
    try:
        from bs4 import BeautifulSoup
        bs = BeautifulSoup(html_txt, 'lxml')
        form = bs.find('form', class_='form-offer-editor') or bs
        sl, dl = (src_country.lower(), dst_country.lower())
        for sel in form.find_all('select'):
            name = sel.get('name')
            if not name:
                continue
            opts = {opt.get_text(strip=True).lower(): opt.get('value') or '' for opt in sel.find_all('option')}
            if sl in opts and dl in opts:
                return (name, opts[dl])
    except Exception as e:
        logger.warning(f'{LP} region parse: {e}')
    return (None, None)
def _country_swapped_title(lot_title: str, src_product: str, dst_product: str) -> Optional[str]:
    if not lot_title or not src_product or (not dst_product):
        return None
    out = lot_title
    changed = False
    sf = _FLAG_RE.search(src_product)
    df = _FLAG_RE.search(dst_product)
    if sf and df and (sf.group(0) in out):
        out = out.replace(sf.group(0), df.group(0))
        changed = True
    def toks(s: str) -> List[str]:
        return [t for t in re.split('\\s+', _FLAG_RE.sub('', s).strip()) if t]
    st, dt = (toks(src_product), toks(dst_product))
    common = {w.lower() for w in st} & {w.lower() for w in dt}
    sd = [w for w in st if w.lower() not in common]
    dd = [w for w in dt if w.lower() not in common]
    for i in range(min(len(sd), len(dd))):
        pat = re.compile(re.escape(sd[i]), re.IGNORECASE)
        if pat.search(out):
            out = pat.sub(dd[i], out)
            changed = True
    return out if changed else None
def _copy_lot(source_lot_id: str, product_id: int, dst_product_title: str, qty: int, group: str, src_product_title: str='') -> Tuple[Optional[str], Optional[str], Optional[str]]:
    try:
        lf = cardinal.account.get_lot_fields(int(source_lot_id))
    except Exception as e:
        return (None, None, None, f'не удалось прочитать исходный лот {source_lot_id}: {e}')
    subcat_id = getattr(getattr(lf, 'subcategory', None), 'id', None)
    if not subcat_id:
        return (None, None, None, 'не удалось определить категорию исходного лота')
    src_lot_title = getattr(lf, 'title_ru', '') or ''
    new_title = _country_swapped_title(src_lot_title, src_product_title, dst_product_title) or dst_product_title or src_lot_title
    region_note = ''
    sc, dc = _country_pair(src_product_title, dst_product_title)
    if sc and dc and (sc.lower() != dc.lower()):
        fname, fval = _region_field_for_lot(source_lot_id, sc, dc)
        if fname is not None:
            try:
                lf.edit_fields({fname: fval})
                region_note = dc
            except Exception as e:
                logger.warning(f'{LP} region set: {e}')
    with _lot_create_lock:
        try:
            before = {str(l.id) for l in cardinal.account.get_my_subcategory_lots(int(subcat_id))}
        except Exception as e:
            return (None, None, None, f'не удалось получить список лотов категории: {e}')
        lf.lot_id = 0
        lf.secrets = []
        lf.auto_delivery = False
        if new_title:
            lf.title_ru = new_title[:90]
        try:
            lf.description_ru = TAG_RE.sub('', getattr(lf, 'description_ru', '') or '').rstrip()
        except Exception:
            pass
        try:
            cardinal.account.save_lot(lf)
        except Exception as e:
            return (None, None, None, f'FunPay отклонил создание лота: {e}')
        time.sleep(2.5)
        try:
            after = {str(l.id) for l in cardinal.account.get_my_subcategory_lots(int(subcat_id))}
        except Exception as e:
            return (None, None, None, f'лот создан, но не удалось найти его id: {e}')
    new_ids = list(after - before)
    if not new_ids:
        return (None, None, None, 'лот создан, но не появился в списке — возможно, FunPay сохранил его выключенным (лимит лотов/премиум). Проверьте на FunPay.')
    new_lot_id = max(new_ids, key=int) if all((i.isdigit() for i in new_ids)) else new_ids[0]
    with _bindings_lock:
        _bindings[new_lot_id] = {'product_id': int(product_id), 'product_title': dst_product_title, 'qty': int(qty), 'group': group, 'lot_name': '', 'enabled': True, 'created_at': _now_str()}
        _save_bindings()
    _apply_lot_sync(new_lot_id, int(product_id))
    return (new_lot_id, lf.title_ru if new_title else dst_product_title, region_note or None, None)
def _configured_bindings() -> Dict[str, Dict[str, Any]]:
    with _bindings_lock:
        return {str(k): _normalize_binding(v) for k, v in _bindings.items() if isinstance(v, dict)}
def _enabled_bindings() -> Dict[str, Dict[str, Any]]:
    with _bindings_lock:
        return {str(k): _normalize_binding(v) for k, v in _bindings.items() if isinstance(v, dict) and v.get('enabled', True)}
def _object_value(value: Any, key: str) -> Any:
    if isinstance(value, dict):
        return value.get(key)
    return getattr(value, key, None)
def _lot_id_text(value: Any) -> Optional[str]:
    if isinstance(value, bool) or value is None:
        return None
    try:
        text = str(value).strip()
    except Exception:
        return None
    return text if text.isdigit() and int(text) > 0 else None
def _lot_id_candidates(value: Any, prefix: str, depth: int=0, seen=None) -> List[Tuple[str, str]]:
    if value is None or depth > 3:
        return []
    if seen is None:
        seen = set()
    marker = id(value)
    if marker in seen:
        return []
    seen.add(marker)
    result = []
    for key in ('lot_id', 'offer_id'):
        candidate = _lot_id_text(_object_value(value, key))
        if candidate:
            result.append((f'{prefix}.{key}', candidate))
    for key in ('lot', 'offer', 'node', 'fields', 'data'):
        child = _object_value(value, key)
        if child is None:
            continue
        scalar = _lot_id_text(child)
        if scalar and key in ('lot', 'offer'):
            result.append((f'{prefix}.{key}', scalar))
            continue
        child_id = _lot_id_text(_object_value(child, 'id'))
        if child_id and key in ('lot', 'offer'):
            result.append((f'{prefix}.{key}.id', child_id))
        result.extend(_lot_id_candidates(child, f'{prefix}.{key}', depth + 1, seen))
    unique = []
    known = set()
    for source, lot_id in result:
        pair = (source, lot_id)
        if pair not in known:
            known.add(pair)
            unique.append(pair)
    return unique
def _order_texts(value: Any) -> List[str]:
    result = []
    for attr in ('full_description', 'description', 'short_description', 'title'):
        raw = _object_value(value, attr)
        if raw:
            text = _clean_text(str(raw))
            if text and text not in result:
                result.append(text)
    return result
def _binding_exact_titles(bindings: Dict[str, Dict[str, Any]]) -> Dict[str, set]:
    result = {str(key): set() for key in bindings}
    cache = {str(item.get('lot_id')): str(item.get('title') or '') for item in _cached_funpay_lots() if isinstance(item, dict)}
    for key, binding in bindings.items():
        for raw in (binding.get('lot_name'), cache.get(str(key))):
            text = _clean_text(str(raw or '')).casefold()
            if text:
                result[str(key)].add(text)
    return result
def _find_binding(order, event) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    bindings = _configured_bindings()
    if not bindings:
        return (None, None)
    oid = str(_object_value(order, 'id') or '')
    candidates = []
    candidates.extend(_lot_id_candidates(event, 'event'))
    candidates.extend(_lot_id_candidates(order, 'order'))
    texts = _order_texts(order)
    full = None
    if cardinal is not None and getattr(cardinal, 'account', None) is not None and oid:
        try:
            full = cardinal.account.get_order(oid)
            candidates.extend(_lot_id_candidates(full, 'get_order'))
            for text in _order_texts(full):
                if text not in texts:
                    texts.append(text)
        except Exception as e:
            logger.warning(f'{LP} get_order({oid}) для матчинга: {e}')
    seen_ids = []
    for source, lot_id in candidates:
        if lot_id not in seen_ids:
            seen_ids.append(lot_id)
        if lot_id in bindings:
            logger.info(f'{LP} #{oid or "?"} matched lot={lot_id} source={source}')
            return (lot_id, bindings[lot_id])
    for txt in texts:
        m = TAG_RE.search(txt or '')
        if m:
            pid = int(m.group(1))
            matches = [(k, b) for k, b in bindings.items() if int(b.get('product_id', -1)) == pid]
            if len(matches) == 1:
                logger.info(f'{LP} #{oid or "?"} matched lot={matches[0][0]} source=description_tag')
                return matches[0]
    exact_titles = _binding_exact_titles(bindings)
    for txt in texts:
        exact = _clean_text(txt).casefold()
        if not exact:
            continue
        matches = [key for key, names in exact_titles.items() if exact in names]
        if len(matches) == 1:
            key = matches[0]
            logger.info(f'{LP} #{oid or "?"} matched lot={key} source=exact_title')
            return (key, bindings[key])
    title = texts[0] if texts else ''
    if title and cfg_get('match_by_title'):
        norm = _norm_title(title)
        matches = []
        for key, binding in bindings.items():
            lot_name = binding.get('lot_name') or ''
            if lot_name and _norm_title(lot_name) == norm:
                matches.append(key)
        if len(matches) == 1:
            key = matches[0]
            logger.info(f'{LP} #{oid or "?"} matched lot={key} source=normalized_title')
            return (key, bindings[key])
    _log_event('binding_miss', order_id=oid or '?', candidate_lot_ids=','.join(seen_ids) if seen_ids else 'none', configured_lot_ids=','.join(sorted(bindings.keys())) if bindings else 'none', title=title[:160] or 'none')
    logger.info(f'{LP} #{oid or "?"} binding not found: lot_ids={seen_ids or "none"} configured={list(bindings.keys()) or "none"} title={title[:160] or "none"}')
    return (None, None)
def handle_new_order(cardinal_obj, event, *args) -> None:
    global cardinal
    if cardinal is None:
        cardinal = cardinal_obj
    if not cfg_get('plugin_enabled'):
        return
    order = getattr(event, 'order', None) or event
    oid = str(getattr(order, 'id', '') or '')
    if not oid:
        return
    with _orders_lock:
        if oid in _processed or oid in _pending or oid in _seen:
            return
        _seen.add(oid)
    try:
        key, raw_binding = _find_binding(order, event)
        binding = _normalize_binding(raw_binding) if raw_binding else None
    except Exception as e:
        logger.error(f'{LP} #{oid} ошибка матчинга: {e}')
        key, binding = (None, None)
    if not binding:
        with _orders_lock:
            _seen.discard(oid)
            if getattr(event, 'lot_id', None) is not None:
                _rejected[oid] = time.time()
                if len(_rejected) > 1000:
                    for k in sorted(_rejected, key=_rejected.get)[:500]:
                        _rejected.pop(k, None)
        return
    amount = getattr(order, 'amount', None)
    try:
        amount = max(int(amount), 1)
    except Exception:
        amount = 1
    per_sale = _binding_qty_per_unit(binding)
    qty = per_sale * amount
    mode = str(binding.get('delivery_mode') or 'api')
    database_id = str(binding.get('database_id') or '')
    product_id = int(binding.get('product_id') or 0)
    product_title = str(binding.get('product_title') or f'товар {product_id}')
    if mode == 'database':
        db = _database_by_id(database_id)
        if db:
            product_id = int(db['product_id'])
            product_title = str(db.get('product_title') or product_title)
    currency = ''
    try:
        cur = getattr(order, 'currency', None)
        currency = str(getattr(cur, 'code', None) or cur or '').lower()
    except Exception:
        pass
    od = {'order_id': oid, 'lot_key': key, 'delivery_mode': mode, 'database_id': database_id, 'product_id': product_id, 'product_title': product_title, 'qty_per_unit': per_sale, 'fp_stock_target': _binding_stock_target(binding), 'qty': qty, 'amount': amount, 'price_rub': _parse_price(getattr(order, 'price', None) if getattr(order, 'price', None) is not None else getattr(order, 'sum', None)), 'currency': currency, 'buyer': getattr(order, 'buyer_username', None) or '', 'chat_id': getattr(order, 'chat_id', None), 'step': 'processing', 'attempt': 0, 'idem_key': f'fp-{oid}', 'shop_order_id': None, 'cost_kop': None, 'error': '', 'created_at': time.time(), 'created_at_str': _now_str()}
    with _orders_lock:
        _pending[oid] = od
        _seen.discard(oid)
        _save_orders_state()
    source = 'база' if mode == 'database' else 'API'
    logger.info(f"{LP} #{oid} наш заказ: lot={key} mode={mode} product={product_id} qty={qty} price={od['price_rub']} {currency}")
    _log_event('order_received', order_id=oid, lot_id=key, mode=mode, product_id=product_id, qty=qty, buyer=od['buyer'])
    _notify_admin(f"🛒 <b>Новый заказ #{oid}</b>\n📦 {product_title} ×{qty}\n👤 {od['buyer']}\n🚚 Источник: {source}\n💵 Продажа: {od['price_rub']:.2f} {od['currency'] or '₽'}", etype='new_order')
    if qty > FUNPAY_ORDER_QTY_MAX:
        _fail_order(oid, ShopApiError(0, 'qty_limit', f'Запрошено {qty} шт., максимум автоматической выдачи FunPay — {FUNPAY_ORDER_QTY_MAX} шт. за заказ'))
        return
    _fp_send(od['chat_id'], _buyer_message('payment_received', order_id=oid, order_url=f'https://funpay.com/orders/{oid}/', product_title=product_title, qty=qty), od['buyer'])
    threading.Thread(target=process_order, args=(oid,), daemon=True).start()
def _api_delivery_payload(resp: Dict[str, Any], expected_qty: int) -> Dict[str, Any]:
    items = resp.get('items') if isinstance(resp, dict) else []
    items = items if isinstance(items, list) else []
    files = [it for it in items if isinstance(it, dict) and str(it.get('type') or '').lower() == 'file']
    values = [str(it.get('value')) for it in items if isinstance(it, dict) and str(it.get('type') or 'text').lower() in ('text', 'steam') and it.get('value')]
    try:
        reported_qty = int(resp.get('qty', expected_qty) or expected_qty)
    except Exception:
        reported_qty = expected_qty
    if files:
        return {'ok': False, 'final': True, 'values': values, 'reason': f'API вернул файловый товар ({len(files)} файл/файлов). Автовыдача FunPay поддерживает только text/steam value.'}
    if reported_qty != expected_qty:
        return {'ok': False, 'final': False, 'values': values, 'reason': f'API сообщает qty={reported_qty}, ожидалось {expected_qty}'}
    if len(values) != expected_qty:
        return {'ok': False, 'final': False, 'values': values, 'reason': f'API вернул {len(values)} текстовых позиций вместо {expected_qty}'}
    return {'ok': True, 'final': True, 'values': values, 'reason': ''}
def _fulfill_api_order(od: Dict[str, Any]) -> Dict[str, Any]:
    client = _get_client()
    if client is None:
        raise ShopApiError(0, 'no_api_key', 'API-ключ не задан (⚙️ Настройки → Аккаунт dim4n4ik.shop)')
    need = int(od.get('qty', 1) or 1)
    if not od.get('shop_order_id'):
        try:
            if _product_stock(int(od['product_id'])) < need and _product_stock(int(od['product_id']), max_age=0) < need:
                raise ShopApiError(409, 'out_of_stock', 'Товар закончился на складе магазина', {'available': 0})
        except ShopApiError:
            raise
        except Exception:
            pass
    if not od.get('shop_order_id') and cfg_get('loss_protection'):
        try:
            price_rub = float(od.get('price_rub') or 0)
            cat_kop = _product_price_kop(int(od['product_id']))
            cur = (od.get('currency') or '').lower()
            if cur in ('', 'rub', '₽') and price_rub > 0 and cat_kop > 0:
                cost_rub = cat_kop * need / 100.0
                margin = float(cfg_get('loss_min_margin_percent') or 0)
                floor = cost_rub * (1 + margin / 100.0)
                if price_rub + 1e-06 < floor:
                    suffix = f' + маржа {margin:.0f}%' if margin else ''
                    raise ShopApiError(0, 'loss_block', f'Цена лота {price_rub:.2f} ₽ ниже закупки {cost_rub:.2f} ₽{suffix} — продажа заблокирована (защита от убытка). Поднимите цену лота.')
        except ShopApiError:
            raise
        except Exception:
            pass
    if od.get('shop_order_id'):
        resp = client.get_order(od['shop_order_id'])
    else:
        _log_event('api_purchase_start', order_id=od.get('order_id'), product_id=od.get('product_id'), qty=need)
        resp = client.create_order(int(od['product_id']), need, str(od['idem_key']))
        _catalog_cache['ts'] = 0.0
        _catalog_cache['items'] = []
        with _orders_lock:
            od['shop_order_id'] = resp.get('order_id')
            od['cost_kop'] = resp.get('cost_kop')
            od['step'] = 'purchased'
            _save_orders_state()
        _log_event('api_purchase_done', order_id=od.get('order_id'), shop_order_id=od.get('shop_order_id'), qty=need, cost_kop=od.get('cost_kop'))
    check = _api_delivery_payload(resp, need)
    if not check['ok'] and not check['final'] and od.get('shop_order_id'):
        for attempt in range(1, 4):
            time.sleep(1 if attempt == 1 else 2)
            resp = client.get_order(int(od['shop_order_id']))
            if od.get('cost_kop') is None:
                od['cost_kop'] = resp.get('cost_kop')
            check = _api_delivery_payload(resp, need)
            _log_event('api_order_refetch', order_id=od.get('order_id'), shop_order_id=od.get('shop_order_id'), attempt=attempt, ready=check['ok'], received=len(check.get('values') or []), expected=need)
            if check['ok'] or check['final']:
                break
    cost_kop = int(od.get('cost_kop') or (resp.get('cost_kop') if isinstance(resp, dict) else 0) or 0)
    if not check['ok']:
        return {'status': 'manual', 'reason': check['reason'], 'values': list(check.get('values') or []), 'cost_kop': cost_kop}
    return {'status': 'ready', 'values': list(check['values']), 'cost_kop': cost_kop, 'source': 'api'}
def _fulfill_database_order(od: Dict[str, Any]) -> Dict[str, Any]:
    database_id = str(od.get('database_id') or '')
    db = _database_by_id(database_id)
    if not db:
        raise ShopApiError(409, 'database_missing', 'Выбранная база аккаунтов не найдена')
    values = _reserve_database_items(database_id, str(od['order_id']), int(od.get('qty', 1) or 1))
    with _orders_lock:
        od['step'] = 'delivering'
        od['database_reserved'] = len(values)
        _save_orders_state()
    return {'status': 'ready', 'values': values, 'cost_kop': 0, 'source': 'database', 'database_id': database_id}
def process_order(oid: str) -> None:
    with _orders_lock:
        od = _pending.get(oid)
        if not od:
            return
        od['step'] = 'processing'
        _save_orders_state()
    delivery_mode = str(od.get('delivery_mode') or 'api')
    try:
        result = _fulfill_database_order(od) if delivery_mode == 'database' else _fulfill_api_order(od)
    except ShopNetworkError as e:
        _manual_check(oid, str(e))
        return
    except ShopApiError as e:
        _fail_order(oid, e)
        return
    except Exception as e:
        logger.exception(f'{LP} #{oid} неожиданная ошибка выдачи: {e}')
        _notify_admin(f'⚠️ <b>Ошибка плагина в заказе #{oid}</b>\n{str(e)[:300]}', etype='error')
        _manual_check(oid, str(e))
        return
    if result.get('status') == 'manual':
        _manual_check(oid, str(result.get('reason') or 'Требуется ручная проверка'))
        return
    values = list(result.get('values') or [])
    with _orders_lock:
        current = _pending.get(oid)
        if current:
            current['step'] = 'sending'
            current['sending_started_at'] = time.time()
            _save_orders_state()
    _log_event('order_sending', order_id=oid, mode=delivery_mode, qty=len(values))
    delivery = _send_goods(oid, od['chat_id'], od['buyer'], values, od['product_title'], od['qty'])
    cost_kop = int(result.get('cost_kop') or 0)
    if not delivery.get('goods_sent'):
        with _orders_lock:
            current = _pending.get(oid)
            if current:
                current['delivery_uncertain'] = True
                if delivery_mode == 'database':
                    current['database_uncertain'] = True
                current['error'] = 'FunPay не подтвердил полную отправку всех сообщений с товаром'
                _save_orders_state()
        _manual_check(oid, 'Результат отправки товара в FunPay неопределён. Автоматическая повторная выдача заблокирована, чтобы исключить двойную продажу. Проверьте чат покупателя вручную.')
        return
    if not delivery.get('footer_sent'):
        _notify_admin(f'⚠️ <b>Заказ #{oid}: товар выдан, но финальное сообщение не отправилось</b>\nПовторно товар не отправляется.', etype='error')
    if delivery_mode == 'database':
        try:
            _commit_database_reservation(str(od.get('database_id') or ''), oid)
        except Exception as e:
            with _orders_lock:
                current = _pending.get(oid)
                if current:
                    current['step'] = 'manual_check'
                    current['database_uncertain'] = True
                    current['error'] = f'Товар отправлен, но резерв базы не удалось подтвердить: {e}'
                    _save_orders_state()
            kb = _make_kb([[('✅ Повторить списание резерва', f'd4s_db_order_commit:{oid}')], [('♻️ Вернуть резерв', f'd4s_db_order_release:{oid}')]])
            _notify_admin(f'⚠️ <b>Заказ #{oid}: товар отправлен, но база не обновилась</b>\n{str(e)[:250]}\nРезерв оставлен для ручной проверки.', keyboard=kb, etype='failure')
            return
    _finish_order(oid, 'COMPLETED', cost_kop)
    _record_sale(int(od.get('product_id') or 0), od['product_title'], int(od['qty']), od['price_rub'] if od['currency'] in ('', 'rub', '₽') else 0.0, cost_kop / 100)
    lot_key = od.get('lot_key')
    with _bindings_lock:
        binding = _normalize_binding(_bindings.get(lot_key or '') or {}) if lot_key else None
    if binding and lot_key and _binding_stock_target(binding) > 0:
        threading.Thread(target=_sync_binding_stock, args=(str(lot_key), binding), daemon=True).start()
    bal_txt = ''
    if delivery_mode == 'api':
        try:
            bal = _refresh_balance()
            if bal is not None:
                bal_txt = f'\n💰 Баланс API: {_fmt_rub_kop(bal)}'
        except Exception:
            pass
    source_txt = '🗃 База аккаунтов' if delivery_mode == 'database' else '🌐 API dim4n4ik.shop'
    warn = ''
    if delivery_mode == 'api' and od['currency'] in ('', 'rub', '₽') and od['price_rub'] and cost_kop and od['price_rub'] < cost_kop / 100:
        warn = f"\n⚠️ <b>Продано дешевле закупки!</b> ({od['price_rub']:.2f} ₽ &lt; {cost_kop / 100:.2f} ₽) — проверьте цену лота"
    _notify_admin(f"✅ <b>Заказ #{oid} выдан</b>\n📦 {od['product_title']} ×{od['qty']}\n👤 {od['buyer']}\n🚚 {source_txt}\n💵 Продажа: {od['price_rub']:.2f} {od['currency'] or '₽'} | Закупка: {_fmt_rub_kop(cost_kop)}{bal_txt}{warn}", etype='success')
def _finish_order(oid: str, status: str, cost_kop: int=0) -> None:
    with _orders_lock:
        od = _pending.pop(oid, None)
        _processed[oid] = time.time()
        _save_orders_state()
    if od:
        _append_order_log({'order_id': oid, 'product_id': od['product_id'], 'product_title': od['product_title'], 'qty': od['qty'], 'price_rub': od['price_rub'], 'cost_kop': cost_kop or od.get('cost_kop'), 'shop_order_id': od.get('shop_order_id'), 'buyer': od['buyer'], 'status': status, 'error': od.get('error', ''), 'ts': time.time(), 'ts_str': _now_str()})
        if not str(status).startswith('COMPLETED'):
            _record_fail()
    _log_event('order_finished', order_id=oid, status=status, cost_kop=cost_kop)
    logger.info(f'{LP} #{oid} завершён: {status}')
ERROR_HUMAN = {'insufficient_balance': 'Недостаточно баланса API — пополните: https://t.me/dim4n4ikshop_bot?start=ref7202094913 → Профиль → Пополнить', 'out_of_stock': 'Товар закончился на складе магазина', 'invalid_key': 'API-ключ неверен или отозван — создайте новый: https://t.me/dim4n4ikshop_bot?start=ref7202094913', 'unauthorized': 'API-ключ не принят — проверьте ключ в настройках', 'forbidden': 'У ключа нет прав на покупки — создайте новый ключ', 'not_found': 'Товар не найден в магазине — проверьте привязку', 'quota_exceeded': 'Превышена часовая квота API (1000 шт/час) — попробуйте позже', 'no_api_key': 'API-ключ не задан в настройках плагина', 'qty_limit': 'Слишком большое количество для одного заказа', 'loss_block': 'Цена лота ниже закупки — продажа заблокирована (защита от убытка)', 'database_stock': 'В базе аккаунтов недостаточно товара', 'database_missing': 'База аккаунтов не найдена или удалена'}
BUSINESS_ERRORS = {'insufficient_balance', 'out_of_stock', 'not_found', 'invalid_request'}
REFUNDABLE = {'insufficient_balance', 'out_of_stock', 'not_found', 'qty_limit', 'loss_block', 'database_stock', 'database_missing'}
def _fail_order(oid: str, err: ShopApiError) -> None:
    human = ERROR_HUMAN.get(err.code, err.message or err.code)
    extra = ''
    if err.code == 'insufficient_balance':
        need = err.extra.get('need_kop')
        if need:
            extra = f' (не хватает {_fmt_rub_kop(int(need))})'
    elif err.code in ('out_of_stock', 'database_stock'):
        avail = err.extra.get('available')
        if avail is not None:
            extra = f' (доступно: {avail} шт.)'
    with _orders_lock:
        od = _pending.get(oid)
        if not od:
            return
        od['step'] = 'failed'
        od['error'] = f'{err.code}: {human}{extra}'
        od['attempt'] = int(od.get('attempt', 0)) + 1
        if err.code in BUSINESS_ERRORS:
            od['idem_key'] = f"fp-{oid}-r{od['attempt']}"
        _save_orders_state()
    _log_event('order_failed', level=logging.ERROR, order_id=oid, code=err.code, reason=human + extra, attempt=od['attempt'])
    logger.error(f"{LP} #{oid} закупка не удалась: {od['error']}")
    auto_refund = bool(cfg_get('auto_refund_enabled')) and err.code in REFUNDABLE
    refunded = False
    if auto_refund:
        refunded = _try_refund(oid)
        if refunded:
            _fp_send(od['chat_id'], _buyer_message('refund', order_id=oid, order_url=f'https://funpay.com/orders/{oid}/', product_title=od['product_title'], qty=od['qty'], reason=human + extra), od['buyer'])
            _finish_order(oid, 'FAILED_REFUNDED')
    if not refunded:
        _fp_send(od['chat_id'], _buyer_message('delay', order_id=oid, order_url=f'https://funpay.com/orders/{oid}/', product_title=od['product_title'], qty=od['qty'], reason=human + extra), od['buyer'])
    kb = None
    if not refunded:
        kb = _make_kb([[('🔁 Повторить закупку', f'd4s_retry:{oid}'), ('↩️ Вернуть деньги', f'd4s_refund:{oid}')]])
    _notify_admin(f"❌ <b>Заказ #{oid}: закупка не удалась</b>\n📦 {od['product_title']} ×{od['qty']} | 👤 {od['buyer']}\n💵 Продажа: {od['price_rub']:.2f} {od['currency'] or '₽'}\n🧾 Причина: {human}{extra}" + ('\n↩️ Авто-возврат выполнен.' if refunded else '\n\nПосле устранения причины нажмите «Повторить закупку».'), keyboard=kb, etype='failure')
def _database_manual_resolution_kb(oid: str):
    return _make_kb([[('✅ Считать выданным', f'd4s_db_order_commit:{oid}')], [('♻️ Вернуть резерв в базу', f'd4s_db_order_release:{oid}')]])
def _manual_check(oid: str, reason: str) -> None:
    with _orders_lock:
        od = _pending.get(oid)
        if not od:
            return
        od['step'] = 'manual_check'
        od['error'] = reason
        _save_orders_state()
    logger.error(f'{LP} #{oid} требует проверки: {reason}')
    _fp_send(od['chat_id'], _buyer_message('delay', order_id=oid, order_url=f'https://funpay.com/orders/{oid}/', product_title=od['product_title'], qty=od['qty'], reason=reason), od['buyer'])
    if str(od.get('delivery_mode') or 'api') == 'database' and od.get('database_reserved'):
        kb = _database_manual_resolution_kb(oid)
        help_text = '\n\nРезерв базы сохранён. Выберите действие только после ручной проверки чата покупателя.'
    else:
        kb = _make_kb([[('🔁 Повторить (безопасно)', f'd4s_retry:{oid}'), ('↩️ Вернуть деньги', f'd4s_refund:{oid}')]])
        help_text = '\n\n«Повторить» использует тот же Idempotency-Key.'
    _notify_admin(f"⚠️ <b>Заказ #{oid}: требуется проверка</b>\n📦 {od['product_title']} ×{od['qty']} | 👤 {od['buyer']}\n🧾 {reason}{help_text}", keyboard=kb, etype='failure')
def _funpay_order_paid_state(order_id: str) -> Tuple[Optional[bool], str]:
    if cardinal is None or getattr(cardinal, 'account', None) is None:
        return (None, 'Cardinal недоступен')
    try:
        order = cardinal.account.get_order(str(order_id))
    except Exception as e:
        _log_event('restart_funpay_check_error', level=logging.WARNING, order_id=order_id, error=str(e)[:180])
        return (None, str(e)[:180])
    raw = getattr(order, 'status', None)
    status = str(getattr(raw, 'name', None) or getattr(raw, 'value', None) or raw or '')
    if not status:
        return (None, 'пустой статус')
    return ('PAID' in status.upper(), status)
def _restart_order_action(order_id: str, od: Dict[str, Any]) -> str:
    oid = str(order_id)
    if oid in _processed or str(od.get('step') or '') == 'delivered':
        if str(od.get('delivery_mode') or 'api') == 'database' and od.get('database_reserved'):
            return 'manual'
        return 'processed'
    mode = str(od.get('delivery_mode') or 'api')
    if mode == 'database' and od.get('database_reserved'):
        return 'manual'
    step = str(od.get('step') or 'processing')
    if step in ('sending', 'delivering', 'manual_check', 'failed'):
        return 'manual'
    if step in ('processing', 'new', 'purchased'):
        return 'resume'
    return 'manual'
def _restart_manual_notice(order_id: str, od: Dict[str, Any], reason: str) -> None:
    oid = str(order_id)
    uncertain = bool(od.get('delivery_uncertain')) or str(od.get('step') or '') in ('sending', 'delivering', 'delivered')
    with _orders_lock:
        current = _pending.get(oid)
        if current:
            current['step'] = 'manual_check'
            current['error'] = reason
            if uncertain:
                current['delivery_uncertain'] = True
            _save_orders_state()
    if str(od.get('delivery_mode') or 'api') == 'database' and od.get('database_reserved'):
        kb = _database_manual_resolution_kb(oid)
    else:
        kb = _make_kb([[('🔁 Повторить (после проверки)', f'd4s_retry:{oid}'), ('↩️ Вернуть деньги', f'd4s_refund:{oid}')]])
    _notify_admin(f"⚠️ <b>Заказ #{oid}: не возобновлён автоматически</b>\n📦 {od.get('product_title') or 'товар'} ×{od.get('qty', 1)}\n🧾 {reason}\n\nПроверьте заказ и чат покупателя перед любым действием.", keyboard=kb, etype=None)
def _recover_pending_orders_after_restart() -> None:
    with _orders_lock:
        snapshot = [(str(oid), dict(od)) for oid, od in _pending.items()]
    resumed = 0
    for oid, od in snapshot:
        try:
            age = time.time() - float(od.get('created_at', 0) or 0)
        except Exception:
            age = 0
        if age > 172800:
            _restart_manual_notice(oid, od, 'Незавершённый заказ старше 48 часов.')
            continue
        action = _restart_order_action(oid, od)
        if action == 'processed':
            with _orders_lock:
                _pending.pop(oid, None)
                _save_orders_state()
            _log_event('restart_processed_cleanup', order_id=oid)
            continue
        paid, status = _funpay_order_paid_state(oid)
        _log_event('restart_funpay_check', order_id=oid, paid=paid, status=status, step=od.get('step'))
        if action == 'manual':
            status_note = f' Статус FunPay после рестарта: {status}.' if status else ''
            _restart_manual_notice(oid, od, 'До рестарта выдача могла уже начаться. Повторная автоматическая отправка заблокирована.' + status_note)
            continue
        if paid is not True:
            if paid is False:
                with _orders_lock:
                    current = _pending.get(oid)
                    if current:
                        current['error'] = f'После рестарта заказ FunPay уже не PAID: {status}'
                _finish_order(oid, 'NOT_PAID_AFTER_RESTART', int(od.get('cost_kop') or 0))
            else:
                _restart_manual_notice(oid, od, f'Не удалось перепроверить статус FunPay: {status}')
            continue
        resumed += 1
        threading.Thread(target=process_order, args=(oid,), daemon=True).start()
    if resumed:
        _notify_admin(f'🔄 После рестарта безопасно возобновлено заказов: {resumed}', etype=None)
def handle_new_message(cardinal_obj, event, *args) -> None:
    global cardinal
    if cardinal is None:
        cardinal = cardinal_obj
    if not cfg_get('plugin_enabled'):
        return
    msg = getattr(event, 'message', None) or event
    text = _clean_text(str(getattr(msg, 'content', None) or getattr(msg, 'text', None) or ''))
    m = ORDER_PAID_RE.search(text)
    if not m:
        return
    oid = m.group(1)
    with _orders_lock:
        if oid in _processed or oid in _pending or oid in _seen or (oid in _rejected):
            return
    if not _configured_bindings():
        return
    try:
        full = cardinal.account.get_order(oid)
    except Exception as e:
        logger.warning(f'{LP} fallback get_order({oid}): {e}')
        return
    status = str(getattr(full, 'status', '') or '')
    if status and 'PAID' not in status.upper():
        return
    logger.info(f'{LP} #{oid} перехвачен из сообщения (fallback)')
    handle_new_order(cardinal, SimpleNamespace(order=full, lot_id=_object_value(full, 'lot_id'), offer_id=_object_value(full, 'offer_id')))
def _balance_loop() -> None:
    global _low_balance_alerted
    while not _stop_event.is_set():
        try:
            interval = max(float(cfg_get('balance_check_interval_min') or 10), 1) * 60
        except Exception:
            interval = 600
        if _stop_event.wait(interval):
            break
        try:
            if not cfg_get('plugin_enabled'):
                continue
            bal = _refresh_balance()
            if bal is None:
                continue
            threshold = float(cfg_get('low_balance_threshold_rub') or 0) * 100
            if threshold and bal < threshold and (not _low_balance_alerted):
                _low_balance_alerted = True
                _notify_admin(f'⚠️ <b>Низкий баланс API: {_fmt_rub_kop(bal)}</b> (порог {_fmt_rub_kop(int(threshold))})\nПополните: https://t.me/dim4n4ikshop_bot?start=ref7202094913 → Профиль → Пополнить, иначе заказы перестанут выдаваться.', etype='low_balance')
            elif threshold and bal >= threshold and _low_balance_alerted:
                _low_balance_alerted = False
                _notify_admin(f'✅ Баланс API восстановлен: {_fmt_rub_kop(bal)}', etype='low_balance')
        except Exception as e:
            logger.warning(f'{LP} balance loop: {e}')
            _notify_admin(f'⚠️ <b>Ошибка проверки баланса</b>\n{str(e)[:300]}', etype='error')
def _stock_check_once() -> None:
    if not cfg_get('plugin_enabled'):
        return
    bindings = _enabled_bindings()
    if not bindings:
        return
    auto = bool(cfg_get('auto_lots_by_stock'))
    disabled_now = []
    enabled_now = []
    changed = False
    for lot_id, binding in bindings.items():
        mode = str(binding.get('delivery_mode') or 'api')
        source_id = str(binding.get('database_id') or '') if mode == 'database' else str(binding.get('product_id') or '')
        source_key = f'{mode}:{source_id}'
        stock = _binding_source_stock(binding, max_age=30)
        effective = stock // _binding_qty_per_unit(binding)
        source_title = str(binding.get('product_title') or source_id or 'источник')
        if mode == 'database':
            db = _database_by_id(str(binding.get('database_id') or ''))
            if db:
                source_title = f"база «{db.get('name')}»"
        if effective <= 0:
            _ok_strikes[source_key] = 0
            alert_key = f'{source_key}:{lot_id}'
            if alert_key not in _oos_alerted:
                _oos_alerted.add(alert_key)
                suffix = ' Лот выключаю автоматически.' if auto else ''
                _notify_admin(f'📦 <b>Источник для лота {lot_id} пуст</b>\n{source_title}: доступно {stock} шт.{suffix}', etype='out_of_stock')
            if auto and lot_id not in _auto_disabled:
                if _set_lot_active(lot_id, False):
                    _auto_disabled[lot_id] = source_key
                    disabled_now.append(lot_id)
                    changed = True
            if _binding_stock_target(binding) > 0:
                _sync_binding_stock(lot_id, binding)
        else:
            alert_key = f'{source_key}:{lot_id}'
            if alert_key in _oos_alerted:
                _oos_alerted.discard(alert_key)
                _notify_admin(f'✅ Источник для лота {lot_id} снова доступен: {source_title}, {stock} шт.', etype='out_of_stock')
            _ok_strikes[source_key] = _ok_strikes.get(source_key, 0) + 1
            if _binding_stock_target(binding) > 0:
                ok, _ = _sync_binding_stock(lot_id, binding)
                if ok and lot_id in _auto_disabled:
                    _auto_disabled.pop(lot_id, None)
                    enabled_now.append(lot_id)
                    changed = True
            elif auto and lot_id in _auto_disabled and _ok_strikes[source_key] >= 2:
                if _set_lot_active(lot_id, True):
                    _auto_disabled.pop(lot_id, None)
                    enabled_now.append(lot_id)
                    changed = True
        time.sleep(0.15)
    if changed:
        _save_auto_disabled()
    if disabled_now:
        _notify_admin('🔴 Автовыключены лоты: ' + ', '.join(disabled_now), etype='out_of_stock')
    if enabled_now:
        _notify_admin('🟢 Автовключены лоты: ' + ', '.join(enabled_now), etype='out_of_stock')
def _stock_loop() -> None:
    while not _stop_event.is_set():
        try:
            interval = max(float(cfg_get('fp_auto_sync_sec') or 60), 30)
        except Exception:
            interval = 60
        if _stop_event.wait(interval):
            break
        try:
            _stock_check_once()
        except Exception as e:
            logger.warning(f'{LP} stock loop: {e}')
def start_background_loops() -> None:
    threading.Thread(target=_balance_loop, daemon=True).start()
    threading.Thread(target=_stock_loop, daemon=True).start()
def _plugin_home(chat_id, message_id=None) -> None:
    text = f'🧩 <b>Плагин:</b> {NAME}\n📦 <b>Версия:</b> <code>{VERSION}</code>\n👥 <b>Авторы:</b> <a href="{ORIGINAL_AUTHOR_URL}">@dmitry_mak09</a>, <a href="{CREATOR_URL}">@tinechelovec</a>\n\nВыберите раздел ниже.'
    kb = _make_kb([[('⚙️ Настройки', 'd4s_main'), ('ℹ️ Информация', 'd4s_info')], [('⬆️ Обновить плагин', 'd4s_update'), ('🗑 Удалить', 'd4s_delete_ask')], [('🔙 К списку плагинов', CB_PLUGINS_LIST_OPEN)]])
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _plugin_info(chat_id, message_id=None) -> None:
    text = 'ℹ️ <b>Информация</b>\n\nСлева — официальный сервис dim4n4ik.shop и его магазины. Справа — чат, канал и GitHub плагина.\n\n🎮 Steam-аккаунты — через Steam-магазин.\n📧 Почты — через отдельный магазин почт.\n\n👤 Создатель сервиса: @dmitry_mak09\n👨‍💻 Разработчик плагина: @tinechelovec'
    if tg_types:
        kb = tg_types.InlineKeyboardMarkup()
        kb.row(tg_types.InlineKeyboardButton('📖 Инструкция', url=INSTRUCTION_URL), tg_types.InlineKeyboardButton('📚 GitHub-инструкция', url=ALT_INSTRUCTION_URL))
        kb.row(tg_types.InlineKeyboardButton('🎮 Steam-магазин', url=SHOP_BOT_URL), tg_types.InlineKeyboardButton('💬 Чат плагина', url=GROUP_URL))
        kb.row(tg_types.InlineKeyboardButton('📧 Почты', url=MAIL_BOT_URL), tg_types.InlineKeyboardButton('📢 Канал', url=CHANNEL_URL))
        kb.row(tg_types.InlineKeyboardButton('💬 Чат магазина', url=SHOP_CHAT_URL), tg_types.InlineKeyboardButton('💻 GitHub', url=GITHUB_URL))
        kb.row(tg_types.InlineKeyboardButton('🌐 Сайт', url=SHOP_SITE_URL))
        kb.row(tg_types.InlineKeyboardButton('👤 Создатель сервиса', url=ORIGINAL_AUTHOR_URL), tg_types.InlineKeyboardButton('👨‍💻 Разработчик', url=CREATOR_URL))
        kb.row(tg_types.InlineKeyboardButton('◀️ Назад', callback_data='d4s_home'))
    else:
        kb = None
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _plugin_update_menu(chat_id, message_id=None) -> None:
    text = f'⬆️ <b>Обновление {NAME}</b>\n\nТекущая версия: <code>{VERSION}</code>\n\nВыберите способ обновления.'
    kb = _make_kb([[('🌐 Онлайн', 'd4s_update_online'), ('📥 Локально', 'd4s_update_local')], [('◀️ Назад', 'd4s_home')]])
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _plugin_version_key(value: Any) -> Tuple[int, int, int, int]:
    nums = [int(x) for x in re.findall(r'\d+', str(value or ''))[:4]]
    nums.extend([0] * (4 - len(nums)))
    return tuple(nums[:4])
def _plugin_version_from_source(source: str) -> Optional[str]:
    m = re.search(r'(?m)^\s*VERSION\s*=\s*[\"\']([^\"\']+)[\"\']', source or '')
    return m.group(1).strip() if m else None
def _download_online_update() -> Tuple[bytes, str]:
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': f'dim4n4ik-shop-cardinal/{VERSION}'}
    errors = []
    try:
        meta = requests.get(f'https://api.github.com/repos/{GITHUB_REPO}', headers=headers, timeout=20)
        meta.raise_for_status()
        branch = str((meta.json() or {}).get('default_branch') or 'main')
        tree = requests.get(f'https://api.github.com/repos/{GITHUB_REPO}/git/trees/{branch}?recursive=1', headers=headers, timeout=25)
        tree.raise_for_status()
        paths = [str(x.get('path')) for x in (tree.json() or {}).get('tree', []) if x.get('type') == 'blob' and str(x.get('path', '')).lower().endswith('.py')]
        paths.sort(key=lambda x: (0 if 'dim4' in x.lower() else 1 if 'steam' in x.lower() else 2, len(x)))
        for path in paths[:30]:
            url = f'https://raw.githubusercontent.com/{GITHUB_REPO}/{branch}/{path}'
            r = requests.get(url, headers={'User-Agent': headers['User-Agent']}, timeout=25)
            if r.status_code != 200 or len(r.content) > 5 * 1024 * 1024:
                continue
            source = r.content.decode('utf-8-sig', errors='replace')
            if UUID in source and 'BIND_TO_PRE_INIT' in source and 'BIND_TO_NEW_ORDER' in source:
                return r.content, url
    except Exception as e:
        errors.append(str(e)[:120])
    names = ('dim4n4ik_shop.py', 'Dim4n4ik-Shop.py', 'Auto-Steam-Account.py', 'FPC-Auto-Steam-Account.py', 'plugin.py')
    for branch in ('main', 'master'):
        for name in names:
            url = f'https://raw.githubusercontent.com/{GITHUB_REPO}/{branch}/{name}'
            try:
                r = requests.get(url, headers={'User-Agent': headers['User-Agent']}, timeout=20)
                if r.status_code != 200 or len(r.content) > 5 * 1024 * 1024:
                    continue
                source = r.content.decode('utf-8-sig', errors='replace')
                if UUID in source and 'BIND_TO_PRE_INIT' in source and 'BIND_TO_NEW_ORDER' in source:
                    return r.content, url
            except Exception as e:
                errors.append(str(e)[:80])
    raise RuntimeError('не удалось найти файл плагина в репозитории' + (': ' + ' | '.join(errors[-3:]) if errors else ''))
def _validate_online_update(payload: bytes) -> Tuple[str, str]:
    if not payload or len(payload) < 1000:
        raise RuntimeError('файл обновления слишком маленький')
    if len(payload) > 5 * 1024 * 1024:
        raise RuntimeError('файл обновления слишком большой')
    try:
        source = payload.decode('utf-8-sig')
    except UnicodeDecodeError as e:
        raise RuntimeError('файл обновления должен быть в UTF-8') from e
    required = (UUID, 'BIND_TO_PRE_INIT', 'BIND_TO_NEW_ORDER', 'BIND_TO_NEW_MESSAGE')
    missing = [x for x in required if x not in source]
    if missing:
        raise RuntimeError('файл не похож на этот плагин или UUID не совпадает')
    new_version = _plugin_version_from_source(source)
    if not new_version:
        raise RuntimeError('в обновлении не найдена VERSION')
    if _plugin_version_key(new_version) <= _plugin_version_key(VERSION):
        raise RuntimeError(f'версия {new_version} не новее установленной {VERSION}')
    compile(source, str(Path(__file__).resolve()), 'exec')
    return source, new_version
def _install_online_update(payload: bytes) -> Dict[str, Any]:
    plugin_file = Path(__file__).resolve()
    temporary = plugin_file.with_name(plugin_file.name + '.update.tmp')
    backup = plugin_file.with_name(plugin_file.name + '.pre-update.bak')
    try:
        _, new_version = _validate_online_update(payload)
        with temporary.open('wb') as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        try:
            os.chmod(temporary, plugin_file.stat().st_mode)
        except Exception:
            pass
        shutil.copy2(plugin_file, backup)
        os.replace(temporary, plugin_file)
        return {'ok': True, 'version': new_version, 'backup': backup.name}
    except Exception as e:
        try:
            if temporary.exists():
                temporary.unlink()
        except Exception:
            pass
        return {'ok': False, 'error': str(e)[:300]}
def _online_update_worker(chat_id, message_id=None) -> None:
    try:
        payload, url = _download_online_update()
        result = _install_online_update(payload)
        if result.get('ok'):
            text = f"✅ <b>Плагин обновлён до версии {result['version']}.</b>\n\nИсточник: <code>{url}</code>\nРезервная копия: <code>{result['backup']}</code>.\nВыполните <code>/restart</code>, чтобы запустить новую версию."
        elif 'не новее установленной' in str(result.get('error')):
            text = f'✅ Установлена актуальная версия <code>{VERSION}</code>.'
        else:
            text = f"❌ <b>Обновление не установлено.</b>\n\n{result.get('error')}\nТекущий файл не изменён."
    except Exception as e:
        text = f'❌ <b>Не удалось проверить обновление.</b>\n\n{str(e)[:300]}'
    finally:
        if _update_lock.locked():
            _update_lock.release()
    kb = _make_kb([[('◀️ В меню', 'd4s_home')]])
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _start_online_update(chat_id, message_id=None) -> None:
    if not _update_lock.acquire(blocking=False):
        text = '⏳ Проверка обновления уже выполняется.'
        kb = _make_kb([[('◀️ Назад', 'd4s_update')]])
        _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
        return
    text = '⏳ Проверяю GitHub и новую версию…'
    kb = _make_kb([[('◀️ Назад', 'd4s_home')]])
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
    threading.Thread(target=_online_update_worker, args=(chat_id, message_id), daemon=True).start()
def _start_local_update(chat_id, message_id=None) -> None:
    _waiting[chat_id] = {'action': 'plugin_local_update', 'prompt_id': message_id}
    text = f'📥 <b>Локальное обновление {NAME}</b>\n\nПришлите новый файл плагина с расширением <code>.py</code>.\n\nБудут проверены UUID, версия и синтаксис. Перед заменой текущего файла будет создана резервная копия.'
    kb = _make_kb([[('❌ Отмена', 'd4s_wait_cancel:d4s_update')]])
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _local_update_document_handler(message) -> None:
    chat_id = getattr(getattr(message, 'chat', None), 'id', None)
    if not chat_id or not _is_authorized(getattr(getattr(message, 'from_user', None), 'id', None)):
        return
    st = _waiting.get(chat_id) or {}
    if st.get('action') != 'plugin_local_update':
        return
    document = getattr(message, 'document', None)
    filename = str(getattr(document, 'file_name', '') or '')
    prompt_id = st.get('prompt_id')
    kb = _make_kb([[('❌ Отмена', 'd4s_wait_cancel:d4s_update')]])
    if not filename.lower().endswith('.py'):
        text = '❌ Нужен файл с расширением <code>.py</code>. Пришлите другой файл.'
        _tg_edit(chat_id, prompt_id, text, kb) if prompt_id else _tg_send(chat_id, text, kb)
        return
    try:
        file_info = bot.get_file(document.file_id)
        payload = bytes(bot.download_file(file_info.file_path))
    except Exception as e:
        text = f'❌ Не удалось скачать файл: {str(e)[:250]}'
        _tg_edit(chat_id, prompt_id, text, kb) if prompt_id else _tg_send(chat_id, text, kb)
        return
    result = _install_online_update(payload)
    _waiting.pop(chat_id, None)
    if result.get('ok'):
        text = f"✅ <b>Локальное обновление установлено: {result['version']}.</b>\n\nРезервная копия: <code>{result['backup']}</code>.\nВыполните <code>/restart</code>, чтобы запустить новую версию."
    elif 'не новее установленной' in str(result.get('error')):
        text = f'✅ Установлена версия <code>{VERSION}</code>; присланный файл не новее.'
    else:
        text = f"❌ <b>Локальное обновление не установлено.</b>\n\n{result.get('error')}\nТекущий файл не изменён."
    result_kb = _make_kb([[('◀️ В меню обновления', 'd4s_update')]])
    _tg_edit(chat_id, prompt_id, text, result_kb) if prompt_id else _tg_send(chat_id, text, result_kb)
def _plugin_delete_confirm(chat_id, message_id=None) -> None:
    text = f'⚠️ <b>Удаление {NAME}</b>\n\nБудут удалены файл плагина и его данные из <code>{STORAGE_DIR}</code>.\n\nЭто действие необратимо. Продолжить?'
    kb = _make_kb([[('✅ Да, удалить', 'd4s_delete_yes'), ('❌ Нет', 'd4s_delete_no')]])
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _delete_plugin_from_disk(chat_id, message_id=None) -> None:
    errors = []
    on_delete()
    plugin_file = Path(__file__).resolve()
    data_dir = Path(STORAGE_DIR).resolve()
    expected_dir = (Path(BASE_DIR) / 'storage' / 'plugins' / 'dim4n4ik_shop').resolve()
    try:
        if data_dir != expected_dir:
            raise RuntimeError('небезопасный путь данных')
        if data_dir.exists():
            shutil.rmtree(data_dir)
    except Exception as e:
        errors.append(f'данные: {e}')
    try:
        for path in (plugin_file.with_name(plugin_file.name + '.pre-update.bak'), plugin_file.with_name(plugin_file.name + '.update.tmp'), plugin_file):
            if path.exists() and path.parent == plugin_file.parent:
                path.unlink()
    except Exception as e:
        errors.append(f'файл: {e}')
    kb = _make_kb([[('🔙 К списку плагинов', CB_PLUGINS_LIST_OPEN)]])
    text = '✅ <b>Плагин удалён.</b>\n\nВыполните <code>/restart</code>.' if not errors else '⚠️ <b>Удаление выполнено частично.</b>\n\n' + '\n'.join(errors)
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _wait_target(st: Dict[str, Any]) -> Tuple[str, str]:
    action = st.get('action')
    if action == 'set_key':
        return '🔙 Назад', 'd4s_account'
    if action in ('set_lowbal', 'set_balance_interval'):
        return '🔙 Назад', 'd4s_notifications'
    if action == 'set_margin':
        return '🔙 Назад', 'd4s_safety'
    if action == 'edit_buyer_message':
        return '🔙 Назад', 'd4s_messages'
    if action in ('set_fpbuf', 'set_fpsync', 'lot_manual_id', 'lot_manual_type'):
        return '🔙 Назад', 'd4s_lot_set'
    if action in ('lot_set_qty', 'lot_set_stock') and st.get('lot_id'):
        return '🔙 Назад', f"d4s_lot_pick:{st['lot_id']}"
    if action in ('db_create_name', 'db_create_product'):
        return '❌ Отмена', 'd4s_databases'
    if action in ('db_rename', 'db_replenish_qty', 'db_import_text', 'db_import_file') and st.get('database_id'):
        return '🔙 Назад', f"d4s_db:{st['database_id']}"
    if action == 'config_import':
        return '❌ Отмена', 'd4s_config'
    if action == 'plugin_local_update':
        return '❌ Отмена', 'd4s_update'
    if action in ('bind_setqty', 'bind_setname') and st.get('lot_id'):
        return '🔙 Назад', f"d4s_bind:{st['lot_id']}"
    if action == 'grp_rename':
        return '❌ Отмена', 'd4s_bind_list'
    if action in ('bind_lot', 'bind_qty', 'bind_group_new', 'bind_group_wait'):
        return '❌ Отмена', 'd4s_bind_list'
    return '❌ Отмена', 'd4s_main'
def _wait_kb(st: Dict[str, Any]):
    label, target = _wait_target(st)
    return _make_kb([[(label, f'd4s_wait_cancel:{target}')]])
def _show_wait_target(chat_id, message_id, target: str) -> None:
    if target == 'd4s_account':
        _menu_account(chat_id, message_id)
    elif target in ('d4s_plugin_set', 'd4s_set'):
        _menu_plugin_settings(chat_id, message_id)
    elif target == 'd4s_notifications':
        _menu_notifications(chat_id, message_id)
    elif target == 'd4s_safety':
        _menu_safety(chat_id, message_id)
    elif target == 'd4s_messages':
        _menu_buyer_messages(chat_id, message_id)
    elif target == 'd4s_order_set':
        _menu_order_settings(chat_id, message_id)
    elif target == 'd4s_lot_set':
        _menu_lot_settings(chat_id, message_id)
    elif target.startswith('d4s_lot_pick:'):
        _menu_lot_detail(chat_id, message_id, target.split(':', 1)[1])
    elif target == 'd4s_databases':
        _menu_databases(chat_id, message_id)
    elif target.startswith('d4s_db:'):
        _menu_database_detail(chat_id, message_id, target.split(':', 1)[1])
    elif target == 'd4s_maintenance':
        _menu_maintenance(chat_id, message_id)
    elif target == 'd4s_config':
        _menu_config(chat_id, message_id)
    elif target == 'd4s_logs':
        _menu_logs(chat_id, message_id)
    elif target == 'd4s_bind_list':
        _menu_bindings(chat_id, message_id)
    elif target.startswith('d4s_bind:'):
        _menu_binding_detail(chat_id, message_id, target.split(':', 1)[1])
    elif target == 'd4s_home':
        _plugin_home(chat_id, message_id)
    elif target == 'd4s_update':
        _plugin_update_menu(chat_id, message_id)
    else:
        _menu_main(chat_id, message_id, live_balance=False)
def _cancel_wait(chat_id, st: Dict[str, Any], message_id=None) -> None:
    _, target = _wait_target(st)
    _waiting.pop(chat_id, None)
    _show_wait_target(chat_id, message_id or st.get('prompt_id'), target)
def _menu_main(chat_id, message_id=None, live_balance: bool=False) -> None:
    key = cfg_get('api_key')
    status = '🟢 работает'
    bal_txt = '—'
    if not key:
        status = '⚪️ ключ не задан'
    elif live_balance:
        try:
            _refresh_balance()
        except Exception as e:
            status = f'🔴 недоступен ({str(e)[:40]})'
    if _last_balance_kop is not None:
        age_min = int((time.time() - _last_balance_ts) / 60)
        bal_txt = _fmt_rub_kop(_last_balance_kop) + (f' ({age_min} мин назад)' if age_min > 1 else '')
    with _bindings_lock:
        total = len(_bindings)
        active = sum((1 for b in _bindings.values() if b.get('enabled', True)))
    stats = _load_stats()
    text = f'⚙️ <b>Панель настроек</b>\n\n• Аккаунт/API: <b>{status}</b>\n• Баланс API: <code>{bal_txt}</code>\n• Лоты: <code>{active}/{total}</code> активных привязок\n• Заказов выдано: <code>{stats["total_orders"]}</code>\n\nВыберите раздел:'
    kb = _make_kb([[('🏪 Аккаунт dim4n4ik.shop', 'd4s_account')], [('⚙️ Настройки плагина', 'd4s_plugin_set')], [('🔗 Настройки лотов', 'd4s_lot_set')], [('📊 Статистика', 'd4s_stats')], [('🔙 Меню плагина', 'd4s_home')]])
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _onoff(key: str) -> str:
    return 'ВКЛ' if cfg_get(key) else 'ВЫКЛ'
def _menu_account(chat_id, message_id=None) -> None:
    key = cfg_get('api_key')
    bal_txt = _fmt_rub_kop(_last_balance_kop) if _last_balance_kop is not None else '—'
    text = f'🏪 <b>Аккаунт dim4n4ik.shop</b>\n\n🔑 API-ключ: {_mask_key(key)}\n🌐 API: <code>{cfg_get("base_url")}</code>\n💰 Баланс API: <b>{bal_txt}</b>\n\n🎮 Steam-магазин: <a href="{SHOP_BOT_URL}">открыть бота</a>\n📧 Магазин почт: <a href="{MAIL_BOT_URL}">открыть бота</a>\n\nЗдесь можно подключить, заменить или удалить API-ключ магазина.'
    rows = []
    if key:
        rows.append([('🔄 Изменить API-ключ', 'd4s_set_key'), ('🗑 Удалить API-ключ', 'd4s_key_delete_ask')])
    else:
        rows.append([('🔑 Добавить API-ключ', 'd4s_set_key')])
    rows.extend([[('🩺 Проверка API', 'd4s_health')], [('🔙 Назад', 'd4s_main')]])
    kb = _make_kb(rows)
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _menu_api_delete_confirm(chat_id, message_id=None) -> None:
    text = '⚠️ <b>Удалить API-ключ?</b>\n\nПлагин перестанет закупать товары до добавления нового ключа. Привязки, статистика и остальные настройки сохранятся.'
    kb = _make_kb([[('✅ Удалить', 'd4s_key_delete_yes'), ('❌ Отмена', 'd4s_key_delete_no')]])
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _menu_plugin_settings(chat_id, message_id=None) -> None:
    notifications = 'ВКЛ' if cfg_get('notifications_enabled') else 'ВЫКЛ'
    try:
        meta = _load_databases_meta()
        database_count = len(meta['databases'])
    except Exception:
        database_count = 0
    text = f'⚙️ <b>Настройки плагина</b>\n\n• Состояние: <b>{"🟢 включён" if cfg_get("plugin_enabled") else "🔴 выключен"}</b>\n• Автовозврат: <b>{_onoff("auto_refund_enabled")}</b>\n• Автодеактивация: <b>{_onoff("auto_lots_by_stock")}</b>\n• Уведомления: <b>{notifications}</b>\n• Баз аккаунтов: <b>{database_count}</b>\n\nВыберите категорию:'
    kb = _make_kb([[('🧩 Состояние плагина', 'd4s_plugin_state')], [('📦 Заказы', 'd4s_order_set')], [('🔔 Уведомления', 'd4s_notifications')], [('🛡 Безопасность', 'd4s_safety')], [('🗃 Базы аккаунтов', 'd4s_databases')], [('🧰 Обслуживание', 'd4s_maintenance')], [('🔙 Назад', 'd4s_main')]])
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _menu_plugin_state(chat_id, message_id=None) -> None:
    enabled = bool(cfg_get('plugin_enabled'))
    text = f'🧩 <b>Состояние плагина</b>\n\nСейчас: <b>{"🟢 Включён" if enabled else "🔴 Выключен"}</b>\n\nПри выключении новые заказы не обрабатываются и автоматическое управление остатками останавливается. Уже запущенная выдача не прерывается.'
    kb = _make_kb([[(f'🧩 Плагин: {"ВКЛ" if enabled else "ВЫКЛ"}', 'd4s_ptgl:plugin_enabled')], [('🔙 Назад', 'd4s_plugin_set')]])
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _menu_order_settings(chat_id, message_id=None) -> None:
    text = f'📦 <b>Настройки заказов</b>\n\n↩️ Автовозврат: <b>{_onoff("auto_refund_enabled")}</b>\n🔌 Автодеактивация лотов при отсутствии товара: <b>{_onoff("auto_lots_by_stock")}</b>\n\nСообщения покупателю можно менять отдельно, не редактируя код.'
    kb = _make_kb([[(f'↩️ Авто-возврат: {_onoff("auto_refund_enabled")}', 'd4s_otgl:auto_refund_enabled')], [(f'🔌 Автодеактивация: {_onoff("auto_lots_by_stock")}', 'd4s_otgl:auto_lots_by_stock')], [('💬 Сообщения покупателю', 'd4s_messages')], [('🔙 Назад', 'd4s_plugin_set')]])
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _menu_notifications(chat_id, message_id=None) -> None:
    text = f'🔔 <b>Уведомления</b>\n\nВсе уведомления: <b>{_onoff("notifications_enabled")}</b>\nПорог низкого баланса: <b>{float(cfg_get("low_balance_threshold_rub") or 0):.0f} ₽</b>\nПроверка баланса: <b>раз в {int(cfg_get("balance_check_interval_min") or 10)} мин.</b>\n\nКаждый тип можно включить или выключить отдельно.'
    rows = [[(f'🔔 Все уведомления: {_onoff("notifications_enabled")}', 'd4s_ntgl:notifications_enabled')], [(f'🛒 Пришёл заказ: {_onoff("notify_new_order")}', 'd4s_ntgl:notify_new_order')], [(f'✅ Заказ выдан: {_onoff("notify_success")}', 'd4s_ntgl:notify_success')], [(f'❌ Заказ не выдан: {_onoff("notify_failure")}', 'd4s_ntgl:notify_failure')], [(f'⚠️ Ошибки: {_onoff("notify_errors")}', 'd4s_ntgl:notify_errors')], [(f'💰 Низкий баланс: {_onoff("notify_low_balance")}', 'd4s_ntgl:notify_low_balance')], [(f'📦 Нет товара / сток: {_onoff("notify_out_of_stock")}', 'd4s_ntgl:notify_out_of_stock')], [('💰 Порог низкого баланса', 'd4s_set_lowbal')], [('⏱ Интервал проверки баланса', 'd4s_set_balint')], [('🔙 Назад', 'd4s_plugin_set')]]
    kb = _make_kb(rows)
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _menu_safety(chat_id, message_id=None) -> None:
    text = f'🛡 <b>Безопасность</b>\n\nЗащита от убытка: <b>{_onoff("loss_protection")}</b>\nМинимальная маржа: <b>{float(cfg_get("loss_min_margin_percent") or 0):.0f}%</b>\n\nЕсли защита включена, плагин не закупит товар, когда цена продажи ниже допустимого уровня.'
    kb = _make_kb([[(f'🛡 Защита от убытка: {_onoff("loss_protection")}', 'd4s_stgl:loss_protection')], [('📉 Минимальная маржа', 'd4s_set_margin')], [('🔙 Назад', 'd4s_plugin_set')]])
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _menu_buyer_messages(chat_id, message_id=None) -> None:
    text = '💬 <b>Сообщения покупателю</b>\n\nВыберите сообщение для редактирования. Доступные переменные: <code>{order_id}</code>, <code>{order_url}</code>, <code>{product_title}</code>, <code>{qty}</code>, <code>{reason}</code>.'
    rows = [[(f'✏️ {label}', f'd4s_msg_edit:{key}')] for key, label in BUYER_MESSAGE_LABELS.items()]
    rows.extend([[('♻️ Сбросить все сообщения', 'd4s_messages_reset')], [('🔙 Назад', 'd4s_order_set')]])
    kb = _make_kb(rows)
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _menu_maintenance(chat_id, message_id=None) -> None:
    log_size = Path(LOG_FILE).stat().st_size if Path(LOG_FILE).exists() else 0
    backups = len(list(Path(BACKUPS_DIR).glob('*.zip')))
    text = f'🧰 <b>Обслуживание</b>\n\n📄 Лог: <code>{log_size} байт</code>\n💾 Резервных копий: <code>{backups}</code>\n📂 Данные: <code>storage/plugins/dim4n4ik_shop</code>\n\nЗдесь можно проверить логи и сделать резервную копию/восстановление конфигурации.'
    kb = _make_kb([[('📄 Логи', 'd4s_logs')], [('💾 Конфиг и резервные копии', 'd4s_config')], [('🔙 Назад', 'd4s_plugin_set')]])
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _menu_logs(chat_id, message_id=None) -> None:
    path = Path(LOG_FILE)
    tail = 'Лог пока пуст.'
    if path.exists():
        try:
            lines = path.read_text(encoding='utf-8', errors='replace').splitlines()[-20:]
            tail = '\n'.join(lines)[-2800:] or 'Лог пока пуст.'
        except Exception as e:
            tail = f'Не удалось прочитать лог: {e}'
    safe = tail.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    text = f'📄 <b>Логи</b>\n\nПоследние записи:\n<code>{safe}</code>'
    kb = _make_kb([[('📥 Скачать лог', 'd4s_logs_download')], [('🗑 Очистить лог', 'd4s_logs_clear_ask')], [('🔙 Назад', 'd4s_maintenance')]])
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _menu_log_clear_confirm(chat_id, message_id=None) -> None:
    kb = _make_kb([[('✅ Очистить', 'd4s_logs_clear_yes'), ('❌ Отмена', 'd4s_logs')]])
    text = '⚠️ <b>Очистить лог плагина?</b>\n\nФайл будет очищен. Настройки, заказы и базы аккаунтов не затрагиваются.'
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _menu_config(chat_id, message_id=None) -> None:
    backups = sorted(Path(BACKUPS_DIR).glob('*.zip'), reverse=True)
    latest = backups[0].name if backups else 'нет'
    text = f'💾 <b>Конфиг и резервные копии</b>\n\nПоследняя копия: <code>{latest}</code>\n\nЭкспорт включает настройки, привязки, состояния заказов, статистику и базы аккаунтов. Перед импортом автоматически создаётся отдельная копия текущих данных.\n\n⚠️ Архив содержит API-ключ и сами аккаунты из баз. Не передавайте его посторонним.'
    kb = _make_kb([[('📦 Создать резервную копию', 'd4s_backup_create')], [('📤 Экспортировать конфиг', 'd4s_backup_export')], [('📥 Импортировать конфиг', 'd4s_backup_import')], [('🩺 Проверить / восстановить', 'd4s_storage_check')], [('🔙 Назад', 'd4s_maintenance')]])
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _menu_databases(chat_id, message_id=None) -> None:
    meta = _load_databases_meta()
    rows = []
    lines = ['🗃 <b>Базы аккаунтов и почт</b>', '', 'Steam-базы можно пополнять через dim4n4ik.shop, а почтовые базы — только текстом или файлом.', '']
    for db in meta['databases']:
        available = _database_stock(db['id'])
        reserved = _database_reserved_count(db['id'])
        icon = '📧' if _is_mail_database(db) else '🗃'
        lines.append(f"• <b>{db['name']}</b> — {db['product_title']}: {available} доступно, {reserved} в резерве")
        rows.append([(f"{icon} {db['name']} · {available} шт.", f"d4s_db:{db['id']}")])
    if not meta['databases']:
        lines.append('Баз пока нет.')
    rows.append([('➕ Создать базу', 'd4s_db_create')])
    rows.append([('🔙 Назад', 'd4s_plugin_set')])
    kb = _make_kb(rows)
    text = '\n'.join(lines)
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _menu_database_detail(chat_id, message_id, database_id: str) -> None:
    db = _database_by_id(database_id)
    if not db:
        _menu_databases(chat_id, message_id)
        return
    available = _database_stock(database_id)
    reserved = _database_reserved_count(database_id)
    refs = _database_references(database_id)
    mail = _is_mail_database(db)
    if mail:
        text = f"📧 <b>{db['name']}</b>\n\n📧 Тип: <b>{db['product_title']}</b>\n📥 Пополнение: <b>только текстом или файлом</b>\n🛒 Магазин почт: <a href=\"{MAIL_BOT_URL}\">открыть бота</a>\n✅ Доступно: <b>{available}</b>\n⏳ В резерве: <b>{reserved}</b>\n➕ Всего добавлено: <b>{db['total_added']}</b>\n🛒 Продано из базы: <b>{db['total_sold']}</b>\n🔗 Используют лоты: <b>{len(refs)}</b>"
    else:
        text = f"🗃 <b>{db['name']}</b>\n\n📦 Товар: <b>{db['product_title']}</b>\nID товара: <code>{db['product_id']}</code>\n🎮 Steam-магазин: <a href=\"{SHOP_BOT_URL}\">открыть бота</a>\n✅ Доступно: <b>{available}</b>\n⏳ В резерве: <b>{reserved}</b>\n➕ Всего добавлено: <b>{db['total_added']}</b>\n🛒 Продано из базы: <b>{db['total_sold']}</b>\n🔗 Используют лоты: <b>{len(refs)}</b>"
    rows = [[('👁 Просмотреть аккаунты', f'd4s_db_view:{database_id}:available:0')]]
    if not mail:
        rows.append([('🛒 Купить через dim4n4ik.shop', f'd4s_db_replenish:{database_id}')])
    rows.extend([[('📝 Добавить текстом', f'd4s_db_import_text:{database_id}'), ('📎 Загрузить файлом', f'd4s_db_import_file:{database_id}')], [('✏️ Переименовать', f'd4s_db_rename:{database_id}')], [('🗑 Удалить базу', f'd4s_db_delete_ask:{database_id}')], [('🔙 К базам', 'd4s_databases')]])
    kb = _make_kb(rows)
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _menu_database_items(chat_id, message_id, database_id: str, section: str='available', page: int=0) -> None:
    db = _database_by_id(database_id)
    if not db:
        _menu_databases(chat_id, message_id)
        return
    inv = _load_database_inventory(database_id)
    rows_data = []
    if section == 'reserved':
        for order_id, values in inv.get('reserved', {}).items():
            for value in values:
                rows_data.append((str(value), str(order_id)))
    else:
        section = 'available'
        rows_data = [(str(value), '') for value in inv.get('available', [])]
    shown = rows_data[:10]
    label = 'Доступные' if section == 'available' else 'В резерве'
    lines = [f"👁 <b>{db['name']}</b>", f"{label}: <b>{len(rows_data)}</b>", f'Показаны первые: <b>{len(shown)}</b> из <b>{len(rows_data)}</b>', '']
    if shown:
        for idx, (value, order_id) in enumerate(shown, start=1):
            safe = value.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            suffix = f' · заказ <code>{order_id}</code>' if order_id else ''
            lines.append(f'<b>{idx}.</b> <code>{safe}</code>{suffix}')
    else:
        lines.append('Записей нет.')
    rows = [[('✅ Доступные', f'd4s_db_view:{database_id}:available:0'), ('⏳ Резерв', f'd4s_db_view:{database_id}:reserved:0')]]
    if section == 'available' and rows_data:
        rows.append([('📥 Скачать доступные .txt', f'd4s_db_export:{database_id}')])
    rows.append([('🔙 К базе', f'd4s_db:{database_id}')])
    kb = _make_kb(rows)
    text = '\n'.join(lines)
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _send_database_export(chat_id, database_id: str) -> bool:
    db = _database_by_id(database_id)
    if not db:
        return False
    values = _load_database_inventory(database_id).get('available', [])
    if not values:
        return False
    Path(BACKUPS_DIR).mkdir(parents=True, exist_ok=True)
    safe_name = re.sub('[^A-Za-z0-9_-]', '_', str(db.get('name') or 'database'))[:40] or 'database'
    path = Path(BACKUPS_DIR) / f'{safe_name}-{database_id}-{int(time.time() * 1000)}.txt'
    try:
        path.write_text('\n'.join(str(v) for v in values) + '\n', encoding='utf-8')
        return _send_document(chat_id, str(path), f"🗃 {db['name']} · доступно {len(values)}")
    finally:
        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass
def _menu_database_delete_confirm(chat_id, message_id, database_id: str) -> None:
    db = _database_by_id(database_id)
    if not db:
        _menu_databases(chat_id, message_id)
        return
    refs = _database_references(database_id)
    if refs:
        text = f"❌ Базу <b>{db['name']}</b> нельзя удалить: её используют лоты <code>{', '.join(refs[:10])}</code>. Сначала смените режим этих лотов или удалите их привязки."
        kb = _make_kb([[('🔙 Назад', f'd4s_db:{database_id}')]])
    else:
        text = f"⚠️ <b>Удалить базу «{db['name']}»?</b>\n\nБудут безвозвратно удалены все { _database_stock(database_id) } доступных аккаунтов этой базы."
        kb = _make_kb([[('✅ Удалить', f'd4s_db_delete_yes:{database_id}'), ('❌ Отмена', f'd4s_db:{database_id}')]])
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _menu_database_product_select(chat_id, message_id=None, page: int=0) -> None:
    try:
        items = _visible_catalog()
    except Exception as e:
        _tg_edit(chat_id, message_id, f'❌ Каталог недоступен: {e}', _make_kb([[('🔙 К базам', 'd4s_databases')]]))
        return
    pages = max(1, (len(items) + 7) // 8)
    page = max(0, min(int(page), pages - 1))
    rows = []
    for item in items[page * 8:(page + 1) * 8]:
        rows.append([(f"{str(item.get('title'))[:30]} · {_fmt_rub_kop(int(item.get('price_kop', 0)))} · {item.get('in_stock', 0)} шт.", f"d4s_dbprod:{item.get('id')}")])
    if pages > 1:
        rows.append([('⬅️', f'd4s_dbprodp:{max(0, page - 1)}'), (f'{page + 1}/{pages}', 'd4s_noop'), ('➡️', f'd4s_dbprodp:{min(pages - 1, page + 1)}')])
    rows.append([('❌ Отмена', 'd4s_databases')])
    text = '🗃 <b>Создание базы</b>\n\nВыберите товар dim4n4ik.shop. В этой базе будут храниться только аккаунты этого товара.'
    _tg_edit(chat_id, message_id, text, _make_kb(rows)) if message_id else _tg_send(chat_id, text, _make_kb(rows))
def _lot_field_title(fields: Any, lot_id: str) -> str:
    for key in ('title_ru', 'title_en', 'title', 'name', 'short_description'):
        value = getattr(fields, key, None)
        if value:
            return re.sub(r'\s+', ' ', str(value)).strip()[:120]
    return f'LOT {lot_id}'
def _ignored_lot_ids() -> set:
    raw = cfg_get('ignored_lot_ids')
    if not isinstance(raw, (list, tuple, set)):
        return set()
    return {str(value) for value in raw if str(value).isdigit()}
def _is_lot_ignored(lot_id: str) -> bool:
    return str(lot_id) in _ignored_lot_ids()
def _set_lot_ignored(lot_id: str, ignored: bool) -> None:
    lot_id = str(lot_id)
    values = _ignored_lot_ids()
    if ignored:
        if lot_id.isdigit():
            values.add(lot_id)
    else:
        values.discard(lot_id)
    cfg_set('ignored_lot_ids', sorted(values, key=lambda value: int(value)))
def _restore_lot_to_plugin(lot_id: str) -> None:
    _set_lot_ignored(str(lot_id), False)
def _cached_funpay_lots() -> List[Dict[str, Any]]:
    raw = cfg_get('lot_cache')
    ignored = _ignored_lot_ids()
    rows = {}
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict) and str(item.get('lot_id', '')).isdigit() and str(item.get('lot_id')) not in ignored:
                rows[str(item['lot_id'])] = dict(item)
    with _bindings_lock:
        for lot_id, binding in _bindings.items():
            if str(lot_id) in ignored:
                continue
            if str(lot_id) not in rows:
                rows[str(lot_id)] = {'lot_id': str(lot_id), 'title': binding.get('lot_name') or f'LOT {lot_id}', 'active': bool(binding.get('enabled', True))}
    return sorted(rows.values(), key=lambda x: (str(x.get('title', '')).casefold(), int(x.get('lot_id', 0))))
def _save_funpay_lot_cache(rows: List[Dict[str, Any]]) -> None:
    clean = []
    seen = set()
    ignored = _ignored_lot_ids()
    for item in rows:
        lot_id = str(item.get('lot_id') or '')
        if not lot_id.isdigit() or lot_id in seen or lot_id in ignored:
            continue
        seen.add(lot_id)
        clean.append({'lot_id': lot_id, 'title': str(item.get('title') or f'LOT {lot_id}')[:120], 'active': bool(item.get('active', True))})
    cfg_set('lot_cache', clean)
def _cache_funpay_lot(item: Dict[str, Any]) -> None:
    lot_id = str(item.get('lot_id') or '')
    if _is_lot_ignored(lot_id):
        return
    rows = {str(x.get('lot_id')): dict(x) for x in _cached_funpay_lots()}
    rows[lot_id] = dict(item)
    _save_funpay_lot_cache(list(rows.values()))
def _remove_lot_from_plugin(lot_id: str) -> None:
    lot_id = str(lot_id)
    with _bindings_lock:
        _bindings.pop(lot_id, None)
        _save_bindings()
    _auto_disabled.pop(lot_id, None)
    _save_auto_disabled()
    rows = [item for item in _cached_funpay_lots() if str(item.get('lot_id')) != lot_id]
    _save_funpay_lot_cache(rows)
    _set_lot_ignored(lot_id, True)
def _validate_funpay_lot(lot_id: str) -> Dict[str, Any]:
    if cardinal is None or not str(lot_id).isdigit():
        raise ValueError('Некорректный LOT ID')
    fields = cardinal.account.get_lot_fields(int(lot_id))
    item = {'lot_id': str(lot_id), 'title': _lot_field_title(fields, str(lot_id)), 'active': bool(getattr(fields, 'active', True))}
    _cache_funpay_lot(item)
    return item
def _discover_funpay_lots() -> Dict[str, Any]:
    global _last_lot_discovery_ts, _last_lot_discovery_report
    if cardinal is None:
        raise ValueError('Cardinal ещё не инициализирован')
    ids = set()
    objects = {}
    category_counts = {category_id: 0 for category_id in AUTO_LOT_CATEGORIES}
    category_failures = 0
    def collect(value):
        if isinstance(value, dict):
            for key, child in value.items():
                try:
                    key_id = int(getattr(key, 'id', key))
                    if key_id > 0:
                        ids.add(str(key_id))
                except Exception:
                    pass
                collect(child)
        elif isinstance(value, (list, tuple, set)):
            for child in value:
                collect(child)
        else:
            try:
                lot_id = int(getattr(value, 'id'))
                if lot_id > 0:
                    ids.add(str(lot_id))
                    objects[str(lot_id)] = value
            except Exception:
                pass
    account = cardinal.account
    for category_id in AUTO_LOT_CATEGORIES:
        try:
            category_lots = account.get_my_subcategory_lots(int(category_id)) or []
            category_ids = set()
            for lot in category_lots:
                try:
                    lot_id = int(getattr(lot, 'id'))
                    if lot_id > 0:
                        category_ids.add(str(lot_id))
                except Exception:
                    pass
                collect(lot)
            category_counts[category_id] = len(category_ids)
        except Exception as e:
            category_failures += 1
            logger.warning(f'{LP} get_my_subcategory_lots({category_id}): {e}')
    if category_failures == len(AUTO_LOT_CATEGORIES):
        try:
            updater = getattr(cardinal, 'update_lots_and_categories', None)
            if callable(updater):
                updater()
        except Exception:
            pass
        profile = getattr(cardinal, 'tg_profile', None) or getattr(cardinal, 'profile', None)
        if profile and callable(getattr(profile, 'get_sorted_lots', None)):
            for mode in (2, 1, 0, 3):
                try:
                    collect(profile.get_sorted_lots(mode) or {})
                except Exception:
                    pass
        try:
            for category in account.get_categories() or []:
                for subcategory in getattr(category, 'subcategories', None) or []:
                    collect(getattr(subcategory, 'lots', None) or [])
                collect(getattr(category, 'lots', None) or [])
        except Exception:
            pass
    for item in _cached_funpay_lots():
        lot_id = str(item.get('lot_id') or '')
        if lot_id.isdigit():
            ids.add(lot_id)
            objects.setdefault(lot_id, SimpleNamespace(id=int(lot_id), title_ru=item.get('title') or f'LOT {lot_id}', active=item.get('active', True)))
    with _bindings_lock:
        ids.update(str(x) for x in _bindings.keys() if str(x).isdigit())
    found = []
    errors = 0
    ignored = _ignored_lot_ids()
    for lot_id in sorted(ids, key=lambda x: int(x)):
        if lot_id in ignored:
            continue
        try:
            fields = account.get_lot_fields(int(lot_id))
            found.append({'lot_id': lot_id, 'title': _lot_field_title(fields, lot_id), 'active': bool(getattr(fields, 'active', True))})
        except Exception:
            obj = objects.get(lot_id)
            if obj is not None:
                found.append({'lot_id': lot_id, 'title': _lot_field_title(obj, lot_id), 'active': bool(getattr(obj, 'active', True))})
            else:
                errors += 1
    _save_funpay_lot_cache(found)
    report = {'found': len(found), 'errors': errors, 'category_counts': category_counts}
    _last_lot_discovery_ts = time.time()
    _last_lot_discovery_report = report
    return report
def _menu_lot_detail(chat_id, message_id, lot_id: str) -> None:
    if _is_lot_ignored(str(lot_id)):
        text = f'ℹ️ Лот <code>{lot_id}</code> удалён из плагина. Чтобы добавить его снова, используйте «Добавить LOT ID».'
        kb = _make_kb([[('🔙 К лотам', 'd4s_lot_set')]])
        _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
        return
    lot = next((x for x in _cached_funpay_lots() if str(x.get('lot_id')) == str(lot_id)), None)
    if not lot:
        try:
            lot = _validate_funpay_lot(lot_id)
        except Exception as e:
            _tg_edit(chat_id, message_id, f'❌ Лот {lot_id} не найден: {e}', _make_kb([[('🔙 К лотам', 'd4s_lot_set')]]))
            return
    with _bindings_lock:
        raw = _bindings.get(str(lot_id))
    binding = _normalize_binding(raw) if raw else None
    lines = [f"🏷 <b>{lot.get('title')}</b>", f'LOT ID: <code>{lot_id}</code>', f"FunPay: <b>{'🟢 включён' if lot.get('active', True) else '🔴 выключен'}</b>", '']
    mode = str(binding.get('delivery_mode') or 'api') if binding else ''
    mail = bool(binding and _binding_is_mail(binding))
    db = None
    if binding:
        if mode == 'database':
            db = _database_by_id(str(binding.get('database_id') or ''))
            if mail:
                source = f"📧 {db.get('name')} — {MAIL_PRODUCT_TITLE}" if db else '📧 база почт не найдена'
            else:
                source = f"🗃 {db.get('name')} — {db.get('product_title')}" if db else '🗃 база не найдена'
        else:
            source = f"🌐 {binding.get('product_title')} (id {binding.get('product_id')})"
        if mail:
            lines.extend([f'Тип: <b>📧 {MAIL_PRODUCT_TITLE}</b>', 'Режим: <b>🗃 Выдавать из отдельной базы почт</b>', f'Источник: <b>{source}</b>', f"За 1 единицу заказа: <b>×{_binding_qty_per_unit(binding)}</b>", f"Автовыдача FunPay: <b>{_binding_stock_target(binding)}</b> позиций", f"Доступно продаж по источнику: <b>{_binding_effective_stock_cached(binding) if _binding_effective_stock_cached(binding) is not None else '—'}</b>"])
        else:
            lines.extend([f"Режим: <b>{'🗃 Выдавать из базы' if mode == 'database' else '🌐 Покупать при заказе'}</b>", f'Источник: <b>{source}</b>', f"За 1 единицу заказа: <b>×{_binding_qty_per_unit(binding)}</b>", f"Автовыдача FunPay: <b>{_binding_stock_target(binding)}</b> позиций", f"Доступно продаж по источнику: <b>{_binding_effective_stock_cached(binding) if _binding_effective_stock_cached(binding) is not None else '—'}</b>"])
    else:
        lines.append('Лот ещё не настроен в плагине. Сначала выберите режим выдачи.')
    state_label = '🟢 Лот: ВКЛ' if lot.get('active', True) else '🔴 Лот: ВЫКЛ'
    rows = [[(state_label, f'd4s_lot_toggle:{lot_id}')]]
    if mail:
        db_name = str(db.get('name')) if db else 'не найдена'
        database_id = str(binding.get('database_id') or '')
        rows.append([(f'📧 База почт: {db_name[:30]}', f'd4s_db:{database_id}')])
    else:
        mode_label = '🚚 Режим: не выбран'
        if mode == 'database':
            mode_label = '🚚 Режим: из базы данных'
        elif mode == 'api':
            mode_label = '🚚 Режим: покупать при заказе'
        rows.append([(mode_label, f'd4s_lot_mode_menu:{lot_id}')])
        if binding:
            if mode == 'database':
                db_name = str(db.get('name')) if db else 'не выбрана'
                rows.append([(f'🗃 База данных: {db_name[:28]}', f'd4s_lot_database:{lot_id}')])
            else:
                product_title = str(binding.get('product_title') or 'не выбран')
                rows.append([(f'🌐 Товар: {product_title[:30]}', f'd4s_lot_mode_api:{lot_id}')])
    if binding:
        rows.append([('🔢 Количество за покупку', f'd4s_lot_qty:{lot_id}'), ('⚡ Кол-во в автовыдаче', f'd4s_lot_stock:{lot_id}')])
    rows.extend([[('🗑 Удалить лот', f'd4s_lot_delete_menu:{lot_id}')], [('🔙 К лотам', 'd4s_lot_set')]])
    _tg_edit(chat_id, message_id, '\n'.join(lines), _make_kb(rows)) if message_id else _tg_send(chat_id, '\n'.join(lines), _make_kb(rows))
def _menu_lot_type_pick(chat_id, message_id, lot_id: str) -> None:
    text = '📦 <b>Тип товара лота</b>\n\nВыберите, что продаётся в этом лоте.'
    rows = [[('🎮 Steam аккаунт', f'd4s_lot_type_steam:{lot_id}')], [('📧 Почты Hotmail / Outlook', f'd4s_lot_type_mail:{lot_id}')], [('🔙 К лотам', 'd4s_lot_set')]]
    kb = _make_kb(rows)
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _binding_is_mail(binding: Any) -> bool:
    if not isinstance(binding, dict):
        return False
    if str(binding.get('source_type') or '').lower() == 'mail':
        return True
    database_id = str(binding.get('database_id') or '')
    return str(binding.get('delivery_mode') or '') == 'database' and bool(database_id) and _is_mail_database(_database_by_id(database_id))
def _configure_mail_lot(lot_id: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    lot_id = str(lot_id)
    db = _create_mail_database(lot_id)
    lot = next((x for x in _cached_funpay_lots() if str(x.get('lot_id')) == lot_id), {})
    with _bindings_lock:
        old = _normalize_binding(_bindings.get(lot_id) or {})
        target = old.get('fp_stock_target') if old else _fp_buffer()
        if int(target or 0) <= 0:
            target = _fp_buffer()
        binding = {'product_id': 0, 'product_title': MAIL_PRODUCT_TITLE, 'lot_name': str(lot.get('title') or old.get('lot_name') or f'LOT {lot_id}'), 'group': old.get('group') or '', 'enabled': old.get('enabled', True), 'delivery_mode': 'database', 'database_id': str(db['id']), 'source_type': 'mail', 'qty_per_unit': old.get('qty_per_unit', 1), 'qty': old.get('qty_per_unit', 1), 'fp_stock_target': target, 'fp_auto': True}
        _bindings[lot_id] = _normalize_binding(binding)
        _save_bindings()
    return db, _bindings[lot_id]
def _menu_lot_mode_pick(chat_id, message_id, lot_id: str) -> None:
    with _bindings_lock:
        raw = _bindings.get(str(lot_id))
    binding = _normalize_binding(raw) if raw else None
    if binding and _binding_is_mail(binding):
        _menu_database_detail(chat_id, message_id, str(binding.get('database_id') or ''))
        return
    current = str(binding.get('delivery_mode') or '') if binding else ''
    api_label = ('✅ ' if current == 'api' else '') + '🌐 Покупать при заказе'
    db_label = ('✅ ' if current == 'database' else '') + '🗃 Выдавать из базы данных'
    rows = [[(api_label, f'd4s_lot_mode_api:{lot_id}')], [(db_label, f'd4s_lot_mode_db:{lot_id}')], [('🔙 Назад', f'd4s_lot_pick:{lot_id}')]]
    text = '🚚 <b>Режим выдачи</b>\n\nВыберите, как этот лот будет получать товар.'
    _tg_edit(chat_id, message_id, text, _make_kb(rows)) if message_id else _tg_send(chat_id, text, _make_kb(rows))
def _menu_lot_api_products(chat_id, message_id, lot_id: str, page: int=0) -> None:
    try:
        items = _visible_catalog()
    except Exception as e:
        _tg_edit(chat_id, message_id, f'❌ Каталог недоступен: {e}', _make_kb([[('🔙 Назад', f'd4s_lot_pick:{lot_id}')]]))
        return
    pages = max(1, (len(items) + 7) // 8)
    page = max(0, min(page, pages - 1))
    rows = [[(f"{str(it.get('title'))[:30]} · {it.get('in_stock', 0)} шт.", f"d4s_lot_apip:{lot_id}:{it.get('id')}")] for it in items[page * 8:(page + 1) * 8]]
    if pages > 1:
        rows.append([('⬅️', f'd4s_lot_apipp:{lot_id}:{max(0,page-1)}'), (f'{page+1}/{pages}', 'd4s_noop'), ('➡️', f'd4s_lot_apipp:{lot_id}:{min(pages-1,page+1)}')])
    rows.append([('❌ Отмена', f'd4s_lot_pick:{lot_id}')])
    _tg_edit(chat_id, message_id, '🌐 <b>Покупать при заказе</b>\n\nВыберите товар dim4n4ik.shop. При каждой покупке лота плагин купит нужное количество через API.', _make_kb(rows))
def _menu_lot_database_pick(chat_id, message_id, lot_id: str) -> None:
    meta = _load_databases_meta()
    rows = []
    for db in meta['databases']:
        if _is_mail_database(db):
            continue
        rows.append([(f"🗃 {db['name']} · {_database_stock(db['id'])} шт. · {db['product_title'][:22]}", f"d4s_lot_dbp:{lot_id}:{db['id']}")])
    if not rows:
        rows.append([('➕ Сначала создать базу', 'd4s_databases')])
    rows.append([('❌ Отмена', f'd4s_lot_pick:{lot_id}')])
    _tg_edit(chat_id, message_id, '🗃 <b>Выдавать из базы</b>\n\nВыберите заранее пополняемую базу аккаунтов.', _make_kb(rows))
def _configure_lot_api(lot_id: str, product_id: int) -> Dict[str, Any]:
    with _bindings_lock:
        existing = dict(_bindings.get(str(lot_id)) or {})
    if _binding_is_mail(existing):
        raise ValueError('Почтовый лот работает только из своей базы почт')
    item = next((x for x in _get_catalog_cached() if int(x.get('id', -1)) == int(product_id)), None)
    if not item or not _is_text_kind(item):
        raise ValueError('Товар не найден или не является текстовым')
    with _bindings_lock:
        old = _normalize_binding(_bindings.get(str(lot_id)) or {})
        lot = next((x for x in _cached_funpay_lots() if str(x.get('lot_id')) == str(lot_id)), {})
        binding = {'product_id': int(product_id), 'product_title': str(item.get('title') or f'товар {product_id}'), 'lot_name': str(lot.get('title') or old.get('lot_name') or f'LOT {lot_id}'), 'group': old.get('group') or '', 'enabled': old.get('enabled', True), 'delivery_mode': 'api', 'database_id': '', 'qty_per_unit': old.get('qty_per_unit', 1), 'qty': old.get('qty_per_unit', 1), 'fp_stock_target': old.get('fp_stock_target') if old else _fp_buffer()}
        if int(binding.get('fp_stock_target') or 0) <= 0:
            binding['fp_stock_target'] = _fp_buffer()
        binding['fp_auto'] = True
        _bindings[str(lot_id)] = _normalize_binding(binding)
        _save_bindings()
    _apply_lot_sync(str(lot_id), int(product_id))
    return _bindings[str(lot_id)]
def _configure_lot_database(lot_id: str, database_id: str) -> Dict[str, Any]:
    db = _database_by_id(database_id)
    if not db:
        raise ValueError('База не найдена')
    with _bindings_lock:
        existing = dict(_bindings.get(str(lot_id)) or {})
    if _binding_is_mail(existing):
        raise ValueError('Почтовый лот привязан только к своей базе почт')
    if _is_mail_database(db):
        raise ValueError('Почтовая база закреплена за своим почтовым лотом')
    with _bindings_lock:
        old = _normalize_binding(_bindings.get(str(lot_id)) or {})
        lot = next((x for x in _cached_funpay_lots() if str(x.get('lot_id')) == str(lot_id)), {})
        target = old.get('fp_stock_target') if old else _fp_buffer()
        if int(target or 0) <= 0:
            target = _fp_buffer()
        binding = {'product_id': int(db['product_id']), 'product_title': str(db['product_title']), 'lot_name': str(lot.get('title') or old.get('lot_name') or f'LOT {lot_id}'), 'group': old.get('group') or '', 'enabled': old.get('enabled', True), 'delivery_mode': 'database', 'database_id': str(database_id), 'qty_per_unit': old.get('qty_per_unit', 1), 'qty': old.get('qty_per_unit', 1), 'fp_stock_target': target, 'fp_auto': True}
        _bindings[str(lot_id)] = _normalize_binding(binding)
        _save_bindings()
    _apply_lot_sync(str(lot_id), int(db['product_id']))
    return _bindings[str(lot_id)]
def _menu_lot_delete_options(chat_id, message_id, lot_id: str) -> None:
    text = f'🗑 <b>Удаление лота {lot_id}</b>\n\nВыберите, что именно удалить.'
    kb = _make_kb([[('🧩 Только из плагина', f'd4s_lot_unbind_ask:{lot_id}')], [('🔥 С FunPay и из плагина', f'd4s_lot_delete_ask:{lot_id}')], [('❌ Отмена', f'd4s_lot_pick:{lot_id}')]])
    _tg_edit(chat_id, message_id, text, kb)
def _menu_lot_unbind_confirm(chat_id, message_id, lot_id: str) -> None:
    text = f'⚠️ <b>Удалить лот {lot_id} только из плагина?</b>\n\nСам лот на FunPay останется. Плагин перестанет обрабатывать его заказы.'
    kb = _make_kb([[('✅ Только из плагина', f'd4s_lot_unbind_yes:{lot_id}'), ('❌ Отмена', f'd4s_lot_pick:{lot_id}')]])
    _tg_edit(chat_id, message_id, text, kb)
def _menu_lot_delete_confirm(chat_id, message_id, lot_id: str) -> None:
    text = f'🔥 <b>Удалить лот {lot_id} с FunPay?</b>\n\nЛот будет удалён с FunPay, а его привязка в плагине будет убрана. Это действие необратимо.'
    kb = _make_kb([[('🔥 Да, удалить лот', f'd4s_lot_delete_yes:{lot_id}'), ('❌ Отмена', f'd4s_lot_pick:{lot_id}')]])
    _tg_edit(chat_id, message_id, text, kb)
def _resync_database_lots(database_id: str) -> None:
    with _bindings_lock:
        targets = [(str(lot_id), _normalize_binding(b)) for lot_id, b in _bindings.items() if str(b.get('delivery_mode') or '') == 'database' and str(b.get('database_id') or '') == str(database_id) and b.get('enabled', True)]
    for lot_id, binding in targets:
        _sync_binding_stock(lot_id, binding)
        time.sleep(0.15)
def _menu_lot_settings(chat_id, message_id=None, page: int=0) -> None:
    report = _last_lot_discovery_report
    lots = _cached_funpay_lots()
    pages = max(1, (len(lots) + 7) // 8)
    page = max(0, min(int(page), pages - 1))
    with _bindings_lock:
        mappings = {str(k): _normalize_binding(v) for k, v in _bindings.items()}
    counts = report.get('category_counts', {}) if isinstance(report, dict) else {}
    text = f'🔗 <b>Настройки лотов</b>\n\nАвтопоиск категорий: 89: <b>{int(counts.get(89, 0) or 0)}</b> · 1350: <b>{int(counts.get(1350, 0) or 0)}</b> · 938: <b>{int(counts.get(938, 0) or 0)}</b>\nНайдено FunPay-лотов: <b>{len(lots)}</b>\nНастроено: <b>{len(mappings)}</b>\n\nВыберите лот. Для каждого можно выбрать покупку при заказе или выдачу из заранее пополненной базы.\nСтраница {page + 1}/{pages}.'
    rows = [[('🔄 Найти лоты', 'd4s_lot_discover'), ('➕ Добавить LOT ID', 'd4s_lot_manual')]]
    for lot in lots[page * 8:(page + 1) * 8]:
        lot_id = str(lot.get('lot_id'))
        state = '🟢' if lot.get('active', True) else '🔴'
        mark = '✅' if lot_id in mappings else '➕'
        title = str(lot.get('title') or f'LOT {lot_id}')[:32]
        rows.append([(f'{state} {mark} {title} · {lot_id}', f'd4s_lot_pick:{lot_id}')])
    if pages > 1:
        nav = []
        if page > 0:
            nav.append(('⬅️', f'd4s_lots:{page - 1}'))
        nav.append((f'{page + 1}/{pages}', 'd4s_noop'))
        if page < pages - 1:
            nav.append(('➡️', f'd4s_lots:{page + 1}'))
        rows.append(nav)
    rows.append([('🙈 Категории каталога', 'd4s_hidecats')])
    rows.append([('🔙 Назад', 'd4s_main')])
    kb = _make_kb(rows)
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _menu_settings(chat_id, message_id=None) -> None:
    _menu_plugin_settings(chat_id, message_id)
PAGE_SIZE = 8
def _menu_bindings(chat_id, message_id=None) -> None:
    global _grp_idx
    with _bindings_lock:
        total = len(_bindings)
        by_group: Dict[str, int] = {}
        for b in _bindings.values():
            by_group[b.get('group') or ''] = by_group.get(b.get('group') or '', 0) + 1
    if not total:
        kb = _make_kb([[('➕ Добавить привязку', 'd4s_add')], [('🔙 Настройки лотов', 'd4s_lot_set')]])
        txt = '🔗 <b>Привязок пока нет</b>\n\nПривязка связывает лот FunPay с товаром магазина: при продаже лота плагин купит товар по API и выдаст покупателю.\nПривязки можно раскладывать по своим группам (CS2, Dota 2, PUBG…).'
        _tg_edit(chat_id, message_id, txt, kb) if message_id else _tg_send(chat_id, txt, kb)
        return
    _grp_idx = sorted((g for g in by_group if g))
    rows = []
    for gi, g in enumerate(_grp_idx):
        rows.append([(f'📁 {g} ({by_group[g]})', f'd4s_bindg:{gi}:0')])
    if by_group.get(''):
        rows.append([(f"📂 {NO_GROUP} ({by_group['']})", 'd4s_bindg:-1:0')])
    rows.append([('➕ Добавить', 'd4s_add'), ('🔙 Настройки лотов', 'd4s_lot_set')])
    text = f'🔗 <b>Привязки лотов</b> ({total})\nВыберите группу:'
    kb = _make_kb(rows)
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _group_by_idx(gi: int) -> Optional[str]:
    if gi == -1:
        return ''
    if 0 <= gi < len(_grp_idx):
        return _grp_idx[gi]
    return None
def _group_items(group: str) -> List[Tuple[str, Dict[str, Any]]]:
    with _bindings_lock:
        return sorted(((k, dict(v)) for k, v in _bindings.items() if (v.get('group') or '') == group), key=lambda kv: kv[0])
def _menu_group(chat_id, message_id, gi: int, page: int=0) -> None:
    group = _group_by_idx(gi)
    if group is None:
        _menu_bindings(chat_id, message_id)
        return
    items = _group_items(group)
    if not items:
        _grp_select.pop(chat_id, None)
        _menu_bindings(chat_id, message_id)
        return
    sel_state = _grp_select.get(chat_id)
    select_mode = bool(sel_state and sel_state.get('gi') == gi)
    sel = set(sel_state['sel']) if select_mode else set()
    pages = max((len(items) + PAGE_SIZE - 1) // PAGE_SIZE, 1)
    page = max(0, min(page, pages - 1))
    rows = []
    for lot_id, b in items[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]:
        mark = '✅' if b.get('enabled', True) else '⏸'
        title = (b.get('product_title') or str(b.get('product_id')))[:25]
        if select_mode:
            check = '🔘' if lot_id in sel else '⚪️'
            rows.append([(f'{check} {mark} {lot_id} → {title}', f'd4s_gtog:{gi}:{page}:{lot_id}')])
        else:
            rows.append([(f"{mark} {lot_id} → {title} ×{b.get('qty', 1)}", f'd4s_bind:{lot_id}')])
    nav = []
    if page > 0:
        nav.append(('⬅️', f'd4s_bindg:{gi}:{page - 1}'))
    nav.append((f'{page + 1}/{pages}', 'd4s_noop'))
    if page < pages - 1:
        nav.append(('➡️', f'd4s_bindg:{gi}:{page + 1}'))
    rows.append(nav)
    gname = group or NO_GROUP
    on = sum((1 for _, b in items if b.get('enabled', True)))
    if select_mode:
        rows.append([(f'▶️ Вкл ({len(sel)})', f'd4s_gon:{gi}'), (f'⏸ Выкл ({len(sel)})', f'd4s_goff:{gi}')])
        rows.append([(f'🗑 Удалить привязки ({len(sel)})', f'd4s_gdel:{gi}')])
        rows.append([('✖️ Готово', f'd4s_gselx:{gi}:{page}')])
        text = f'📁 <b>{gname}</b> — выбор лотов\nОтметьте лоты и примените действие.\n🗑 удаляет только привязку (лот на FunPay остаётся).'
    else:
        rows.append([('🌍 Добавить страну (новый лот)', f'd4s_gadd:{gi}:0')])
        rows.append([('☑️ Выбрать несколько', f'd4s_gsel:{gi}:{page}')])
        if group:
            rows.append([('✏️ Переименовать группу', f'd4s_grpren:{gi}')])
        rows.append([('🔙 К группам', 'd4s_bind_list'), ('🏠 Меню', 'd4s_main')])
        text = f'📁 <b>{gname}</b> · {len(items)} лот(ов) · вкл {on}\nНажмите для управления:'
    kb = _make_kb(rows)
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _grp_first_source(group: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    items = _group_items(group)
    if not items:
        return None
    return min(items, key=lambda kv: kv[1].get('created_at', ''))
def _grp_batch_active(chat_id, gi: int, active: bool) -> None:
    sel_state = _grp_select.get(chat_id)
    group = _group_by_idx(gi)
    if not sel_state or sel_state.get('gi') != gi or group is None:
        return
    sel = list(sel_state.get('sel') or [])
    if not sel:
        _tg_send(chat_id, 'Ничего не выбрано.')
        return
    word = 'включаю' if active else 'выключаю'
    _tg_send(chat_id, f'⏳ {word.capitalize()} {len(sel)} лот(ов) на FunPay…')
    def work():
        done, fail = ([], [])
        for lid in sel:
            ok = _set_lot_active(lid, active)
            with _bindings_lock:
                if lid in _bindings:
                    _bindings[lid]['enabled'] = active
                if lid in _auto_disabled:
                    del _auto_disabled[lid]
            (done if ok else fail).append(lid)
            time.sleep(1.5)
        with _bindings_lock:
            _save_bindings()
        _save_auto_disabled()
        w = 'включены' if active else 'выключены'
        msg = f'✅ {w.capitalize()} на FunPay: {len(done)}'
        if fail:
            msg += f"\n⚠️ не удалось ({len(fail)}): {', '.join(fail)}"
        _tg_send(chat_id, msg)
        _grp_select.pop(chat_id, None)
        _menu_group(chat_id, None, gi)
    threading.Thread(target=work, daemon=True).start()
def _menu_add_country(chat_id, message_id, gi: int, page: int=0) -> None:
    group = _group_by_idx(gi)
    if group is None:
        _menu_bindings(chat_id, message_id)
        return
    src = _grp_first_source(group)
    if not src:
        _tg_edit(chat_id, message_id, 'В группе нет лота-образца.', _make_kb([[('🔙 К группам', 'd4s_bind_list')]]))
        return
    _, sb = src
    try:
        catalog = _get_catalog_cached()
    except Exception as e:
        _tg_edit(chat_id, message_id, f'❌ Каталог: {e}', _make_kb([[('🔙 Назад', f'd4s_bindg:{gi}:0')]]))
        return
    by_id = {int(it['id']): it for it in catalog}
    src_pid = int(sb['product_id'])
    cat = _cat_name(by_id[src_pid]) if src_pid in by_id else None
    if not cat:
        _tg_edit(chat_id, message_id, 'Не удалось определить категорию товара-образца.', _make_kb([[('🔙 Назад', f'd4s_bindg:{gi}:0')]]))
        return
    with _bindings_lock:
        bound = {int(b['product_id']) for b in _bindings.values() if (b.get('group') or '') == group}
    options = [it for it in _visible_catalog(catalog) if _cat_name(it) == cat and int(it['id']) not in bound]
    if not options:
        _tg_edit(chat_id, message_id, f'В категории «{cat}» все товары уже добавлены в группу «{group}».', _make_kb([[('🔙 Назад', f'd4s_bindg:{gi}:0')]]))
        return
    pages = max((len(options) + PAGE_SIZE - 1) // PAGE_SIZE, 1)
    page = max(0, min(page, pages - 1))
    rows = []
    for it in options[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]:
        price = _fmt_rub_kop(int(it.get('price_kop', 0)))
        rows.append([(f"{str(it.get('title'))[:30]} — {price} ({it.get('in_stock', 0)} шт)", f"d4s_gcp:{gi}:{it.get('id')}")])
    nav = []
    if page > 0:
        nav.append(('⬅️', f'd4s_gadd:{gi}:{page - 1}'))
    nav.append((f'{page + 1}/{pages}', 'd4s_noop'))
    if page < pages - 1:
        nav.append(('➡️', f'd4s_gadd:{gi}:{page + 1}'))
    rows.append(nav)
    rows.append([('🔙 Назад', f'd4s_bindg:{gi}:0')])
    text = f'🌍 <b>Добавить страну в «{group}»</b>\nКатегория: {cat}\n\nВыберите страну — плагин создаст лот по образцу первого лота группы, поменяет в его названии страну на выбранную и впишет тег:'
    _tg_edit(chat_id, message_id, text, _make_kb(rows))
def _grp_copy_country(chat_id, gi: int, product_id: int) -> None:
    group = _group_by_idx(gi)
    if group is None:
        return
    src = _grp_first_source(group)
    if not src:
        _tg_send(chat_id, 'В группе нет лота-образца.')
        return
    src_lot, sb = src
    try:
        by_id = {int(it['id']): it for it in _get_catalog_cached()}
    except Exception:
        by_id = {}
    item = by_id.get(int(product_id))
    dst_title = str(item.get('title')) if item else f'товар {product_id}'
    src_item = by_id.get(int(sb['product_id']))
    src_title = str(src_item.get('title')) if src_item else sb.get('product_title') or ''
    qty = int(sb.get('qty', 1))
    _tg_send(chat_id, f'⏳ Создаю лот на FunPay по образцу {src_lot} (меняю страну в названии)…')
    def work():
        new_id, applied, region, err = _copy_lot(src_lot, int(product_id), dst_title, qty, group, src_product_title=src_title)
        if err:
            _tg_send(chat_id, f'❌ Не удалось создать лот: {err}')
            return
        region_line = f'🌍 Регион в лоте выставлен: {region}\n' if region else '⚠️ Регион в форме лота не нашёл — проверьте вручную!\n'
        fpad_line = ''
        if sb.get('fp_auto'):
            ok, n = _sync_fp_stock(new_id, int(product_id))
            if ok:
                with _bindings_lock:
                    if new_id in _bindings:
                        _bindings[new_id]['fp_auto'] = True
                        _save_bindings()
                fpad_line = f'⚡ Мгновенная выдача FunPay включена (в наличии {n}).\n'
        _tg_send(chat_id, f'✅ Создан лот <b>{new_id}</b>:\n<code>{applied}</code>\n{region_line}{fpad_line}привязан к «{dst_title}» в группе «{group}», тег вписан.\n💡 Проверьте/поправьте лот на FunPay:\nhttps://funpay.com/lots/offerEdit?offer={new_id}')
        _menu_group(chat_id, None, gi)
    threading.Thread(target=work, daemon=True).start()
def _menu_binding_detail(chat_id, message_id, lot_id: str) -> None:
    with _bindings_lock:
        b = _bindings.get(lot_id)
    if not b:
        _menu_bindings(chat_id, message_id)
        return
    text = f"🔗 <b>Привязка лота {lot_id}</b>\n\n📦 Товар: {b.get('product_title')} (id {b.get('product_id')})\n📁 Группа: {b.get('group') or NO_GROUP}\n🔢 Кол-во за 1 шт. заказа: {b.get('qty', 1)}\n🏷 Название лота: {b.get('lot_name') or '—'}\nСтатус: {('✅ включена' if b.get('enabled', True) else '⏸ выключена')} (тумблер также включает/выключает лот на FunPay)\n⚡ Мгновенная выдача FunPay: {('✅ вкл' if b.get('fp_auto') else '❌ выкл')}\n\n💡 Ссылка на лот: https://funpay.com/lots/offer?id={lot_id}\n💡 Для лотов-клонов добавьте в описание лота тег <code>d4s:{b.get('product_id')}</code>"
    kb = _make_kb([[('⏸ Выключить' if b.get('enabled', True) else '▶️ Включить', f'd4s_bind_tgl:{lot_id}'), ('🔢 Кол-во', f'd4s_bind_qty:{lot_id}')], [(f"⚡ Мгновенная выдача: {('ВКЛ' if b.get('fp_auto') else 'выкл')}", f'd4s_bind_fpad:{lot_id}')], [('📁 Группа', f'd4s_bind_grp:{lot_id}'), ('🔄 Синхр. лота', f'd4s_bind_sync:{lot_id}')], [('🏷 Название вручную', f'd4s_bind_name:{lot_id}'), ('🗑 Удалить', f'd4s_bind_del:{lot_id}')], [('🔙 К привязкам', 'd4s_bind_list')]])
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _menu_add(chat_id, message_id=None) -> None:
    global _cat_idx
    try:
        visible = _visible_catalog()
    except Exception as e:
        txt = f'❌ Не удалось получить каталог: {e}'
        kb = _make_kb([[('🔙 Меню', 'd4s_main')]])
        _tg_edit(chat_id, message_id, txt, kb) if message_id else _tg_send(chat_id, txt, kb)
        return
    if not visible:
        txt = '❌ Нет доступных товаров: каталог пуст, API-ключ не задан или все категории скрыты (⚙️ Настройки → 🙈 Категории).'
        kb = _make_kb([[('🔙 Меню', 'd4s_main')]])
        _tg_edit(chat_id, message_id, txt, kb) if message_id else _tg_send(chat_id, txt, kb)
        return
    _cat_idx = _ordered_categories(visible)
    if len(_cat_idx) == 1:
        _menu_add_products(chat_id, message_id, 0, 0)
        return
    rows = []
    for ci, cat in enumerate(_cat_idx):
        items = [it for it in visible if _cat_name(it) == cat]
        stock = sum((int(it.get('in_stock', 0)) for it in items))
        rows.append([(f'{cat} ({len(items)} тов., {stock} шт)', f'd4s_addc:{ci}:0')])
    rows.append([('🔙 Меню', 'd4s_main')])
    text = '➕ <b>Новая привязка</b>\nШаг 1/5 — выберите категорию магазина:'
    kb = _make_kb(rows)
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _menu_add_products(chat_id, message_id, ci: int, page: int=0) -> None:
    try:
        visible = _visible_catalog()
    except Exception as e:
        _tg_edit(chat_id, message_id, f'❌ Каталог: {e}', _make_kb([[('🔙 Меню', 'd4s_main')]]))
        return
    if not 0 <= ci < len(_cat_idx):
        _menu_add(chat_id, message_id)
        return
    cat = _cat_idx[ci]
    items = [it for it in visible if _cat_name(it) == cat]
    if not items:
        _menu_add(chat_id, message_id)
        return
    pages = max((len(items) + PAGE_SIZE - 1) // PAGE_SIZE, 1)
    page = max(0, min(page, pages - 1))
    rows = []
    for it in items[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]:
        title = str(it.get('title', '?'))[:30]
        price = _fmt_rub_kop(int(it.get('price_kop', 0)))
        rows.append([(f"{title} — {price} ({it.get('in_stock', 0)} шт)", f"d4s_pick:{it.get('id')}")])
    nav = []
    if page > 0:
        nav.append(('⬅️', f'd4s_addc:{ci}:{page - 1}'))
    nav.append((f'{page + 1}/{pages}', 'd4s_noop'))
    if page < pages - 1:
        nav.append(('➡️', f'd4s_addc:{ci}:{page + 1}'))
    rows.append(nav)
    rows.append([('🔙 Категории', 'd4s_add'), ('🏠 Меню', 'd4s_main')])
    text = f'➕ <b>Новая привязка</b> · {cat}\nШаг 2/5 — выберите товар:'
    kb = _make_kb(rows)
    _tg_edit(chat_id, message_id, text, kb)
def _send_group_picker(chat_id, st: Dict[str, Any]) -> None:
    global _grp_idx
    _grp_idx = _binding_groups()
    rows = [[(f'📁 {g}', f'd4s_grpp:{gi}')] for gi, g in enumerate(_grp_idx)]
    rows.append([('➕ Новая группа', 'd4s_grpn'), (f'⏭ {NO_GROUP}', 'd4s_grps')])
    rows.append([('❌ Отмена', 'd4s_wait_cancel:d4s_bind_list')])
    st['action'] = 'bind_group_wait'
    _waiting[chat_id] = st
    _tg_send(chat_id, 'Шаг 5/5 — выберите <b>группу</b> для привязки (ваша категория: CS2, Dota 2, PUBG, Steam…) или создайте новую:', _make_kb(rows))
def _finalize_binding(chat_id, st: Dict[str, Any], group: str) -> None:
    _waiting.pop(chat_id, None)
    if st.get('mode') == 'regroup':
        lot_id = st['lot_id']
        with _bindings_lock:
            if lot_id in _bindings:
                _bindings[lot_id]['group'] = group
                _save_bindings()
        _tg_send(chat_id, f'✅ Лот {lot_id} → группа «{group or NO_GROUP}»')
        _menu_bindings(chat_id)
        return
    lot_ids = st.get('lot_ids')
    if lot_ids:
        with _bindings_lock:
            for lid in lot_ids:
                _bindings[lid] = {'product_id': st['product_id'], 'product_title': st.get('product_title', ''), 'qty': st.get('qty', 1), 'group': group, 'lot_name': '', 'enabled': True, 'created_at': _now_str()}
            _save_bindings()
        _tg_send(chat_id, f'⏳ Привязываю {len(lot_ids)} лот(ов) в группу «{group or NO_GROUP}», синхронизирую названия и теги с FunPay…')
        def _mass_sync():
            lines = []
            for lid in lot_ids:
                rep = _apply_lot_sync(lid, int(st['product_id']))
                lines.append(f"{('⚠️' if '⚠️' in rep else '✅')} {lid}")
                time.sleep(1.0)
            _tg_send(chat_id, '✅ Массовая привязка готова:\n' + '\n'.join(lines) + '\n⚠️ — синк не прошёл, откройте привязку → «🔄 Синхр. лота».')
            _menu_bindings(chat_id)
        threading.Thread(target=_mass_sync, daemon=True).start()
        return
    lot_id = st['lot_id']
    with _bindings_lock:
        _bindings[lot_id] = {'product_id': st['product_id'], 'product_title': st.get('product_title', ''), 'qty': st.get('qty', 1), 'group': group, 'lot_name': '', 'enabled': True, 'created_at': _now_str()}
        _save_bindings()
    sync_report = _apply_lot_sync(lot_id, int(st['product_id']))
    _tg_send(chat_id, f"✅ Привязка создана: лот {lot_id} → «{st.get('product_title') or st['product_id']}» ×{st.get('qty', 1)} · группа «{group or NO_GROUP}»\n\n{sync_report}")
    _menu_bindings(chat_id)
def _menu_catalog(chat_id, message_id=None, page: int=0) -> None:
    try:
        catalog = _get_catalog_cached()
    except Exception as e:
        catalog = []
        _tg_send(chat_id, f'❌ Ошибка каталога: {e}')
    hidden = _hidden_categories(catalog) if catalog else set()
    shown = [it for it in catalog if _cat_name(it) not in hidden]
    if not shown:
        kb = _make_kb([[('🔙 Настройки лотов', 'd4s_lot_set')]])
        txt = 'Каталог пуст (или все категории скрыты в настройках).'
        _tg_edit(chat_id, message_id, txt, kb) if message_id else _tg_send(chat_id, txt, kb)
        return
    cats = _ordered_categories(shown)
    pages = len(cats)
    page = max(0, min(page, pages - 1))
    cat = cats[page]
    with _bindings_lock:
        bound = {int(b['product_id']) for b in _bindings.values()}
    lines = [f'🛒 <b>{cat}</b> (категория {page + 1}/{pages})\n']
    for it in shown:
        if _cat_name(it) != cat:
            continue
        mark = '🔗' if int(it.get('id', -1)) in bound else '▫️'
        note = '' if _is_text_kind(it) else ' · 📎 файловая выдача — плагином не поддерживается'
        lines.append(f"{mark} id <code>{it.get('id')}</code> · {it.get('title')} — {_fmt_rub_kop(int(it.get('price_kop', 0)))} · {it.get('in_stock', 0)} шт{note}")
    nav = []
    if page > 0:
        nav.append(('⬅️', f'd4s_cat:{page - 1}'))
    nav.append((f'{page + 1}/{pages}', 'd4s_noop'))
    if page < pages - 1:
        nav.append(('➡️', f'd4s_cat:{page + 1}'))
    kb = _make_kb([nav, [('🔙 Настройки лотов', 'd4s_lot_set')]])
    text = '\n'.join(lines)[:4000]
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _menu_hidecats(chat_id, message_id=None) -> None:
    global _allcat_idx
    try:
        catalog = _get_catalog_cached()
    except Exception as e:
        _tg_edit(chat_id, message_id, f'❌ Каталог: {e}', _make_kb([[('🔙 Настройки лотов', 'd4s_lot_set')]]))
        return
    hidden = _hidden_categories(catalog)
    _allcat_idx = _ordered_categories(catalog)
    rows = []
    for ci, cat in enumerate(_allcat_idx):
        mark = '🙈' if cat in hidden else '✅'
        rows.append([(f'{mark} {cat}', f'd4s_cattgl:{ci}')])
    rows.append([('🔙 Настройки лотов', 'd4s_lot_set')])
    text = '🙈 <b>Категории магазина</b>\n\n✅ — видна в привязках и каталоге, 🙈 — скрыта.\nПочты скрыты по умолчанию: их нельзя продавать на FunPay.'
    kb = _make_kb(rows)
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _menu_orders(chat_id, message_id=None) -> None:
    log = load_json(ORDER_LOG_FILE, [])
    with _orders_lock:
        pending = dict(_pending)
    lines = ['📜 <b>Заказы</b>\n']
    if pending:
        lines.append('⏳ <b>В обработке:</b>')
        for oid, od in list(pending.items())[:10]:
            step = {'processing': 'закупка', 'delivering': 'выдача', 'failed': '❌ ошибка', 'manual_check': '⚠️ проверка'}.get(od.get('step'), od.get('step'))
            lines.append(f"• #{oid} {od.get('product_title')} ×{od.get('qty')} — {step}")
            if od.get('error'):
                lines.append(f"   <i>{str(od['error'])[:80]}</i>")
        lines.append('')
    if log:
        lines.append('🗂 <b>Последние 10:</b>')
        icons = {'COMPLETED': '✅', 'FAILED_REFUNDED': '↩️', 'DELIVERY_FAILED': '🛑'}
        for e in list(reversed(log))[:10]:
            ic = icons.get(e.get('status'), '❌')
            lines.append(f"{ic} #{e.get('order_id')} {e.get('product_title')} ×{e.get('qty')} · {e.get('ts_str', '')[5:16]}")
    else:
        lines.append('Заказов пока не было.')
    kb = _make_kb([[('🔙 Настройки лотов', 'd4s_lot_set')]])
    text = '\n'.join(lines)[:4000]
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _menu_stats(chat_id, message_id=None) -> None:
    stats = _load_stats()
    profit = stats['total_revenue_rub'] - stats['total_cost_rub']
    lines = [f'📊 <b>Статистика</b>\n', f"✅ Заказов выдано: {stats['total_orders']}", f"❌ Ошибок: {stats['total_failed']}", f"📦 Единиц товара: {stats['total_qty']}", f"💵 Выручка (₽-заказы): {stats['total_revenue_rub']:.2f} ₽", f"💸 Закупка: {stats['total_cost_rub']:.2f} ₽", f'📈 Прибыль: {profit:.2f} ₽']
    if stats.get('items'):
        lines.append('\n<b>По товарам:</b>')
        top = sorted(stats['items'].values(), key=lambda x: -x.get('qty', 0))[:10]
        for it in top:
            lines.append(f"• {it['title']}: {it['orders']} зак. / {it['qty']} шт")
    if stats.get('last_order_at'):
        lines.append(f"\n🕐 Последний заказ: {stats['last_order_at']}")
    kb = _make_kb([[('🔙 Меню', 'd4s_main')]])
    text = '\n'.join(lines)
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _menu_health(chat_id, message_id=None) -> None:
    lines = ['🩺 <b>Проверка API</b>\n']
    client = _get_client()
    if client is None:
        lines.append('❌ API-ключ не задан.')
    else:
        t0 = time.time()
        try:
            pong = client.ping()
            lines.append(f"✅ Ping: ok (v{pong.get('version', '?')}, {(time.time() - t0) * 1000:.0f} мс)")
        except Exception as e:
            lines.append(f'❌ Ping: {str(e)[:100]}')
        try:
            bal = _refresh_balance()
            lines.append(f'✅ Баланс: {_fmt_rub_kop(bal)}')
        except Exception as e:
            lines.append(f'❌ Баланс: {str(e)[:100]}')
        try:
            catalog = _get_catalog_cached(max_age=0)
            lines.append(f'✅ Каталог: {len(catalog)} товаров')
            bindings = _enabled_bindings()
            if bindings:
                by_id = {int(it['id']): it for it in catalog}
                for lot_id, b in bindings.items():
                    pid = int(b['product_id'])
                    it = by_id.get(pid)
                    if it is None:
                        lines.append(f'⚠️ Лот {lot_id}: товар id {pid} не найден в каталоге!')
                    elif int(it.get('in_stock', 0)) <= 0:
                        lines.append(f"⚠️ Лот {lot_id}: «{it.get('title')}» — нет в наличии")
        except Exception as e:
            lines.append(f'❌ Каталог: {str(e)[:100]}')
    kb = _make_kb([[('🔙 Аккаунт', 'd4s_account'), ('🏠 Настройки', 'd4s_main')]])
    text = '\n'.join(lines)
    _tg_edit(chat_id, message_id, text, kb) if message_id else _tg_send(chat_id, text, kb)
def _cb_router(call) -> None:
    data = getattr(call, 'data', '') or ''
    chat_id = getattr(getattr(getattr(call, 'message', None), 'chat', None), 'id', None)
    message_id = getattr(getattr(call, 'message', None), 'message_id', None)
    user_id = getattr(getattr(call, 'from_user', None), 'id', None)
    if chat_id is None:
        return
    if not _is_authorized(user_id):
        return
    def ack(text_=None):
        try:
            bot.answer_callback_query(call.id, text_)
        except Exception:
            pass
    parts = data.split(':')
    action, args_ = (parts[0], parts[1:])
    def iarg(i, default=0):
        try:
            return int(args_[i])
        except Exception:
            return default
    arg = args_[0] if args_ else ''
    if action == 'd4s_noop':
        ack()
    elif action == 'd4s_home':
        ack()
        _plugin_home(chat_id, message_id)
    elif action == 'd4s_info':
        ack()
        _plugin_info(chat_id, message_id)
    elif action == 'd4s_update':
        ack()
        _plugin_update_menu(chat_id, message_id)
    elif action in ('d4s_update_online', 'd4s_update_run'):
        ack('Проверяю обновление…')
        _start_online_update(chat_id, message_id)
    elif action == 'd4s_update_local':
        ack()
        _start_local_update(chat_id, message_id)
    elif action == 'd4s_delete_ask':
        ack()
        _plugin_delete_confirm(chat_id, message_id)
    elif action == 'd4s_delete_yes':
        ack('Удаляю…')
        _delete_plugin_from_disk(chat_id, message_id)
    elif action == 'd4s_delete_no':
        ack()
        _plugin_home(chat_id, message_id)
    elif action == 'd4s_wait_cancel':
        ack('Отменено')
        st = _waiting.get(chat_id) or {}
        target = ':'.join(args_) or _wait_target(st)[1]
        _waiting.pop(chat_id, None)
        _show_wait_target(chat_id, message_id, target)
    elif action == 'd4s_main':
        ack()
        _menu_main(chat_id, message_id, live_balance=False)
    elif action == 'd4s_account':
        ack()
        _menu_account(chat_id, message_id)
    elif action == 'd4s_key_delete_ask':
        ack()
        _menu_api_delete_confirm(chat_id, message_id)
    elif action == 'd4s_key_delete_yes':
        _clear_api_key()
        ack('API-ключ удалён')
        _menu_account(chat_id, message_id)
    elif action == 'd4s_key_delete_no':
        ack()
        _menu_account(chat_id, message_id)
    elif action == 'd4s_plugin_set':
        ack()
        _menu_plugin_settings(chat_id, message_id)
    elif action == 'd4s_plugin_state':
        ack()
        _menu_plugin_state(chat_id, message_id)
    elif action == 'd4s_order_set':
        ack()
        _menu_order_settings(chat_id, message_id)
    elif action == 'd4s_notifications':
        ack()
        _menu_notifications(chat_id, message_id)
    elif action == 'd4s_safety':
        ack()
        _menu_safety(chat_id, message_id)
    elif action == 'd4s_maintenance':
        ack()
        _menu_maintenance(chat_id, message_id)
    elif action == 'd4s_logs':
        ack()
        _menu_logs(chat_id, message_id)
    elif action == 'd4s_logs_download':
        ack('Отправляю…')
        if not _send_document(chat_id, LOG_FILE, '📄 Лог Dim4n4ik Shop'):
            _tg_send(chat_id, '⚠️ Лог пока пуст или файл недоступен.')
    elif action == 'd4s_logs_clear_ask':
        ack()
        _menu_log_clear_confirm(chat_id, message_id)
    elif action == 'd4s_logs_clear_yes':
        ack('Очищено')
        try:
            cleared = False
            for handler in list(logger.handlers):
                if isinstance(handler, logging.FileHandler) and getattr(handler, 'baseFilename', '') == str(Path(LOG_FILE).resolve()) and getattr(handler, 'stream', None):
                    handler.acquire()
                    try:
                        handler.stream.seek(0)
                        handler.stream.truncate(0)
                        handler.stream.flush()
                        cleared = True
                    finally:
                        handler.release()
            if not cleared:
                Path(LOG_FILE).write_text('', encoding='utf-8')
        except Exception as e:
            _tg_send(chat_id, f'❌ Не удалось очистить лог: {e}')
        _menu_logs(chat_id, message_id)
    elif action == 'd4s_config':
        ack()
        _menu_config(chat_id, message_id)
    elif action == 'd4s_backup_create':
        ack('Создаю…')
        try:
            path = _create_config_backup('manual')
            _tg_send(chat_id, f'✅ Резервная копия создана: <code>{Path(path).name}</code>')
        except Exception as e:
            _tg_send(chat_id, f'❌ Резервная копия не создана: {str(e)[:200]}')
        _menu_config(chat_id, message_id)
    elif action == 'd4s_backup_export':
        ack('Готовлю архив…')
        try:
            path = _create_config_backup('export')
            if not _send_document(chat_id, path, '💾 Резервная копия Dim4n4ik Shop'):
                raise RuntimeError('Telegram не принял файл')
        except Exception as e:
            _tg_send(chat_id, f'❌ Экспорт не выполнен: {str(e)[:200]}')
    elif action == 'd4s_backup_import':
        _waiting[chat_id] = {'action': 'config_import', 'prompt_id': message_id}
        ack()
        _tg_send(chat_id, '📥 Пришлите ZIP-архив резервной копии Dim4n4ik Shop. Перед заменой данных будет автоматически создана копия текущего состояния.', _wait_kb(_waiting[chat_id]))
    elif action == 'd4s_storage_check':
        ack('Проверяю…')
        result = _check_restore_storage()
        if result.get('ok'):
            restored = result.get('restored') or []
            text_ = '✅ Все основные JSON-файлы исправны.' if not restored else '✅ Восстановлены файлы: ' + ', '.join(restored)
        else:
            text_ = '⚠️ Не удалось полностью восстановить: ' + ', '.join(result.get('invalid') or []) + '. ' + str(result.get('error') or '')
        if result.get('restored'):
            _stop_event.set()
            text_ += ' Выполните /restart перед дальнейшей работой плагина.'
        _tg_send(chat_id, text_)
        _menu_config(chat_id, message_id)
    elif action == 'd4s_databases':
        ack()
        _menu_databases(chat_id, message_id)
    elif action == 'd4s_db_create':
        _waiting[chat_id] = {'action': 'db_create_name'}
        ack()
        _tg_send(chat_id, '➕ <b>Новая база аккаунтов</b>\n\nОтправьте название базы, например <code>Steam Argentina</code>.', _wait_kb(_waiting[chat_id]))
    elif action == 'd4s_dbprodp':
        st = _waiting.get(chat_id) or {}
        if st.get('action') != 'db_create_product':
            ack('Создание базы уже завершено')
            _menu_databases(chat_id, message_id)
        else:
            ack()
            _menu_database_product_select(chat_id, message_id, iarg(0, 0))
    elif action == 'd4s_dbprod':
        st = _waiting.get(chat_id) or {}
        if st.get('action') != 'db_create_product':
            ack('Сначала задайте название базы')
            return
        pid = iarg(0, 0)
        item = next((x for x in _get_catalog_cached() if int(x.get('id', -1)) == pid and _is_text_kind(x)), None)
        if not item:
            ack('Товар не найден')
            return
        try:
            db = _create_database(str(st.get('name') or ''), pid, str(item.get('title') or f'товар {pid}'))
            _waiting.pop(chat_id, None)
            ack('База создана')
            _menu_database_detail(chat_id, message_id, db['id'])
        except Exception as e:
            ack(str(e)[:100])
    elif action == 'd4s_db':
        ack()
        _menu_database_detail(chat_id, message_id, arg)
    elif action == 'd4s_db_view':
        database_id = args_[0] if args_ else ''
        section = args_[1] if len(args_) > 1 else 'available'
        page = iarg(2, 0)
        ack()
        _menu_database_items(chat_id, message_id, database_id, section, page)
    elif action == 'd4s_db_export':
        ack('Отправляю…')
        if not _send_database_export(chat_id, arg):
            _tg_send(chat_id, '⚠️ В базе нет доступных аккаунтов для экспорта.')
    elif action == 'd4s_db_replenish':
        db = _database_by_id(arg)
        if not db:
            ack('База не найдена')
            return
        if _is_mail_database(db):
            ack('Почты добавляются только текстом или файлом')
            return
        _waiting[chat_id] = {'action': 'db_replenish_qty', 'database_id': arg}
        ack()
        _tg_send(chat_id, f'🛒 Сколько аккаунтов купить через dim4n4ik.shop и добавить в базу? От 1 до {API_QTY_MAX}.', _wait_kb(_waiting[chat_id]))
    elif action == 'd4s_db_import_text':
        if not _database_by_id(arg):
            ack('База не найдена')
            return
        _waiting[chat_id] = {'action': 'db_import_text', 'database_id': arg}
        ack()
        _tg_send(chat_id, '📝 <b>Добавление аккаунтов текстом</b>\n\nОтправьте аккаунты одним сообщением. Каждый непустой ряд будет добавлен как отдельная позиция. Дубликаты будут пропущены.', _wait_kb(_waiting[chat_id]))
    elif action == 'd4s_db_import_file':
        if not _database_by_id(arg):
            ack('База не найдена')
            return
        _waiting[chat_id] = {'action': 'db_import_file', 'database_id': arg}
        ack()
        _tg_send(chat_id, '📎 <b>Загрузка аккаунтов файлом</b>\n\nПришлите файл <code>.txt</code> или <code>.csv</code>. Каждый непустой ряд будет добавлен как отдельная позиция. Дубликаты будут пропущены.', _wait_kb(_waiting[chat_id]))
    elif action == 'd4s_db_rename':
        db = _database_by_id(arg)
        if not db:
            ack('База не найдена')
            return
        _waiting[chat_id] = {'action': 'db_rename', 'database_id': arg}
        ack()
        _tg_send(chat_id, f"✏️ Отправьте новое название для базы <b>{db['name']}</b>.", _wait_kb(_waiting[chat_id]))
    elif action == 'd4s_db_delete_ask':
        ack()
        _menu_database_delete_confirm(chat_id, message_id, arg)
    elif action == 'd4s_db_delete_yes':
        try:
            ok = _delete_database(arg)
            ack('База удалена' if ok else 'База не найдена')
            _menu_databases(chat_id, message_id)
        except Exception as e:
            ack(str(e)[:120])
            _menu_database_detail(chat_id, message_id, arg)
    elif action == 'd4s_messages':
        ack()
        _menu_buyer_messages(chat_id, message_id)
    elif action == 'd4s_messages_reset':
        cfg_set('buyer_messages', dict(DEFAULT_BUYER_MESSAGES))
        ack('Сообщения сброшены')
        _menu_buyer_messages(chat_id, message_id)
    elif action == 'd4s_msg_edit':
        if arg not in BUYER_MESSAGE_LABELS:
            ack('Неизвестный шаблон')
            return
        st = {'action': 'edit_buyer_message', 'key': arg}
        _waiting[chat_id] = st
        current = _buyer_messages().get(arg, '')
        safe = current.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        ack()
        _tg_send(chat_id, f'✏️ <b>{BUYER_MESSAGE_LABELS[arg]}</b>\n\nТекущий текст:\n<code>{safe}</code>\n\nОтправьте новый текст сообщения.', _wait_kb(st))
    elif action == 'd4s_lot_set':
        ack()
        _menu_lot_settings(chat_id, message_id)
    elif action == 'd4s_lots':
        ack()
        _menu_lot_settings(chat_id, message_id, iarg(0, 0))
    elif action == 'd4s_lot_discover':
        ack('Ищу лоты…')
        try:
            report = _discover_funpay_lots()
            counts = report.get('category_counts', {})
            _tg_send(chat_id, f"✅ Категория 89: {int(counts.get(89, 0) or 0)} лотов. Категория 1350: {int(counts.get(1350, 0) or 0)} лотов. Категория 938: {int(counts.get(938, 0) or 0)} лотов. Всего уникальных: {report['found']}. Ошибок чтения: {report['errors']}.")
        except Exception as e:
            _tg_send(chat_id, f'❌ Не удалось найти лоты: {str(e)[:180]}')
        _menu_lot_settings(chat_id, message_id)
    elif action == 'd4s_lot_manual':
        _waiting[chat_id] = {'action': 'lot_manual_id'}
        ack()
        _tg_send(chat_id, '➕ Отправьте числовой LOT ID FunPay или ссылку на лот.', _wait_kb(_waiting[chat_id]))
    elif action == 'd4s_lot_type_steam':
        st = _waiting.get(chat_id) or {}
        if st.get('action') != 'lot_manual_type' or str(st.get('lot_id') or '') != str(arg):
            ack('Сессия добавления истекла')
            return
        _waiting.pop(chat_id, None)
        ack()
        _menu_lot_mode_pick(chat_id, message_id, arg)
    elif action == 'd4s_lot_type_mail':
        st = _waiting.get(chat_id) or {}
        if st.get('action') != 'lot_manual_type' or str(st.get('lot_id') or '') != str(arg):
            ack('Сессия добавления истекла')
            return
        try:
            db, binding = _configure_mail_lot(arg)
            _waiting.pop(chat_id, None)
            ack('База почт создана')
            _menu_database_detail(chat_id, message_id, str(db['id']))
        except Exception as e:
            ack(str(e)[:110])
    elif action == 'd4s_lot_pick':
        ack()
        _menu_lot_detail(chat_id, message_id, arg)
    elif action == 'd4s_lot_toggle':
        try:
            lot = _validate_funpay_lot(arg)
            new_state = not bool(lot.get('active', True))
            ok = _set_lot_active(arg, new_state)
            if not ok:
                raise RuntimeError('FunPay не сохранил состояние')
            lot['active'] = new_state
            _cache_funpay_lot(lot)
            with _bindings_lock:
                if arg in _bindings:
                    _bindings[arg]['enabled'] = new_state
                    _save_bindings()
            _auto_disabled.pop(arg, None)
            _save_auto_disabled()
            ack('Готово')
        except Exception as e:
            ack(str(e)[:100])
        _menu_lot_detail(chat_id, message_id, arg)
    elif action == 'd4s_lot_mode_menu':
        ack()
        _menu_lot_mode_pick(chat_id, message_id, arg)
    elif action == 'd4s_lot_mode_api':
        ack()
        _menu_lot_api_products(chat_id, message_id, arg, 0)
    elif action == 'd4s_lot_apipp':
        lot_id = args_[0] if args_ else ''
        page = iarg(1, 0)
        ack()
        _menu_lot_api_products(chat_id, message_id, lot_id, page)
    elif action == 'd4s_lot_apip':
        lot_id = args_[0] if args_ else ''
        pid = iarg(1, 0)
        try:
            binding = _configure_lot_api(lot_id, pid)
            ack('Режим сохранён')
            if _binding_stock_target(binding) > 0:
                threading.Thread(target=_sync_binding_stock, args=(lot_id, binding), daemon=True).start()
        except Exception as e:
            ack(str(e)[:110])
        _menu_lot_detail(chat_id, message_id, lot_id)
    elif action == 'd4s_lot_mode_db':
        ack()
        _menu_lot_database_pick(chat_id, message_id, arg)
    elif action == 'd4s_lot_database':
        ack()
        _menu_lot_database_pick(chat_id, message_id, arg)
    elif action == 'd4s_lot_dbp':
        lot_id = args_[0] if args_ else ''
        database_id = args_[1] if len(args_) > 1 else ''
        try:
            binding = _configure_lot_database(lot_id, database_id)
            ack('Режим сохранён')
            threading.Thread(target=_sync_binding_stock, args=(lot_id, binding), daemon=True).start()
        except Exception as e:
            ack(str(e)[:110])
        _menu_lot_detail(chat_id, message_id, lot_id)
    elif action == 'd4s_lot_qty':
        if arg not in _bindings:
            ack('Сначала выберите режим выдачи')
            return
        _waiting[chat_id] = {'action': 'lot_set_qty', 'lot_id': arg}
        ack()
        _tg_send(chat_id, f'🔢 Сколько аккаунтов выдавать за 1 единицу заказа? Введите целое число от 1 до {FUNPAY_ORDER_QTY_MAX}.', _wait_kb(_waiting[chat_id]))
    elif action == 'd4s_lot_stock':
        if arg not in _bindings:
            ack('Сначала выберите режим выдачи')
            return
        _waiting[chat_id] = {'action': 'lot_set_stock', 'lot_id': arg}
        ack()
        _tg_send(chat_id, '⚡ Сколько позиций максимум держать в автовыдаче FunPay? Введите 0–500. 0 отключает заглушки автовыдачи.', _wait_kb(_waiting[chat_id]))
    elif action == 'd4s_lot_delete_menu':
        ack()
        _menu_lot_delete_options(chat_id, message_id, arg)
    elif action == 'd4s_lot_unbind_ask':
        ack()
        _menu_lot_unbind_confirm(chat_id, message_id, arg)
    elif action == 'd4s_lot_unbind_yes':
        _remove_lot_from_plugin(arg)
        threading.Thread(target=_disable_fp_autodelivery, args=(arg,), daemon=True).start()
        ack('Лот удалён из плагина')
        _menu_lot_settings(chat_id, message_id)
    elif action == 'd4s_lot_delete_ask':
        ack()
        _menu_lot_delete_confirm(chat_id, message_id, arg)
    elif action == 'd4s_lot_delete_yes':
        ack('Удаляю…')
        ok = _delete_lot_fp(arg)
        if ok:
            with _bindings_lock:
                _bindings.pop(arg, None)
                _save_bindings()
            _auto_disabled.pop(arg, None)
            _save_auto_disabled()
            rows = [x for x in _cached_funpay_lots() if str(x.get('lot_id')) != str(arg)]
            _save_funpay_lot_cache(rows)
            _tg_send(chat_id, f'✅ Лот {arg} удалён с FunPay и из плагина.')
            _menu_lot_settings(chat_id, message_id)
        else:
            _tg_send(chat_id, f'⚠️ FunPay не подтвердил удаление лота {arg}. Настройка плагина сохранена.')
            _menu_lot_detail(chat_id, message_id, arg)
    elif action == 'd4s_set':
        ack()
        _menu_plugin_settings(chat_id, message_id)
    elif action == 'd4s_ptgl':
        if arg == 'plugin_enabled':
            cfg_set(arg, not cfg_get(arg))
        ack()
        _menu_plugin_state(chat_id, message_id)
    elif action == 'd4s_otgl':
        if arg in ('auto_refund_enabled', 'auto_lots_by_stock'):
            cfg_set(arg, not cfg_get(arg))
        ack()
        _menu_order_settings(chat_id, message_id)
    elif action == 'd4s_ntgl':
        if arg in ('notifications_enabled', 'notify_new_order', 'notify_success', 'notify_failure', 'notify_errors', 'notify_low_balance', 'notify_out_of_stock'):
            cfg_set(arg, not cfg_get(arg))
        ack()
        _menu_notifications(chat_id, message_id)
    elif action == 'd4s_stgl':
        if arg == 'loss_protection':
            cfg_set(arg, not cfg_get(arg))
        ack()
        _menu_safety(chat_id, message_id)
    elif action == 'd4s_tgl':
        if arg in DEFAULT_CONFIG:
            cfg_set(arg, not cfg_get(arg))
        ack()
        if arg == 'auto_lots_by_stock':
            _menu_lot_settings(chat_id, message_id)
        else:
            _menu_plugin_settings(chat_id, message_id)
    elif action == 'd4s_hidecats':
        ack()
        _menu_hidecats(chat_id, message_id)
    elif action == 'd4s_cattgl':
        ci = iarg(0, -1)
        if 0 <= ci < len(_allcat_idx):
            cat = _allcat_idx[ci]
            try:
                hidden = set(_hidden_categories(_get_catalog_cached()))
            except Exception:
                hidden = set(cfg_get('hidden_categories') or [])
            if cat in hidden:
                hidden.discard(cat)
            else:
                hidden.add(cat)
            cfg_set('hidden_categories', sorted(hidden))
        ack()
        _menu_hidecats(chat_id, message_id)
    elif action == 'd4s_set_key':
        _waiting[chat_id] = {'action': 'set_key'}
        ack()
        _tg_send(chat_id, f'🔑 Отправьте API-ключ (<code>rk_live_...</code>).\nВзять: <a href="{SHOP_BOT_URL}">Steam-бот dim4n4ik</a> → Профиль → «🔑 API».', _wait_kb(_waiting[chat_id]))
    elif action == 'd4s_set_lowbal':
        _waiting[chat_id] = {'action': 'set_lowbal'}
        ack()
        _tg_send(chat_id, '💰 Отправьте порог низкого баланса в рублях (например, 200).', _wait_kb(_waiting[chat_id]))
    elif action == 'd4s_set_balint':
        _waiting[chat_id] = {'action': 'set_balance_interval'}
        ack()
        _tg_send(chat_id, '⏱ Отправьте интервал проверки баланса в минутах (минимум 1).', _wait_kb(_waiting[chat_id]))
    elif action == 'd4s_set_margin':
        _waiting[chat_id] = {'action': 'set_margin'}
        ack()
        _tg_send(chat_id, '📉 Минимальная маржа сверх закупки, % (0 = просто не ниже закупки; поднимите, чтобы покрыть комиссию FunPay, например 20).', _wait_kb(_waiting[chat_id]))
    elif action == 'd4s_set_fpbuf':
        _waiting[chat_id] = {'action': 'set_fpbuf'}
        ack()
        _tg_send(chat_id, '⚡ Сколько заглушек держать на FunPay «в наличии» (буфер, например 25)?\nМеньше буфер → меньше переобещаний при общем складе, но чаще «нет в наличии».', _wait_kb(_waiting[chat_id]))
    elif action == 'd4s_set_fpsync':
        _waiting[chat_id] = {'action': 'set_fpsync'}
        ack()
        _tg_send(chat_id, '⏱ Как часто синкать буфер со складом API, в секундах (мин 30, например 120)?\nЧаще → точнее остаток, но больше запросов к FunPay.', _wait_kb(_waiting[chat_id]))
    elif action == 'd4s_bind_list':
        ack()
        _menu_bindings(chat_id, message_id)
    elif action == 'd4s_bindg':
        ack()
        _menu_group(chat_id, message_id, iarg(0, -2), iarg(1, 0))
    elif action == 'd4s_gsel':
        gi = iarg(0, -2)
        _grp_select[chat_id] = {'gi': gi, 'sel': set()}
        ack('Отметьте лоты')
        _menu_group(chat_id, message_id, gi, iarg(1, 0))
    elif action == 'd4s_gselx':
        _grp_select.pop(chat_id, None)
        ack('Готово')
        _menu_group(chat_id, message_id, iarg(0, -2), iarg(1, 0))
    elif action == 'd4s_gtog':
        gi = iarg(0, -2)
        page = iarg(1, 0)
        lot_id = args_[2] if len(args_) > 2 else ''
        st = _grp_select.get(chat_id)
        if st and st.get('gi') == gi and lot_id:
            sel = st['sel']
            sel.discard(lot_id) if lot_id in sel else sel.add(lot_id)
        ack()
        _menu_group(chat_id, message_id, gi, page)
    elif action == 'd4s_gon':
        ack('Включаю…')
        _grp_batch_active(chat_id, iarg(0, -2), True)
    elif action == 'd4s_goff':
        ack('Выключаю…')
        _grp_batch_active(chat_id, iarg(0, -2), False)
    elif action == 'd4s_gdel':
        gi = iarg(0, -2)
        st = _grp_select.get(chat_id)
        n = len(st.get('sel') or []) if st and st.get('gi') == gi else 0
        if not n:
            ack('Ничего не выбрано')
            return
        ack()
        kb = _make_kb([[('🗑 Только привязки', f'd4s_gdel2:{gi}')], [('🔥 Лоты на FunPay + привязки', f'd4s_gdelf:{gi}')], [('🔙 Отмена', f'd4s_bindg:{gi}:0')]])
        _tg_edit(chat_id, message_id, f'Удалить {n} выбранных?\n🗑 <b>только привязки</b> — снимется автозакупка, лоты на FunPay останутся.\n🔥 <b>лоты + привязки</b> — лоты удалятся с FunPay <b>безвозвратно</b>.', kb)
    elif action == 'd4s_gdel2':
        gi = iarg(0, -2)
        st = _grp_select.get(chat_id)
        sel = list(st.get('sel') or []) if st and st.get('gi') == gi else []
        with _bindings_lock:
            for lid in sel:
                _bindings.pop(lid, None)
            _save_bindings()
        _grp_select.pop(chat_id, None)
        ack(f'Удалено: {len(sel)}')
        _menu_bindings(chat_id, message_id)
    elif action == 'd4s_gdelf':
        gi = iarg(0, -2)
        st = _grp_select.get(chat_id)
        sel = list(st.get('sel') or []) if st and st.get('gi') == gi else []
        if not sel:
            ack('Ничего не выбрано')
            return
        _grp_select.pop(chat_id, None)
        ack('Удаляю лоты…')
        _tg_send(chat_id, f'⏳ Удаляю {len(sel)} лот(ов) с FunPay…')
        def _work_gdelf():
            ok, fail = ([], [])
            for lid in sel:
                (ok if _delete_lot_fp(lid) else fail).append(lid)
                with _bindings_lock:
                    _bindings.pop(lid, None)
                _auto_disabled.pop(lid, None)
                time.sleep(1.5)
            with _bindings_lock:
                _save_bindings()
            _save_auto_disabled()
            msg = f'🔥 Удалено с FunPay: {len(ok)}'
            if fail:
                msg += f"\n⚠️ не удалось ({len(fail)}): {', '.join(fail)} — привязки убраны, лоты удалите на FunPay вручную"
            _tg_send(chat_id, msg)
            _menu_bindings(chat_id)
        threading.Thread(target=_work_gdelf, daemon=True).start()
    elif action == 'd4s_gadd':
        ack()
        _menu_add_country(chat_id, message_id, iarg(0, -2), iarg(1, 0))
    elif action == 'd4s_gcp':
        pid = iarg(1, 0)
        if not pid:
            ack('Ошибка')
            return
        ack('Создаю лот…')
        _grp_copy_country(chat_id, iarg(0, -2), pid)
    elif action == 'd4s_grpren':
        group = _group_by_idx(iarg(0, -2))
        if not group:
            ack('Группа не найдена')
            return
        _waiting[chat_id] = {'action': 'grp_rename', 'old': group}
        ack()
        _tg_send(chat_id, f'✏️ Отправьте новое имя для группы «{group}».', _wait_kb(_waiting[chat_id]))
    elif action == 'd4s_bind':
        ack()
        _menu_binding_detail(chat_id, message_id, arg)
    elif action == 'd4s_bind_tgl':
        with _bindings_lock:
            b = _bindings.get(arg)
            if not b:
                ack('Привязка не найдена')
                return
            new_state = not b.get('enabled', True)
            b['enabled'] = new_state
            _save_bindings()
            if arg in _auto_disabled:
                del _auto_disabled[arg]
                _save_auto_disabled()
        ack('Готово')
        _menu_binding_detail(chat_id, message_id, arg)
        def _toggle_fp_lot():
            ok = _set_lot_active(arg, new_state)
            word = 'включён' if new_state else 'выключен'
            if ok:
                _tg_send(chat_id, f'✅ Лот {arg} на FunPay {word}.')
            else:
                _tg_send(chat_id, f"⚠️ Лот {arg} на FunPay не удалось {('включить' if new_state else 'выключить')} (проверьте вручную).")
        threading.Thread(target=_toggle_fp_lot, daemon=True).start()
    elif action == 'd4s_bind_qty':
        _waiting[chat_id] = {'action': 'bind_setqty', 'lot_id': arg}
        ack()
        _tg_send(chat_id, f'🔢 Сколько единиц товара выдавать за 1 шт. заказа лота {arg}? (обычно 1)', _wait_kb(_waiting[chat_id]))
    elif action == 'd4s_bind_grp':
        with _bindings_lock:
            exists = arg in _bindings
        if not exists:
            ack('Привязка не найдена')
            return
        ack()
        _send_group_picker(chat_id, {'mode': 'regroup', 'lot_id': arg})
    elif action == 'd4s_bind_sync':
        with _bindings_lock:
            b = _bindings.get(arg)
        if not b:
            ack('Привязка не найдена')
            return
        ack('Читаю лот с FunPay...')
        report = _apply_lot_sync(arg, int(b['product_id']))
        _tg_send(chat_id, f'🔄 Лот {arg}:\n{report}')
        _menu_binding_detail(chat_id, message_id, arg)
    elif action == 'd4s_bind_fpad':
        with _bindings_lock:
            b = _bindings.get(arg)
        if not b:
            ack('Привязка не найдена')
            return
        new_val = not b.get('fp_auto')
        ack('Включаю…' if new_val else 'Выключаю…')
        lot_id = arg
        pid = int(b['product_id'])
        _tg_send(chat_id, '⚡ Включаю мгновенную выдачу FunPay на лоте ' + lot_id + ' (галочка + заглушка вместо кредов)…' if new_val else f'🔌 Выключаю мгновенную выдачу FunPay на лоте {lot_id}…')
        def _work_fpad():
            if new_val:
                ok, n = _sync_fp_stock(lot_id, pid)
            else:
                ok, n = (_disable_fp_autodelivery(lot_id), 0)
            if ok:
                with _bindings_lock:
                    if lot_id in _bindings:
                        _bindings[lot_id]['fp_auto'] = new_val
                        _save_bindings()
                if new_val:
                    _tg_send(chat_id, f"✅ Лот {lot_id}: мгновенная выдача FunPay ВКЛ.\n📦 В наличии на FunPay: {n} (буфер {_fp_buffer()}, но не выше склада).\nFunPay сразу пришлёт покупателю заглушку, реальный аккаунт выдаст плагин. Буфер пополняется после продажи и синкается со складом каждые {int(cfg_get('fp_auto_sync_sec') or 120)} c.")
                else:
                    _tg_send(chat_id, f'🔌 Лот {lot_id}: мгновенная выдача FunPay ВЫКЛ (галочка снята, заглушки убраны).')
            else:
                _tg_send(chat_id, f'❌ Лот {lot_id}: не удалось изменить автовыдачу на FunPay.')
            _menu_binding_detail(chat_id, None, lot_id)
        threading.Thread(target=_work_fpad, daemon=True).start()
    elif action == 'd4s_bind_name':
        _waiting[chat_id] = {'action': 'bind_setname', 'lot_id': arg}
        ack()
        _tg_send(chat_id, '🏷 Отправьте ТОЧНОЕ название лота на FunPay (для резервного определения заказа, если Cardinal не передаст lot_id).', _wait_kb(_waiting[chat_id]))
    elif action == 'd4s_bind_del':
        ack()
        kb = _make_kb([[('🗑 Только привязку', f'd4s_bind_del2:{arg}')], [('🔥 Лот на FunPay + привязку', f'd4s_bind_delf:{arg}')], [('🔙 Отмена', f'd4s_bind:{arg}')]])
        _tg_edit(chat_id, message_id, f'Что удалить для лота {arg}?\n🗑 <b>привязку</b> — плагин перестанет закупать, лот на FunPay останется.\n🔥 <b>лот</b> — удалит лот с FunPay <b>безвозвратно</b> + привязку.', kb)
    elif action == 'd4s_bind_del2':
        with _bindings_lock:
            _bindings.pop(arg, None)
            _save_bindings()
        _auto_disabled.pop(arg, None)
        _save_auto_disabled()
        ack('Привязка удалена')
        _menu_bindings(chat_id, message_id)
    elif action == 'd4s_bind_delf':
        lot_id = arg
        ack('Удаляю лот с FunPay…')
        def _work_delf():
            ok = _delete_lot_fp(lot_id)
            with _bindings_lock:
                _bindings.pop(lot_id, None)
                _save_bindings()
            _auto_disabled.pop(lot_id, None)
            _save_auto_disabled()
            if ok:
                _tg_send(chat_id, f'🔥 Лот {lot_id} удалён с FunPay, привязка убрана.')
            else:
                _tg_send(chat_id, f'⚠️ Лот {lot_id} не удалось удалить с FunPay (удалите вручную). Привязка убрана.')
            _menu_bindings(chat_id)
        threading.Thread(target=_work_delf, daemon=True).start()
    elif action == 'd4s_add':
        ack()
        _menu_add(chat_id, message_id)
    elif action == 'd4s_addc':
        ack()
        _menu_add_products(chat_id, message_id, iarg(0, -1), iarg(1, 0))
    elif action == 'd4s_pick':
        try:
            pid = int(arg)
        except Exception:
            ack('Ошибка')
            return
        title = ''
        for it in _catalog_cache.get('items', []):
            if int(it.get('id', -1)) == pid:
                if not _is_text_kind(it):
                    ack('Только текстовые товары')
                    return
                title = str(it.get('title', ''))
                break
        _waiting[chat_id] = {'action': 'bind_lot', 'product_id': pid, 'product_title': title}
        ack()
        _tg_send(chat_id, f'➕ Товар: <b>{title or pid}</b>\n\nШаг 3/5 — пришлите <b>ссылку на лот</b> или его <b>ID</b> (число).\nНапример: <code>https://funpay.com/lots/offer?id=12345678</code> или <code>12345678</code>\n\n💡 Можно сразу НЕСКОЛЬКО (клоны): каждую ссылку/ID с новой строки или через пробел — привяжутся все разом.\nНазвание и описание лота подтянутся автоматически.', _wait_kb(_waiting[chat_id]))
    elif action in ('d4s_grpp', 'd4s_grpn', 'd4s_grps'):
        st = _waiting.get(chat_id)
        if not st or st.get('action') not in ('bind_group_wait',):
            ack('Сессия истекла — начните заново')
            return
        if action == 'd4s_grpp':
            gi = iarg(0, -2)
            group = _group_by_idx(gi)
            if not group:
                ack('Группа не найдена')
                return
            ack()
            _finalize_binding(chat_id, st, group)
        elif action == 'd4s_grps':
            ack()
            _finalize_binding(chat_id, st, '')
        else:
            st['action'] = 'bind_group_new'
            _waiting[chat_id] = st
            ack()
            _tg_send(chat_id, '➕ Отправьте название новой группы (например, <code>CS2</code>, <code>Dota 2</code>, <code>PUBG</code>).', _wait_kb(st))
    elif action == 'd4s_cat':
        ack()
        _menu_catalog(chat_id, message_id, iarg(0, 0))
    elif action == 'd4s_orders':
        ack()
        _menu_orders(chat_id, message_id)
    elif action == 'd4s_stats':
        ack()
        _menu_stats(chat_id, message_id)
    elif action == 'd4s_health':
        ack('Проверяю...')
        _menu_health(chat_id, message_id)
    elif action == 'd4s_db_order_commit':
        with _orders_lock:
            od = dict(_pending.get(arg) or {})
        if not od or not od.get('database_id'):
            ack('Заказ не найден')
            return
        count = _commit_database_reservation(str(od['database_id']), arg)
        _finish_order(arg, 'COMPLETED_MANUAL', int(od.get('cost_kop') or 0))
        _record_sale(int(od.get('product_id') or 0), str(od.get('product_title') or 'Товар'), int(od.get('qty') or count), float(od.get('price_rub') or 0) if str(od.get('currency') or '') in ('', 'rub', '₽') else 0.0, 0.0)
        ack('Отмечено выданным')
        _tg_send(chat_id, f'✅ Заказ #{arg} отмечен выданным. Списано из базы: {count}.')
        threading.Thread(target=_resync_database_lots, args=(str(od['database_id']),), daemon=True).start()
    elif action == 'd4s_db_order_release':
        with _orders_lock:
            od = _pending.get(arg)
            snapshot = dict(od or {})
        if not od or not od.get('database_id'):
            ack('Заказ не найден')
            return
        count = _release_database_reservation(str(od['database_id']), arg)
        with _orders_lock:
            current = _pending.get(arg)
            if current:
                current['database_reserved'] = 0
                current['database_uncertain'] = False
                current['step'] = 'failed'
                current['error'] = 'Резерв вручную возвращён в базу после проверки'
                _save_orders_state()
        ack('Резерв возвращён')
        kb = _make_kb([[('🔁 Повторить выдачу', f'd4s_retry:{arg}'), ('↩️ Вернуть деньги', f'd4s_refund:{arg}')]])
        _tg_send(chat_id, f'♻️ В базу возвращено: {count}. Теперь можно повторить выдачу или вернуть деньги.', kb)
        threading.Thread(target=_resync_database_lots, args=(str(snapshot.get('database_id') or ''),), daemon=True).start()
    elif action == 'd4s_retry':
        with _orders_lock:
            od = _pending.get(arg)
            already_processed = arg in _processed
        if not od:
            ack('Заказ уже завершён')
            return
        if already_processed or str(od.get('step') or '') == 'delivered':
            ack('Товар уже отмечен выданным')
            return
        if od.get('delivery_uncertain') or str(od.get('step') or '') == 'sending':
            ack('Повтор заблокирован: сначала проверьте чат покупателя')
            _tg_send(chat_id, f'⚠️ Заказ #{arg}: повторная автоматическая выдача заблокирована, потому что товар мог уже частично или полностью уйти покупателю. Сначала проверьте чат FunPay вручную.')
            return
        if str(od.get('delivery_mode') or 'api') == 'database' and od.get('database_reserved'):
            ack('Сначала проверьте резерв базы вручную')
            return
        ack('Повторяю выдачу...')
        _tg_send(chat_id, f'🔁 Повторяю выдачу по заказу #{arg}...')
        _log_event('manual_retry', order_id=arg, step=od.get('step'), shop_order_id=od.get('shop_order_id'))
        threading.Thread(target=process_order, args=(arg,), daemon=True).start()
    elif action == 'd4s_refund':
        with _orders_lock:
            od = _pending.get(arg)
        if not od:
            ack('Заказ уже завершён')
            return
        if str(od.get('delivery_mode') or 'api') == 'database' and od.get('database_reserved'):
            ack('Сначала решите судьбу резерва базы')
            return
        ack()
        if _try_refund(arg):
            _fp_send(od['chat_id'], _buyer_message('refund', order_id=arg, order_url=f'https://funpay.com/orders/{arg}/', product_title=od['product_title'], qty=od['qty'], reason=od.get('error', '')), od['buyer'])
            _finish_order(arg, 'FAILED_REFUNDED')
            _tg_send(chat_id, f'↩️ Возврат по заказу #{arg} выполнен.')
        else:
            _tg_send(chat_id, f'❌ Возврат по #{arg} не удался — сделайте вручную на FunPay.')
    else:
        ack()
def _text_handler(m) -> None:
    chat_id = getattr(getattr(m, 'chat', None), 'id', None)
    if chat_id is None:
        return
    st = _waiting.get(chat_id)
    if not st:
        return
    if not _is_authorized(getattr(getattr(m, 'from_user', None), 'id', None)):
        return
    text = (getattr(m, 'text', None) or '').strip()
    if text.lower() in ('/cancel', 'отмена', 'cancel'):
        _cancel_wait(chat_id, st)
        return
    action = st.get('action')
    if action == 'db_create_name':
        try:
            name = _validate_database_name(text)
        except Exception as e:
            _tg_send(chat_id, f'⚠️ {str(e)[:150]}', _wait_kb(st))
            return
        st['action'] = 'db_create_product'
        st['name'] = name
        _waiting[chat_id] = st
        _menu_database_product_select(chat_id)
    elif action == 'db_rename':
        try:
            db = _rename_database(str(st.get('database_id') or ''), text)
        except Exception as e:
            _tg_send(chat_id, f'⚠️ {str(e)[:150]}', _wait_kb(st))
            return
        _waiting.pop(chat_id, None)
        _tg_send(chat_id, f"✅ База переименована: <b>{db['name']}</b>.")
        _menu_database_detail(chat_id, None, db['id'])
    elif action == 'db_replenish_qty':
        try:
            qty = int(text)
            if qty < 1 or qty > API_QTY_MAX:
                raise ValueError(f'Введите число от 1 до {API_QTY_MAX}')
        except Exception as e:
            _tg_send(chat_id, f'⚠️ {str(e)[:150]}', _wait_kb(st))
            return
        database_id = str(st.get('database_id') or '')
        _waiting.pop(chat_id, None)
        _tg_send(chat_id, f'⏳ Покупаю {qty} шт. для базы…')
        def _work_db_replenish():
            try:
                result = _replenish_database(database_id, qty)
                _tg_send(chat_id, f"✅ В базу добавлено: {result['qty']} шт. Теперь доступно: {result['available']}.")
                _resync_database_lots(database_id)
            except Exception as e:
                logger.error(f'{LP} database replenish {database_id}: {e}')
                _tg_send(chat_id, f'❌ База не пополнена: {str(e)[:220]}')
            _menu_database_detail(chat_id, None, database_id)
        threading.Thread(target=_work_db_replenish, daemon=True).start()
    elif action == 'db_import_text':
        database_id = str(st.get('database_id') or '')
        try:
            result = _import_database_items(database_id, text.splitlines(), 'manual_text')
        except Exception as e:
            _tg_send(chat_id, f'❌ Аккаунты не добавлены: {str(e)[:220]}', _wait_kb(st))
            return
        _waiting.pop(chat_id, None)
        _tg_send(chat_id, f"✅ Добавлено: <b>{result['added']}</b>. Пропущено: <b>{result['skipped']}</b>. Сейчас доступно: <b>{result['available']}</b>.")
        _resync_database_lots(database_id)
        _menu_database_detail(chat_id, None, database_id)
    elif action == 'db_import_file':
        _tg_send(chat_id, '📎 Ожидаю файл <code>.txt</code> или <code>.csv</code>.', _wait_kb(st))
    elif action == 'lot_manual_id':
        ids = _parse_lot_ids(text)
        if not ids:
            _tg_send(chat_id, '⚠️ Пришлите числовой LOT ID или ссылку вида <code>https://funpay.com/lots/offer?id=...</code>.', _wait_kb(st))
            return
        lot_id = ids[0]
        try:
            lot = _validate_funpay_lot(lot_id)
        except Exception as e:
            _tg_send(chat_id, f'❌ Лот не прочитан: {str(e)[:180]}', _wait_kb(st))
            return
        _restore_lot_to_plugin(lot_id)
        _cache_funpay_lot(lot)
        _waiting[chat_id] = {'action': 'lot_manual_type', 'lot_id': lot_id}
        _menu_lot_type_pick(chat_id, None, lot_id)
    elif action == 'lot_set_qty':
        try:
            qty = int(text)
            if qty < 1 or qty > FUNPAY_ORDER_QTY_MAX:
                raise ValueError(f'Введите число от 1 до {FUNPAY_ORDER_QTY_MAX}')
        except Exception as e:
            _tg_send(chat_id, f'⚠️ {str(e)[:120]}', _wait_kb(st))
            return
        lot_id = str(st.get('lot_id') or '')
        with _bindings_lock:
            if lot_id not in _bindings:
                _waiting.pop(chat_id, None)
                _menu_lot_settings(chat_id)
                return
            _bindings[lot_id]['qty_per_unit'] = qty
            _bindings[lot_id]['qty'] = qty
            binding = _normalize_binding(_bindings[lot_id])
            _bindings[lot_id] = binding
            _save_bindings()
        _waiting.pop(chat_id, None)
        _tg_send(chat_id, f'✅ За одну единицу заказа будет выдаваться: {qty}.')
        if _binding_stock_target(binding) > 0:
            threading.Thread(target=_sync_binding_stock, args=(lot_id, binding), daemon=True).start()
        _menu_lot_detail(chat_id, None, lot_id)
    elif action == 'lot_set_stock':
        try:
            target = int(text)
            if target < 0 or target > 500:
                raise ValueError('Введите число от 0 до 500')
        except Exception as e:
            _tg_send(chat_id, f'⚠️ {str(e)[:120]}', _wait_kb(st))
            return
        lot_id = str(st.get('lot_id') or '')
        with _bindings_lock:
            if lot_id not in _bindings:
                _waiting.pop(chat_id, None)
                _menu_lot_settings(chat_id)
                return
            _bindings[lot_id]['fp_stock_target'] = target
            _bindings[lot_id]['fp_auto'] = target > 0
            binding = _normalize_binding(_bindings[lot_id])
            _bindings[lot_id] = binding
            _save_bindings()
        _waiting.pop(chat_id, None)
        if target > 0:
            threading.Thread(target=_sync_binding_stock, args=(lot_id, binding), daemon=True).start()
        else:
            threading.Thread(target=_disable_fp_autodelivery, args=(lot_id,), daemon=True).start()
        _tg_send(chat_id, f'✅ Лимит автовыдачи FunPay: {target}.')
        _menu_lot_detail(chat_id, None, lot_id)
    elif action == 'config_import':
        _tg_send(chat_id, '📥 Ожидаю ZIP-файл резервной копии.', _wait_kb(st))
    elif action == 'set_key':
        if not text.startswith('rk_'):
            _tg_send(chat_id, '⚠️ Ключ должен начинаться с <code>rk_</code>. Попробуйте ещё раз.', _wait_kb(st))
            return
        old_key = str(cfg_get('api_key') or '')
        with _config_lock:
            _config['api_key'] = text
        _reset_api_runtime()
        try:
            bal = _refresh_balance()
        except ShopNetworkError:
            with _config_lock:
                _config['api_key'] = old_key
            _reset_api_runtime()
            _tg_send(chat_id, '❌ Проблема с подключением к API dim4n4ik.shop. API-ключ не сохранён. Проверьте интернет или доступность сервиса и попробуйте ещё раз.', _wait_kb(st))
            return
        except ShopApiError as e:
            with _config_lock:
                _config['api_key'] = old_key
            _reset_api_runtime()
            reason = ERROR_HUMAN.get(e.code, e.message or e.code)
            _tg_send(chat_id, f'❌ API-ключ не сохранён. Сервис отклонил проверку: {reason}', _wait_kb(st))
            return
        except Exception as e:
            with _config_lock:
                _config['api_key'] = old_key
            _reset_api_runtime()
            _tg_send(chat_id, f'❌ Не удалось проверить подключение к API. API-ключ не сохранён: {str(e)[:120]}', _wait_kb(st))
            return
        cfg_set('api_key', text)
        _waiting.pop(chat_id, None)
        _tg_send(chat_id, f'✅ API-ключ добавлен. Баланс: {_fmt_rub_kop(bal)}')
        _menu_account(chat_id)
    elif action == 'set_lowbal':
        try:
            val = float(text.replace(',', '.'))
        except Exception:
            _tg_send(chat_id, '⚠️ Отправьте число (рубли).', _wait_kb(st))
            return
        _waiting.pop(chat_id, None)
        cfg_set('low_balance_threshold_rub', max(val, 0.0))
        _menu_notifications(chat_id)
    elif action == 'set_balance_interval':
        try:
            val = int(text)
        except Exception:
            _tg_send(chat_id, '⚠️ Отправьте целое число минут.', _wait_kb(st))
            return
        if val < 1 or val > 1440:
            _tg_send(chat_id, '⚠️ Интервал должен быть от 1 до 1440 минут.', _wait_kb(st))
            return
        _waiting.pop(chat_id, None)
        cfg_set('balance_check_interval_min', val)
        _menu_notifications(chat_id)
    elif action == 'edit_buyer_message':
        key = str(st.get('key') or '')
        if key not in BUYER_MESSAGE_LABELS:
            _waiting.pop(chat_id, None)
            _menu_buyer_messages(chat_id)
            return
        if not text or len(text) > 3500:
            _tg_send(chat_id, '⚠️ Сообщение должно содержать от 1 до 3500 символов.', _wait_kb(st))
            return
        sample = {'order_id': '123', 'order_url': 'https://funpay.com/orders/123/', 'product_title': 'Товар', 'qty': '1', 'reason': 'Причина'}
        try:
            text.format(**sample)
        except Exception as e:
            _tg_send(chat_id, f'⚠️ Ошибка в переменных сообщения: {str(e)[:120]}', _wait_kb(st))
            return
        messages = _buyer_messages()
        messages[key] = text
        cfg_set('buyer_messages', messages)
        _waiting.pop(chat_id, None)
        _tg_send(chat_id, '✅ Сообщение сохранено.')
        _menu_buyer_messages(chat_id)
    elif action == 'set_margin':
        try:
            val = float(text.replace(',', '.'))
        except Exception:
            _tg_send(chat_id, '⚠️ Отправьте число (проценты).', _wait_kb(st))
            return
        _waiting.pop(chat_id, None)
        cfg_set('loss_min_margin_percent', max(0.0, val))
        _tg_send(chat_id, f"✅ Мин. маржа: {int(cfg_get('loss_min_margin_percent'))}%")
        _menu_safety(chat_id)
    elif action == 'set_fpbuf':
        try:
            val = int(text)
        except Exception:
            _tg_send(chat_id, '⚠️ Отправьте целое число.', _wait_kb(st))
            return
        _waiting.pop(chat_id, None)
        cfg_set('fp_auto_buffer', max(1, min(val, 500)))
        _tg_send(chat_id, f'✅ Буфер мгновенной выдачи: {_fp_buffer()} шт.')
        _menu_lot_settings(chat_id)
    elif action == 'set_fpsync':
        try:
            val = int(text)
        except Exception:
            _tg_send(chat_id, '⚠️ Отправьте число секунд.', _wait_kb(st))
            return
        _waiting.pop(chat_id, None)
        cfg_set('fp_auto_sync_sec', max(30, val))
        _tg_send(chat_id, f"✅ Интервал синка: {int(cfg_get('fp_auto_sync_sec'))} c.")
        _menu_lot_settings(chat_id)
    elif action == 'bind_lot':
        ids = _parse_lot_ids(text)
        if not ids:
            _tg_send(chat_id, '⚠️ Пришлите ссылку на лот (<code>https://funpay.com/lots/offer?id=...</code>) или его ID (число).', _wait_kb(st))
            return
        with _bindings_lock:
            already = [i for i in ids if i in _bindings]
            ids = [i for i in ids if i not in _bindings]
        note = f"\n🔗 Уже привязаны, пропускаю: {', '.join(already)}" if already else ''
        if not ids:
            _tg_send(chat_id, f'⚠️ Все эти лоты уже привязаны.{note}\nПришлите другие.', _wait_kb(st))
            return
        if len(ids) == 1:
            st['lot_id'] = ids[0]
            count_txt = f'Лот {ids[0]}.'
        else:
            st['lot_ids'] = ids
            count_txt = f'Лотов: {len(ids)}.'
        st['action'] = 'bind_qty'
        _tg_send(chat_id, f'{count_txt}{note}\nШаг 4/5 — сколько единиц товара выдавать за 1 шт. заказа? (обычно 1; отправьте <code>-</code> для 1)', _wait_kb(st))
    elif action == 'bind_qty':
        if text == '-':
            qty = 1
        else:
            try:
                qty = int(text)
                if qty < 1 or qty > FUNPAY_ORDER_QTY_MAX:
                    raise ValueError
            except Exception:
                _tg_send(chat_id, f'⚠️ Отправьте число от 1 до {FUNPAY_ORDER_QTY_MAX} или <code>-</code>.', _wait_kb(st))
                return
        st['qty'] = qty
        st['mode'] = 'create'
        _send_group_picker(chat_id, st)
    elif action == 'bind_group_new':
        group = text[:40].strip()
        if not group:
            _tg_send(chat_id, '⚠️ Пустое имя. Отправьте название группы.', _wait_kb(st))
            return
        _finalize_binding(chat_id, st, group)
    elif action == 'grp_rename':
        new = text[:40].strip()
        if not new:
            _tg_send(chat_id, '⚠️ Пустое имя. Отправьте название.', _wait_kb(st))
            return
        _waiting.pop(chat_id, None)
        n = _rename_group(st['old'], new)
        _tg_send(chat_id, f"✅ Группа «{st['old']}» → «{new}» ({n} привязок)")
        _menu_bindings(chat_id)
    elif action == 'bind_setqty':
        try:
            qty = int(text)
            if qty < 1 or qty > FUNPAY_ORDER_QTY_MAX:
                raise ValueError
        except Exception:
            _tg_send(chat_id, f'⚠️ Отправьте целое число от 1 до {FUNPAY_ORDER_QTY_MAX}.', _wait_kb(st))
            return
        _waiting.pop(chat_id, None)
        with _bindings_lock:
            if st['lot_id'] in _bindings:
                _bindings[st['lot_id']]['qty'] = qty
                _bindings[st['lot_id']]['qty_per_unit'] = qty
                _save_bindings()
        _tg_send(chat_id, f"✅ Кол-во для лота {st['lot_id']}: ×{qty}")
        _menu_bindings(chat_id)
    elif action == 'bind_setname':
        _waiting.pop(chat_id, None)
        with _bindings_lock:
            if st['lot_id'] in _bindings:
                _bindings[st['lot_id']]['lot_name'] = text
                _save_bindings()
        _tg_send(chat_id, f"✅ Название лота {st['lot_id']} сохранено.")
        _menu_bindings(chat_id)
    else:
        _waiting.pop(chat_id, None)
def _database_import_document_handler(message) -> None:
    chat_id = getattr(getattr(message, 'chat', None), 'id', None)
    if chat_id is None:
        return
    st = _waiting.get(chat_id) or {}
    if st.get('action') != 'db_import_file':
        return
    if not _is_authorized(getattr(getattr(message, 'from_user', None), 'id', None)):
        return
    document = getattr(message, 'document', None)
    filename = str(getattr(document, 'file_name', '') or '')
    if not filename.lower().endswith(('.txt', '.csv')):
        _tg_send(chat_id, '⚠️ Нужен файл <code>.txt</code> или <code>.csv</code>.', _wait_kb(st))
        return
    try:
        size = int(getattr(document, 'file_size', 0) or 0)
        if size > 5 * 1024 * 1024:
            raise ValueError('Файл слишком большой. Максимум 5 МБ')
        info = bot.get_file(document.file_id)
        payload = bytes(bot.download_file(info.file_path))
        if len(payload) > 5 * 1024 * 1024:
            raise ValueError('Файл слишком большой. Максимум 5 МБ')
        text = None
        for encoding in ('utf-8-sig', 'utf-8', 'cp1251'):
            try:
                text = payload.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        if text is None:
            raise ValueError('Не удалось определить кодировку файла')
        database_id = str(st.get('database_id') or '')
        result = _import_database_items(database_id, text.splitlines(), 'file')
        _waiting.pop(chat_id, None)
        _tg_send(chat_id, f"✅ Файл <b>{filename[:80]}</b> импортирован. Добавлено: <b>{result['added']}</b>. Пропущено: <b>{result['skipped']}</b>. Сейчас доступно: <b>{result['available']}</b>.")
        _resync_database_lots(database_id)
        _menu_database_detail(chat_id, None, database_id)
    except Exception as e:
        logger.error(f'{LP} database file import: {e}')
        _tg_send(chat_id, f'❌ Файл не импортирован: {str(e)[:220]}', _wait_kb(st))
def _waiting_message_handler(message) -> None:
    chat_id = getattr(getattr(message, 'chat', None), 'id', None)
    if chat_id is None:
        return
    st = _waiting.get(chat_id) or {}
    action = st.get('action')
    if getattr(message, 'document', None) is not None:
        if action == 'db_import_file':
            _database_import_document_handler(message)
            return
        if action == 'config_import':
            _config_import_document_handler(message)
            return
        if action == 'plugin_local_update':
            _local_update_document_handler(message)
            return
        return
    _text_handler(message)
def _config_import_document_handler(message) -> None:
    chat_id = getattr(getattr(message, 'chat', None), 'id', None)
    if chat_id is None:
        return
    st = _waiting.get(chat_id) or {}
    if st.get('action') != 'config_import':
        return
    if not _is_authorized(getattr(getattr(message, 'from_user', None), 'id', None)):
        return
    document = getattr(message, 'document', None)
    filename = str(getattr(document, 'file_name', '') or '')
    if not filename.lower().endswith('.zip'):
        _tg_send(chat_id, '⚠️ Нужен ZIP-файл резервной копии.', _wait_kb(st))
        return
    temp = Path(BACKUPS_DIR) / f'import-{int(time.time() * 1000)}.zip'
    try:
        with _orders_lock:
            active_orders = len(_pending)
        if active_orders:
            _tg_send(chat_id, f'⚠️ Импорт заблокирован: сейчас есть незавершённые заказы ({active_orders}). Завершите их и повторите импорт.', _wait_kb(st))
            return
        info = bot.get_file(document.file_id)
        payload = bytes(bot.download_file(info.file_path))
        temp.write_bytes(payload)
        check = _validate_backup_archive(str(temp))
        if not check.get('ok'):
            _tg_send(chat_id, f"❌ Архив отклонён: {check.get('error')}", _wait_kb(st))
            return
        result = _restore_backup_archive(str(temp))
        if not result.get('ok'):
            _tg_send(chat_id, f"❌ Импорт не выполнен: {result.get('error')}", _wait_kb(st))
            return
        _waiting.pop(chat_id, None)
        _stop_event.set()
        _tg_send(chat_id, f"✅ Восстановлено файлов: {len(result.get('restored') or [])}. Перед импортом создана резервная копия. Фоновые операции плагина остановлены до перезапуска. Выполните <code>/restart</code>.", _make_kb([[('◀️ Обслуживание', 'd4s_maintenance')]]))
    except Exception as e:
        logger.error(f'{LP} config import: {e}')
        _tg_send(chat_id, f'❌ Импорт не выполнен: {str(e)[:220]}', _wait_kb(st))
    finally:
        try:
            temp.unlink(missing_ok=True)
        except Exception:
            pass
def _register_telegram_handlers(c) -> None:
    global admin_chat_id
    predicate = lambda m: getattr(getattr(m, 'chat', None), 'id', None) in _waiting
    try:
        tg_register = getattr(getattr(c, 'telegram', None), 'msg_handler', None)
        if callable(tg_register):
            tg_register(_waiting_message_handler, func=predicate, content_types=['text', 'document'])
        else:
            bot.register_message_handler(_waiting_message_handler, func=predicate, content_types=['text', 'document'])
    except Exception as e:
        logger.warning(f'{LP} cannot register waiting message handler: {e}')
    def _cmd_handler(message):
        global admin_chat_id
        chat_id = getattr(getattr(message, 'chat', None), 'id', None)
        if not chat_id:
            return
        if not _is_authorized(getattr(getattr(message, 'from_user', None), 'id', None)):
            return
        if admin_chat_id is None:
            admin_chat_id = chat_id
        _plugin_home(chat_id)
    try:
        bot.register_message_handler(_cmd_handler, commands=['d4shop'])
    except Exception as e:
        logger.warning(f'{LP} cannot register /d4shop: {e}')
    def _cb_safe(call):
        data = str(getattr(call, 'data', None) or '')
        chat_id = getattr(getattr(getattr(call, 'message', None), 'chat', None), 'id', None)
        started = time.monotonic()
        _log_event('telegram_callback', action=data[:160], chat_id=chat_id)
        try:
            _cb_router(call)
            _log_event('telegram_callback_done', action=data[:160], chat_id=chat_id, ms=int((time.monotonic() - started) * 1000))
        except Exception as e:
            _log_event('telegram_callback_error', level=logging.ERROR, action=data[:160], chat_id=chat_id, error=str(e)[:200], ms=int((time.monotonic() - started) * 1000))
            logger.exception(f'{LP} callback error: {e}')
            try:
                if chat_id:
                    _tg_send(chat_id, f'❌ Ошибка: {str(e)[:100]}')
            except Exception:
                pass
    try:
        bot.register_callback_query_handler(_cb_safe, func=lambda call: isinstance(getattr(call, 'data', None), str) and call.data.startswith('d4s'))
    except Exception as e:
        logger.warning(f'{LP} cannot register callbacks: {e}')
    if _CBT:
        def _open_plugin_home(call):
            try:
                bot.answer_callback_query(call.id)
            except Exception:
                pass
            chat_id = getattr(getattr(getattr(call, 'message', None), 'chat', None), 'id', None)
            message_id = getattr(getattr(call, 'message', None), 'message_id', None)
            if chat_id:
                global admin_chat_id
                if admin_chat_id is None:
                    admin_chat_id = chat_id
                _plugin_home(chat_id, message_id)
        def _plugin_entry(data):
            data = str(data or '')
            if data in (CBT_SETTINGS, f'{UUID}:0'):
                return True
            edit = getattr(_CBT, 'EDIT_PLUGIN', None)
            settings = getattr(_CBT, 'PLUGIN_SETTINGS', None)
            return bool((edit is not None and data.startswith(f'{edit}:{UUID}')) or (settings is not None and data.startswith(f'{settings}:{UUID}')))
        try:
            c.telegram.cbq_handler(_open_plugin_home, func=lambda call: _plugin_entry(getattr(call, 'data', None)))
        except Exception as e:
            logger.warning(f'{LP} cannot register plugin menu button: {e}')
    logger.info(f'{LP} Telegram handlers registered')
def d4s_pre_init(c, *args) -> None:
    global cardinal, bot, admin_chat_id, _config, _bindings, _pending, _processed
    _early_storage_migration()
    _configure_file_logging()
    _stop_event.clear()
    cardinal = c
    logger.info(f'{LP} initializing v{VERSION}...')
    try:
        bot_obj = getattr(c.telegram, 'bot', None)
    except Exception:
        bot_obj = None
    globals()['bot'] = bot_obj
    with _config_lock:
        cfg = load_json(CONFIG_FILE, {})
        _config = dict(DEFAULT_CONFIG)
        _config['buyer_messages'] = dict(DEFAULT_BUYER_MESSAGES)
        if isinstance(cfg, dict):
            _config.update({k: v for k, v in cfg.items() if k in DEFAULT_CONFIG})
            messages = dict(DEFAULT_BUYER_MESSAGES)
            if isinstance(cfg.get('buyer_messages'), dict):
                raw_messages = cfg['buyer_messages']
                messages.update({str(k): str(v) for k, v in raw_messages.items() if k in messages})
                if str(raw_messages.get('goods_header') or '') == LEGACY_DEFAULT_GOODS_HEADER:
                    messages['goods_header'] = DEFAULT_BUYER_MESSAGES['goods_header']
            _config['buyer_messages'] = messages
        if not isinstance(_config.get('lot_cache'), list):
            _config['lot_cache'] = []
        save_json(CONFIG_FILE, _config)
    with _bindings_lock:
        raw_bindings = load_json(BINDINGS_FILE, {})
        _bindings = _normalize_bindings(raw_bindings)
        save_json(BINDINGS_FILE, _bindings)
    with _orders_lock:
        p = load_json(PENDING_FILE, {})
        _pending = p if isinstance(p, dict) else {}
        pr = load_json(PROCESSED_FILE, {})
        _processed = pr if isinstance(pr, dict) else {}
    ad = load_json(AUTO_DISABLED_FILE, {})
    _auto_disabled.clear()
    _auto_disabled.update(ad if isinstance(ad, dict) else {})
    save_json(AUTO_DISABLED_FILE, _auto_disabled)
    if not Path(ORDER_LOG_FILE).exists() or _raw_json(Path(ORDER_LOG_FILE), list) is None:
        save_json(ORDER_LOG_FILE, [])
    if not Path(STATS_FILE).exists() or _raw_json(Path(STATS_FILE), dict) is None:
        save_json(STATS_FILE, dict(DEFAULT_STATS))
    try:
        auth = getattr(getattr(c, 'telegram', None), 'authorized_users', None)
        if isinstance(auth, dict) and auth:
            admin_chat_id = int(list(auth.keys())[0])
    except Exception:
        admin_chat_id = None
    logger.info(f'{LP} admin_chat_id={admin_chat_id}, bindings={len(_bindings)}, pending={len(_pending)}, processed={len(_processed)}')
    try:
        c.add_telegram_commands(UUID, [('d4shop', 'Auto Steam Account: меню плагина', True)])
    except Exception as e:
        logger.warning(f'{LP} add_telegram_commands: {e}')
    if bot:
        _register_telegram_handlers(c)
    _recover_pending_orders_after_restart()
    start_background_loops()
    logger.info(f'{LP} initialized')
def on_delete(*args) -> None:
    _stop_event.set()
    try:
        _save_orders_state()
        _save_bindings()
        _save_auto_disabled()
    except Exception:
        pass
    logger.info(f'{LP} plugin delete: state saved')
    _close_file_logging()
BIND_TO_PRE_INIT = [d4s_pre_init]
BIND_TO_NEW_ORDER = [handle_new_order]
BIND_TO_NEW_MESSAGE = [handle_new_message]
BIND_TO_LAST_CHAT_MESSAGE_CHANGED = [handle_new_message]
BIND_TO_INIT_MESSAGE = [handle_new_message]
BIND_TO_DELETE = [on_delete]