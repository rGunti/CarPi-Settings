"""
CARPI SETTINGS
(C) 2018, Raphael "rGunti" Guntersweiler
Licensed under MIT
"""

from configparser import ConfigParser
from logging import Logger
from os.path import basename
from typing import Any

from carpicommons.log import logger


class ConfigError:
    pass


class ConfigStore(object):
    """
    Defines a base implementation for a configuration store
    """
    def __init__(self, logger_name: str = None):
        self._log: Logger = logger(logger_name
                                   if logger_name
                                   else self.__class__.__name__)
        self._log.debug("Setting up new Config Store ...")

    def read_value(self, key: str, default: str=None) -> str:
        raise NotImplementedError

    def read_int_value(self, key: str, default: int=None) -> int:
        self._log.debug("Reading %s as Int", key)
        v = self.read_value(key)
        return int(v) if v is not None else default

    def read_float_value(self, key: str, default: float=None) -> float:
        self._log.debug("Reading %s as Float", key)
        v = self.read_value(key)
        return float(v) if v is not None else default

    def read_bool_value(self, key: str, default: bool=False) -> bool:
        self._log.debug("Reading %s as Bool", key)
        v = self.read_value(key)
        return v == "1" if v is not None else default

    def write_value(self, key: str, value: Any):
        raise NotImplementedError

    def save_config(self):
        raise NotImplementedError


class MemoryStore(ConfigStore):
    """
    Provides a ConfigStore compliant interface to an in-memory
    dictionary which is not persisted over multiple runtimes
    """
    def __init__(self,
                 logger_name: str = None):
        """
        :param logger_name: optional custom name provided in Log
        """
        super().__init__(logger_name)
        self._dict = dict()
        self._log.info("New In-Memory configuration setup")

    def read_value(self, key: str, default: str = None) -> str:
        self._log.debug("Reading %s", key)
        return self._dict.get(key, default=default)

    def write_value(self, key: str, value: Any):
        self._log.debug("Writing %s", key)
        self._dict[key] = value

    def save_config(self):
        self._log.warning("In-Memory configurations cannot be saved! This is a NOOP")


class IniStore(ConfigStore):
    """
    Provides a ConfigStore compliant interface to an INI file
    using Pythons "ConfigParser" API
    """
    def __init__(self,
                 ini_file: str,
                 logger_name: str = None):
        """
        Instantiates a new INI Config Store and auto-loads data from
        a given file
        :param ini_file: INI file to autoload
        :param logger_name: optional custom name provided in Log
        """
        super().__init__(logger_name
                         if logger_name else
                         basename(ini_file))
        self._config: ConfigParser = self._load_config(ini_file)
        self._file_path = ini_file

    def _load_config(self, ini_file: str):
        c = ConfigParser()
        self._log.info("Reading configuration from %s ...", ini_file)
        with open(ini_file, 'r') as f:
            c.read_file(f)

        self._log.info("Read configuration successfully")
        return c

    @staticmethod
    def _parse_key(key: str) -> tuple:
        dot = key.index('.')
        return key[:dot], key[dot + 1:]

    def read_value(self, key: str, default: str=None) -> str:
        ini_sec, ini_key = IniStore._parse_key(key)
        self._log.debug("Reading [%s] %s", ini_sec, ini_key)
        return self._config.get(ini_sec, ini_key, fallback=default)

    def read_int_value(self, key: str, default: int = None) -> int:
        ini_sec, ini_key = IniStore._parse_key(key)
        self._log.debug("Reading [%s] %s as Int", ini_sec, ini_key)
        return self._config.getint(ini_sec, ini_key, fallback=default)

    def read_float_value(self, key: str, default: float = None) -> float:
        ini_sec, ini_key = IniStore._parse_key(key)
        self._log.debug("Reading [%s] %s as Float", ini_sec, ini_key)
        return self._config.getfloat(ini_sec, ini_key, fallback=default)

    def read_bool_value(self, key: str, default: bool = False) -> bool:
        ini_sec, ini_key = IniStore._parse_key(key)
        self._log.debug("Reading [%s] %s as Bool", ini_sec, ini_key)
        return self._config.getboolean(ini_sec, ini_key, fallback=default)

    def write_value(self, key: str, value: Any):
        ini_sec, ini_key = IniStore._parse_key(key)
        self._log.debug("Writing [%s] %s", ini_sec, ini_key)
        self._config.set(ini_sec, ini_key, str(value))

    def save_config(self):
        self._log.info("Writing configuration to %s ...", self._file_path)
        with open(self._file_path, 'w') as f:
            self._config.write(f)

        self._log.info("Completed!", self._file_path)


try:
    from redis.client import Redis

    class RedisStore(ConfigStore):
        """
        Provides a ConfigStore compliant interface to a Redis Database
        """
        def __init__(self,
                     redis: Redis = None,
                     url: str = None,
                     host: str = '127.0.0.1',
                     port: int = 6379,
                     db: int = 0,
                     password: str = None,
                     logger_name: str = None):
            """
            Instantiates a new Redis Config Store using one of three methods:

            1. When a Redis instance is passed (using the parameter "redis"), it will simply reuse it

            2. When a Redis URL is passed (using the parameter "url"), it will try to establish a connection using said URL

            3. In all other cases, it will try to connect to a Redis instance with the provided data

            :param redis: Redis instance to use (default: None)
            :param url: Redis URL to connect to (default: None)
            :param host: Redis Host (default: 127.0.0.1)
            :param port: Redis Host Port (default: 6379)
            :param db: Redis Database (default: 0)
            :param password: Redis Host Password (default: None)
            :param logger_name: optional custom name provided in Log
            """
            super().__init__(logger_name if logger_name
                             else (url if url
                                   else ("Redis {}".format(host) if host
                                         else None)))

            # Setup instance vars
            self._redis: Redis = None

            if redis:
                # If Redis instance was provided, use it
                r = redis
            elif url:
                # If Redis URL was provided, create new instance with it
                r = Redis.from_url(url)
            else:
                # Else, try setting up a new Redis instance with primitive information
                r = RedisStore._build_redis(host, port, db, password)

            # Assign Redis instance to class
            self._redis = r

        @staticmethod
        def _build_redis(host: str,
                         port: int=6379,
                         db: int=0,
                         password: str=None) -> Redis:
            return Redis(host=host,
                         port=port,
                         db=db,
                         password=password)

        def read_value(self, key: str, default: str = None) -> str:
            self._log.debug("Reading %s", key)
            v = self._redis.get(key)
            return str(v) if v else default

        def write_value(self, key: str, value: Any):
            self._log.debug("Writing %s", key)
            self._redis.set(key, str(value))

        def save_config(self):
            self._log.info("Issuing SAVE ...")
            self._redis.save()
            self._log.info("SAVE completed")

except ModuleNotFoundError:
    # Redis Config store is only exported when the Redis module is available
    pass
