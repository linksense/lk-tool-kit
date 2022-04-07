import pickle  # noqa: S403
import struct
import zlib
from enum import Enum
from typing import Callable, Dict, Optional, Tuple, Union


class Version(bytes, Enum):
    V1 = b"V1"
    OLD = b"OLD"

    CURRENT = V1


class Serializable:
    _BOARD_OBJ_VERSION_DESERIALIZER_MAP: Dict[
        Version, Callable[[type, bytes, bool, float], "Serializable"]
    ] = {
        Version.V1: lambda cls, data, compress, timestamp: pickle.loads(  # noqa: S301
            zlib.decompress(data[15:]) if compress else data[15:]
        ),
    }
    _VERSION_PREFIX: bytes = b"version"
    _serialization_version: Optional[Version] = None

    @classmethod
    def set_legacy_version_deserializer(
        cls, deserializer: Callable[[type, bytes, bool, float], "Serializable"]
    ) -> None:
        cls._BOARD_OBJ_VERSION_DESERIALIZER_MAP[Version.OLD] = deserializer

    @classmethod
    def is_legacy_version(cls, data: bytes) -> bool:
        raise NotImplementedError

    @classmethod
    def _version_encoder(cls, bytes_data: bytes) -> bytes:
        """
        新版本的版本编码器

        Args:
            bytes_data (bytes): _description_

        Returns:
            bytes: _description_
        """
        mask = Version.CURRENT.value
        lmask = len(mask)
        return bytes(c ^ mask[i % lmask] for i, c in enumerate(bytes_data))

    @classmethod
    def _version_decoder(cls, bytes_data: bytes) -> Optional[Version]:
        """
        新版本的版本解码器

        Args:
            bytes_data (bytes): _description_

        Returns:
            Optional[Version]: _description_
        """
        if cls.is_legacy_version(bytes_data):
            return Version.OLD
        bytes_data = bytes_data[:7]
        for mask in Version:
            lmask = len(mask)
            attempt = bytes(c ^ mask[i % lmask] for i, c in enumerate(bytes_data))
            if attempt == cls._VERSION_PREFIX:
                return mask

    @classmethod
    def parse_version(
        cls,
        buf: bytes,
        need_version: bool = False,
    ) -> Union[int, Tuple[int, Version]]:
        """解析版本

        Args:
            buf (bytes): _description_
            need_version (bool, optional): _description_. Defaults to False.

        Returns:
            Union[int, Tuple[int, Version]]: _description_
        """
        board_object_version = cls._version_decoder(buf)
        timestamp = 0
        if board_object_version is not None:
            fb = buf[7:15]
            if len(fb) == 8:
                timestamp = struct.unpack("d", fb)[0]
        if need_version:
            return timestamp, board_object_version
        return timestamp

    @classmethod
    def version_header_generator(cls, timestamp: float) -> bytes:
        """
        打包新的版本 + 时间戳(旧的版本)

        Args:
            timestamp (float): _description_

        Returns:
            bytes: _description_
        """
        return cls._version_encoder(cls._VERSION_PREFIX) + struct.pack("d", timestamp)

    @classmethod
    def serialize(cls, timestamp: float, data: object, compress: bool) -> bytes:
        """
        serialize data(Latest version)

        Args:
            data (object): data to serialize
            compress (bool): compress data or not

        Returns:
            bytes: serialized data
        """
        res = pickle.dumps(data, protocol=pickle.HIGHEST_PROTOCOL)
        res = zlib.compress(res) if compress else res
        return cls.version_header_generator(timestamp) + res

    @classmethod
    def deserialize(cls, package: bytes, compress: bool) -> "Serializable":
        """
        从压缩包中加载

        Args:
            package (bytes): 数据包
            compress (bool, optional): 是否压缩了. Defaults to True.

        Raises:
            ValueError: _description_

        Returns:
            BoardObject: _description_
        """
        timestamp, version = cls.parse_version(package, need_version=True)
        deserializer = cls._BOARD_OBJ_VERSION_DESERIALIZER_MAP.get(version)
        if deserializer is None:
            raise ValueError(f"unsupported version or Invalid package: {version}")
        obj = deserializer(cls, package, compress, timestamp)
        obj._serialization_version = version
        return obj
