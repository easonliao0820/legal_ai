import requests
import urllib3
from typing import Dict, List, Optional, Any

class JudicialOpenDataAPI:
    """
    司法院開放資料 API 整合客戶端 (Judicial Yuan Open Data API Client)
    """
    
    BASE_URL_DATA = "https://opendata.judicial.gov.tw/data/api/rest"
    BASE_URL_API = "https://opendata.judicial.gov.tw/api"
    
    def __init__(self, member_account: str = 'easonliao', pwd: str = 'easonliao940820', verify_ssl: bool = False):
        self.member_account = member_account
        self.pwd = pwd
        self.token = None
        self.token_expires = None
        self.verify_ssl = verify_ssl
        
        if not self.verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # 若有提供帳號密碼，則自動嘗試登入
        if self.member_account and self.pwd:
            self.authenticate()

    def _get_headers(self) -> Dict[str, str]:
        """產生 Requests 所需的 Headers，若有 Token 則自動加入 Bearer 授權"""
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        return headers

    # ==========================================
    # (3) 取得會員授權 Token (Authentication)
    # ==========================================
    def authenticate(self, member_account: str = 'easonliao', pwd: str = 'easonliao940820') -> Dict[str, Any]:
        """
        (3-1) 使用 HTTP POST 方法到網址取得授權 Token
        """
        account = member_account or self.member_account
        password = pwd or self.pwd
        
        if not account or not password:
            raise ValueError("必須提供 memberAccount 與 pwd 才能取得 Token")
            
        url = f"{self.BASE_URL_API}/MemberTokens"
        payload = {
            "memberAccount": account,
            "pwd": password
        }
        
        response = requests.post(
            url, 
            json=payload, 
            headers={'Content-Type': 'application/json'},
            verify=self.verify_ssl
        )
        data = response.json()
        
        if response.status_code == 200 and "token" in data:
            self.token = data["token"]
            self.token_expires = data.get("expires")
            return data
        else:
            # 失敗時可能會回傳 {"succeeded": false, "message": "帳號或密碼錯誤!"}
            raise Exception(f"認證失敗: {data.get('message', '未知錯誤')}")

    # ==========================================
    # (1) 取得主題分類清單 (Categories)
    # ==========================================
    def get_categories(self) -> List[Dict[str, str]]:
        """
        (1-1) 基本查詢: 取得全部司法院主題分類清單
        回傳範例: [{"categoryNo": "001", "categoryName": "其他"}, ...]
        """
        url = f"{self.BASE_URL_DATA}/categories"
        response = requests.get(url, headers=self._get_headers(), verify=self.verify_ssl)
        response.raise_for_status()
        return response.json()

    def get_category_resources(self, category_no: str) -> List[Dict[str, Any]]:
        """
        (1-2) 進階查詢: 指定主題分類代碼取得資料源清單
        回傳欄位包含 datasetId, title, categoryName, filesets 等
        """
        url = f"{self.BASE_URL_DATA}/categories/{category_no}/resources"
        response = requests.get(url, headers=self._get_headers(), verify=self.verify_ssl)
        response.raise_for_status()
        return response.json()

    # ==========================================
    # (2) 以 URL 存取資料 (File Access)
    # ==========================================
    def get_file(self, file_set_id: str, top: Optional[int] = None, skip: Optional[int] = None) -> Any:
        """
        (2-1) 基本查詢 / (2-2) 進階查詢: 取出指定資料源的結果
        - top: 取得前資料筆數 (選填)
        - skip: 跳過資料筆數 (選填)
        備註: top 與 skip 目前只支援 CSV, JSON, XML 檔案格式
        """
        url = f"{self.BASE_URL_API}/FilesetLists/{file_set_id}/file"
        params = {}
        if top is not None:
            params['top'] = top
        if skip is not None:
            params['skip'] = skip
            
        response = requests.get(url, params=params, headers=self._get_headers(), verify=self.verify_ssl)
        response.raise_for_status()
        
        # 如果回傳是 JSON 格式，直接解析為 dict/list
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' in content_type:
            return response.json()
        
        # 否則回傳原始二進位內容
        return response.content

# 測試範例 (供參考)
if __name__ == "__main__":
    # 初始化 API 客戶端
    api = JudicialOpenDataAPI()
    
    print("--- (1-1) 取得主題分類 ---")
    categories = api.get_categories()
    print(categories[:2]) # 印出前兩筆
    
    print("\n--- (1-2) 取得特定分類資料源清單 ---")
    resources = api.get_category_resources(category_no="001")
    print(resources[:1]) # 印出第一筆
    
    # 若需用到需要驗證的 API 或操作 Token:
    # api.authenticate(member_account="YOUR_ACCOUNT", pwd="YOUR_PASSWORD")
    # file_data = api.get_file(file_set_id="1038", top=10)
