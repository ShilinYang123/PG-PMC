#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PG-Dev AI设计助理 - 加密工具
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding, rsa
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

from src.utils.logger import get_logger


@dataclass
class EncryptionConfig:
    """加密配置"""

    algorithm: str = "AES-256-GCM"
    key_derivation: str = "PBKDF2"
    iterations: int = 100000
    salt_length: int = 32
    iv_length: int = 16
    tag_length: int = 16


class EncryptionError(Exception):
    """加密相关异常"""

    pass


class SimpleEncryption:
    """简单加密工具（不依赖cryptography库）"""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    def generate_key(self, length: int = 32) -> bytes:
        """生成随机密钥

        Args:
            length: 密钥长度

        Returns:
            bytes: 随机密钥
        """
        return secrets.token_bytes(length)

    def hash_password(
        self, password: str, salt: Optional[bytes] = None
    ) -> Tuple[str, str]:
        """哈希密码

        Args:
            password: 明文密码
            salt: 盐值，如果为None则自动生成

        Returns:
            Tuple[str, str]: (哈希值, 盐值)
        """
        try:
            if salt is None:
                salt = secrets.token_bytes(32)

            # 使用PBKDF2进行密码哈希
            hash_value = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt, 100000  # 迭代次数
            )

            return (
                base64.b64encode(hash_value).decode("utf-8"),
                base64.b64encode(salt).decode("utf-8"),
            )

        except Exception as e:
            self.logger.error(f"密码哈希失败: {e}")
            raise EncryptionError(f"密码哈希失败: {e}")

    def verify_password(self, password: str, hash_value: str, salt: str) -> bool:
        """验证密码

        Args:
            password: 明文密码
            hash_value: 存储的哈希值
            salt: 盐值

        Returns:
            bool: 是否匹配
        """
        try:
            salt_bytes = base64.b64decode(salt.encode("utf-8"))
            expected_hash = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt_bytes, 100000
            )

            stored_hash = base64.b64decode(hash_value.encode("utf-8"))
            return hmac.compare_digest(expected_hash, stored_hash)

        except Exception as e:
            self.logger.error(f"密码验证失败: {e}")
            return False

    def simple_encrypt(self, data: str, key: str) -> str:
        """简单加密（XOR）

        Args:
            data: 待加密数据
            key: 密钥

        Returns:
            str: 加密后的数据（Base64编码）
        """
        try:
            # 扩展密钥以匹配数据长度
            key_bytes = key.encode("utf-8")
            data_bytes = data.encode("utf-8")

            # XOR加密
            encrypted = bytearray()
            for i, byte in enumerate(data_bytes):
                encrypted.append(byte ^ key_bytes[i % len(key_bytes)])

            return base64.b64encode(encrypted).decode("utf-8")

        except Exception as e:
            self.logger.error(f"简单加密失败: {e}")
            raise EncryptionError(f"简单加密失败: {e}")

    def simple_decrypt(self, encrypted_data: str, key: str) -> str:
        """简单解密（XOR）

        Args:
            encrypted_data: 加密数据（Base64编码）
            key: 密钥

        Returns:
            str: 解密后的数据
        """
        try:
            # 解码Base64
            encrypted_bytes = base64.b64decode(encrypted_data.encode("utf-8"))
            key_bytes = key.encode("utf-8")

            # XOR解密
            decrypted = bytearray()
            for i, byte in enumerate(encrypted_bytes):
                decrypted.append(byte ^ key_bytes[i % len(key_bytes)])

            return decrypted.decode("utf-8")

        except Exception as e:
            self.logger.error(f"简单解密失败: {e}")
            raise EncryptionError(f"简单解密失败: {e}")

    def generate_token(self, length: int = 32) -> str:
        """生成随机令牌

        Args:
            length: 令牌长度

        Returns:
            str: 随机令牌
        """
        return secrets.token_urlsafe(length)

    def hash_data(self, data: Union[str, bytes], algorithm: str = "sha256") -> str:
        """哈希数据

        Args:
            data: 待哈希的数据
            algorithm: 哈希算法

        Returns:
            str: 哈希值（十六进制）
        """
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")

            hash_obj = hashlib.new(algorithm)
            hash_obj.update(data)
            return hash_obj.hexdigest()

        except Exception as e:
            self.logger.error(f"数据哈希失败: {e}")
            raise EncryptionError(f"数据哈希失败: {e}")


