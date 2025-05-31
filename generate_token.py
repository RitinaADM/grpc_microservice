from src.infra.auth.jwt_utils import JWTUtils

if __name__ == "__main__":
    jwt_utils = JWTUtils()
    token = jwt_utils.create_token({"user_id": "test-user"})
    print(f"Generated JWT: {token}")