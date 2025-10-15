import urllib.parse

import requests

from .oauth import OAuth, OAuthUserInfo


class GithubOAuth(OAuth):
    """GithubOAuth第三方授权认证类"""
    _AUTHORIZE_URL = "https://github.com/login/oauth/authorize"  # 跳转授权接口
    _ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"  # 获取授权令牌接口
    _USER_INFO_URL = "https://api.github.com/user"  # 获取用户信息接口
    _EMAIL_INFO_URL = "https://api.github.com/user/emails"  # 获取用户邮箱接口

    def get_provider(self) -> str:
        return "github"

    def get_authorization_url(self) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "user:email",  # 请求用户基本信息和邮箱访问权限
        }
        return f"{self._AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"

    def get_access_token(self, code: str) -> str:
        # 1.组装请求数据
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
        }
        headers = {"Accept": "application/json"}

        # 2.发起post请求并获取相应的数据
        resp = requests.post(self._ACCESS_TOKEN_URL, data=data, headers=headers)
        resp.raise_for_status()
        resp_json = resp.json()

        # 3.提取access_token对应的数据
        access_token = resp_json.get("access_token")
        if not access_token:
            raise ValueError(f"Github OAuth授权失败: {resp_json}")

        return access_token

    def get_raw_user_info(self, token: str) -> dict:
        # 1.组装请求数据
        headers = {"Authorization": f"token {token}"}

        # 2.发起get请求获取用户数据
        resp = requests.get(self._USER_INFO_URL, headers=headers)
        resp.raise_for_status()
        raw_info = resp.json()

        # 3.尝试多种方式获取用户邮箱
        email = None
        
        # 首先尝试从用户公开信息中获取邮箱
        if raw_info.get("email"):
            email = raw_info.get("email")
        
        # 如果公开信息中没有邮箱，则尝试通过/user/emails接口获取
        if not email:
            try:
                email_resp = requests.get(self._EMAIL_INFO_URL, headers=headers)
                email_resp.raise_for_status()
                email_info = email_resp.json()

                # 提取主邮箱地址
                primary_email = next((email for email in email_info if email.get("primary", None)), None)
                if primary_email:
                    email = primary_email.get("email")
                    
                # 如果没有主邮箱但有邮箱列表，使用第一个邮箱
                if not email and email_info:
                    email = email_info[0].get("email")
            except requests.exceptions.RequestException:
                # 如果无法通过API获取邮箱，继续使用其他方式
                pass

        # 确保至少有一个邮箱地址
        if not email:
            # 生成默认的GitHub noreply邮箱
            email = f"{raw_info.get('id')}+{raw_info.get('login')}@users.noreply.github.com"

        return {**raw_info, "email": email}

    def _transform_user_info(self, raw_info: dict) -> OAuthUserInfo:
        # 1.提取邮箱，如果不存在设置一个默认邮箱
        email = raw_info.get("email")
        # 不再需要检查邮箱是否存在，因为get_raw_user_info已经确保有邮箱
        
        # 2.组装数据
        return OAuthUserInfo(
            id=str(raw_info.get("id")),
            name=str(raw_info.get("name")) if raw_info.get("name") else str(raw_info.get("login")),
            email=str(email),
        )