class AdvancedEncryption:
    """高级加密工具（依赖cryptography库）"""

    def __init__(self, config: Optional[EncryptionConfig] = None):
        if not CRYPTOGRAPHY_AVAILABLE:
            raise EncryptionError("cryptography库未安装，无法使用高级加密功能")

        self.config = config or EncryptionConfig()
        self.logger = get_logger(self.__class__.__name__)

    def generate_key(self) -> bytes:
        """生成Fernet密钥

        Returns:
            bytes: Fernet密钥
        """
        return Fernet.generate_key()

    def derive_key_from_password(
        self, password: str, salt: Optional[bytes] = None
    ) -> Tuple[bytes, bytes]:
        """从密码派生密钥

        Args:
            password: 密码
            salt: 盐值，如果为None则自动生成

        Returns:
            Tuple[bytes, bytes]: (密钥, 盐值)
        """
        try:
            if salt is None:
                salt = os.urandom(self.config.salt_length)

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=self.config.iterations,
            )

            key = base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))
            return key, salt

        except Exception as e:
            self.logger.error(f"密钥派生失败: {e}")
            raise EncryptionError(f"密钥派生失败: {e}")

    def encrypt_data(self, data: Union[str, bytes], key: bytes) -> bytes:
        """加密数据

        Args:
            data: 待加密数据
            key: 加密密钥

        Returns:
            bytes: 加密后的数据
        """
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")

            fernet = Fernet(key)
            return fernet.encrypt(data)

        except Exception as e:
            self.logger.error(f"数据加密失败: {e}")
            raise EncryptionError(f"数据加密失败: {e}")

    def decrypt_data(self, encrypted_data: bytes, key: bytes) -> bytes:
        """解密数据

        Args:
            encrypted_data: 加密数据
            key: 解密密钥

        Returns:
            bytes: 解密后的数据
        """
        try:
            fernet = Fernet(key)
            return fernet.decrypt(encrypted_data)

        except Exception as e:
            self.logger.error(f"数据解密失败: {e}")
            raise EncryptionError(f"数据解密失败: {e}")

    def encrypt_file(
        self, file_path: Path, key: bytes, output_path: Optional[Path] = None
    ) -> Path:
        """加密文件

        Args:
            file_path: 源文件路径
            key: 加密密钥
            output_path: 输出文件路径，如果为None则在原文件名后添加.enc

        Returns:
            Path: 加密文件路径
        """
        try:
            if not file_path.exists():
                raise EncryptionError(f"文件不存在: {file_path}")

            if output_path is None:
                output_path = file_path.with_suffix(file_path.suffix + ".enc")

            with open(file_path, "rb") as f:
                data = f.read()

            encrypted_data = self.encrypt_data(data, key)

            with open(output_path, "wb") as f:
                f.write(encrypted_data)

            self.logger.info(f"文件加密完成: {file_path} -> {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"文件加密失败: {e}")
            raise EncryptionError(f"文件加密失败: {e}")

    def decrypt_file(
        self, encrypted_file_path: Path, key: bytes, output_path: Optional[Path] = None
    ) -> Path:
        """解密文件

        Args:
            encrypted_file_path: 加密文件路径
            key: 解密密钥
            output_path: 输出文件路径，如果为None则去掉.enc后缀

        Returns:
            Path: 解密文件路径
        """
        try:
            if not encrypted_file_path.exists():
                raise EncryptionError(f"加密文件不存在: {encrypted_file_path}")

            if output_path is None:
                if encrypted_file_path.suffix == ".enc":
                    output_path = encrypted_file_path.with_suffix("")
                else:
                    output_path = encrypted_file_path.with_suffix(".dec")

            with open(encrypted_file_path, "rb") as f:
                encrypted_data = f.read()

            decrypted_data = self.decrypt_data(encrypted_data, key)

            with open(output_path, "wb") as f:
                f.write(decrypted_data)

            self.logger.info(f"文件解密完成: {encrypted_file_path} -> {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"文件解密失败: {e}")
            raise EncryptionError(f"文件解密失败: {e}")

    def generate_rsa_keypair(self, key_size: int = 2048) -> Tuple[bytes, bytes]:
        """生成RSA密钥对

        Args:
            key_size: 密钥长度

        Returns:
            Tuple[bytes, bytes]: (私钥, 公钥)
        """
        try:
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=key_size,
            )

            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )

            public_key = private_key.public_key()
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )

            return private_pem, public_pem

        except Exception as e:
            self.logger.error(f"RSA密钥对生成失败: {e}")
            raise EncryptionError(f"RSA密钥对生成失败: {e}")

    def rsa_encrypt(self, data: bytes, public_key_pem: bytes) -> bytes:
        """RSA加密

        Args:
            data: 待加密数据
            public_key_pem: 公钥（PEM格式）

        Returns:
            bytes: 加密后的数据
        """
        try:
            public_key = serialization.load_pem_public_key(public_key_pem)

            encrypted = public_key.encrypt(
                data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )

            return encrypted

        except Exception as e:
            self.logger.error(f"RSA加密失败: {e}")
            raise EncryptionError(f"RSA加密失败: {e}")

    def rsa_decrypt(self, encrypted_data: bytes, private_key_pem: bytes) -> bytes:
        """RSA解密

        Args:
            encrypted_data: 加密数据
            private_key_pem: 私钥（PEM格式）

        Returns:
            bytes: 解密后的数据
        """
        try:
            private_key = serialization.load_pem_private_key(
                private_key_pem,
                password=None,
            )

            decrypted = private_key.decrypt(
                encrypted_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )

            return decrypted

        except Exception as e:
            self.logger.error(f"RSA解密失败: {e}")
            raise EncryptionError(f"RSA解密失败: {e}")


