import bcrypt

def hash_password(plain_password: str) -> bytes:
    """
    生成密码的 bcrypt 哈希值（bytes 类型）
    :param plain_password: 明文密码（字符串）
    :return: 加密后的哈希值（bytes）
    """
    # 1. 将字符串密码转为字节码（bcrypt 要求输入为 bytes）
    password_bytes = plain_password.encode("utf-8")
    
    # 2. 生成盐值（自动生成，rounds=12 为默认强度，可调整 4-31 之间）
    salt = bcrypt.gensalt(rounds=12)  # rounds 越大，哈希越慢，安全性越高
    
    # 3. 生成哈希值（盐值已嵌入哈希结果中）
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    
    return hashed_bytes

def verify_password(plain_password: str, stored_hash: bytes) -> bool:
    """
    验证明文密码与存储的哈希值是否匹配
    :param plain_password: 用户输入的明文密码（字符串）
    :param stored_hash: 数据库中存储的哈希值（bytes 类型）
    :return: 匹配返回 True，否则 False
    """
    # 1. 明文密码转为字节码
    password_bytes = plain_password.encode("utf-8")
    
    # 2. 验证：bcrypt 自动从 stored_hash 中提取盐值，用相同盐值哈希明文后比对
    return bcrypt.checkpw(password_bytes, stored_hash)