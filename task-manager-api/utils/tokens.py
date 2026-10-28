from itsdangerous import URLSafeTimedSerializer

LOGIN_TOKEN_SALT = "login-token"


def issue_login_token(user_id, secret_key):
    """Token opaco para o cliente, assinado com a SECRET_KEY: não dá para forjá-lo para outro id."""
    return URLSafeTimedSerializer(secret_key, salt=LOGIN_TOKEN_SALT).dumps({"uid": user_id})