class SecureStorage:
    """安全存储"""

    def __init__(self, storage_path: Path, password: str):
        self.storage_path = Path(storage_path)
        self.password = password
        self.logger = get_logger(self.__class__.__name__)

        # 选择加密方式
        if CRYPTOGRAPHY_AVAILABLE:
            self.encryption = AdvancedEncryption()
        else:
            self.encryption = SimpleEncryption()
            self.logger.warning(
                "使用简单加密方式，建议安装cryptography库以获得更好的安全性"
            )

        # 确保存储目录存在
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _get_key(self) -> Union[bytes, str]:
        """获取加密密钥"""
        if CRYPTOGRAPHY_AVAILABLE:
            key, _ = self.encryption.derive_key_from_password(self.password)
            return key
        else:
            return self.password

    def store_data(self, key: str, data: Any) -> bool:
        """存储数据

        Args:
            key: 数据键
            data: 数据值

        Returns:
            bool: 是否成功
        """
        try:
            # 序列化数据
            json_data = json.dumps(data, ensure_ascii=False, indent=2)

            # 加密数据
            encryption_key = self._get_key()

            if CRYPTOGRAPHY_AVAILABLE:
                encrypted_data = self.encryption.encrypt_data(json_data, encryption_key)
                # 保存为二进制文件
                file_path = self.storage_path / f"{key}.enc"
                with open(file_path, "wb") as f:
                    f.write(encrypted_data)
            else:
                encrypted_data = self.encryption.simple_encrypt(
                    json_data, encryption_key
                )
                # 保存为文本文件
                file_path = self.storage_path / f"{key}.txt"
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(encrypted_data)

            self.logger.info(f"数据存储成功: {key}")
            return True

        except Exception as e:
            self.logger.error(f"数据存储失败: {e}")
            return False

    def load_data(self, key: str) -> Optional[Any]:
        """加载数据

        Args:
            key: 数据键

        Returns:
            Any: 数据值，如果不存在或解密失败则返回None
        """
        try:
            encryption_key = self._get_key()

            if CRYPTOGRAPHY_AVAILABLE:
                file_path = self.storage_path / f"{key}.enc"
                if not file_path.exists():
                    return None

                with open(file_path, "rb") as f:
                    encrypted_data = f.read()

                decrypted_data = self.encryption.decrypt_data(
                    encrypted_data, encryption_key
                )
                json_data = decrypted_data.decode("utf-8")
            else:
                file_path = self.storage_path / f"{key}.txt"
                if not file_path.exists():
                    return None

                with open(file_path, "r", encoding="utf-8") as f:
                    encrypted_data = f.read()

                json_data = self.encryption.simple_decrypt(
                    encrypted_data, encryption_key
                )

            # 反序列化数据
            data = json.loads(json_data)

            self.logger.info(f"数据加载成功: {key}")
            return data

        except Exception as e:
            self.logger.error(f"数据加载失败: {e}")
            return None

    def delete_data(self, key: str) -> bool:
        """删除数据

        Args:
            key: 数据键

        Returns:
            bool: 是否成功
        """
        try:
            if CRYPTOGRAPHY_AVAILABLE:
                file_path = self.storage_path / f"{key}.enc"
            else:
                file_path = self.storage_path / f"{key}.txt"

            if file_path.exists():
                file_path.unlink()
                self.logger.info(f"数据删除成功: {key}")
                return True
            else:
                self.logger.warning(f"数据不存在: {key}")
                return False

        except Exception as e:
            self.logger.error(f"数据删除失败: {e}")
            return False

    def list_keys(self) -> List[str]:
        """列出所有数据键

        Returns:
            List[str]: 数据键列表
        """
        try:
            keys = []

            if CRYPTOGRAPHY_AVAILABLE:
                pattern = "*.enc"
            else:
                pattern = "*.txt"

            for file_path in self.storage_path.glob(pattern):
                key = file_path.stem
                keys.append(key)

            return sorted(keys)

        except Exception as e:
            self.logger.error(f"列出数据键失败: {e}")
            return []

    def clear_all(self) -> bool:
        """清空所有数据

        Returns:
            bool: 是否成功
        """
        try:
            count = 0

            for pattern in ["*.enc", "*.txt"]:
                for file_path in self.storage_path.glob(pattern):
                    file_path.unlink()
                    count += 1

            self.logger.info(f"清空数据完成，删除了 {count} 个文件")
            return True

        except Exception as e:
            self.logger.error(f"清空数据失败: {e}")
            return False


# 全局实例
simple_encryption = SimpleEncryption()

if CRYPTOGRAPHY_AVAILABLE:
    advanced_encryption = AdvancedEncryption()
else:
    advanced_encryption = None


# 便捷函数
def hash_password(password: str) -> Tuple[str, str]:
    """哈希密码

    Args:
        password: 明文密码

    Returns:
        Tuple[str, str]: (哈希值, 盐值)
    """
    return simple_encryption.hash_password(password)


def verify_password(password: str, hash_value: str, salt: str) -> bool:
    """验证密码

    Args:
        password: 明文密码
        hash_value: 存储的哈希值
        salt: 盐值

    Returns:
        bool: 是否匹配
    """
    return simple_encryption.verify_password(password, hash_value, salt)


def generate_token(length: int = 32) -> str:
    """生成随机令牌

    Args:
        length: 令牌长度

    Returns:
        str: 随机令牌
    """
    return simple_encryption.generate_token(length)


def hash_data(data: Union[str, bytes], algorithm: str = "sha256") -> str:
    """哈希数据

    Args:
        data: 待哈希的数据
        algorithm: 哈希算法

    Returns:
        str: 哈希值（十六进制）
    """
    return simple_encryption.hash_data(data, algorithm)


def encrypt_data(data: str, key: str) -> str:
    """加密数据

    Args:
        data: 待加密数据
        key: 密钥

    Returns:
        str: 加密后的数据
    """
    return simple_encryption.simple_encrypt(data, key)


def decrypt_data(encrypted_data: str, key: str) -> str:
    """解密数据

    Args:
        encrypted_data: 加密数据
        key: 密钥

    Returns:
        str: 解密后的数据
    """
    return simple_encryption.simple_decrypt(encrypted_data, key)
