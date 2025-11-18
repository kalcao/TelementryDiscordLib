import requests
import time
import random
from urllib.parse import urlparse

class Solver:
    def __init__(self, url, sitekey, rqdata="", user_agent="", proxy=None):
        """
        :param proxy: "user:password@host:port" 또는 "http://user:password@host:port"
        """
        self.url = url
        self.sitekey = sitekey
        self.rqdata = rqdata
        self.user_agent = user_agent
        self.proxy = proxy
        self.server_url = "http://localhost:5001"

    def _parse_proxy(self):
        """프록시 문자열을 srv, usr, pw 로 분해해서 반환"""
        if not self.proxy:
            return {}

        raw = self.proxy

        # 스킴이 없으면 http:// 자동 추가 (urlparse가 제대로 작동하게)
        if "://" not in raw:
            raw = "http://" + raw

        try:
            parsed = urlparse(raw)
        except Exception as e:
            print(f"[Proxy Parser] Invalid proxy({self.proxy}): {e}")
            return {}

        result = {}

        # hostname:port
        if parsed.hostname and parsed.port:
            result["srv"] = f"{parsed.hostname}:{parsed.port}"

        # username
        if parsed.username:
            result["usr"] = parsed.username

        # password
        if parsed.password:
            result["pw"] = parsed.password

        return result

    def solve(self, timeout=300, poll_interval=1):
        """
        서버로 GET /solve?url=...&sitekey=... 과 함께 proxy 정보도 보내서 작업 요청
        """
        params = {
            "url": self.url,
            "sitekey": self.sitekey,
            "rqdata": self.rqdata,
            "user_agent": self.user_agent,
        }

        # proxy 파싱해서 srv / usr / pw 추가
        proxy_params = self._parse_proxy()
        params.update(proxy_params)

        # 디버깅 출력
        print("[Solver] Sending parameters to server:")
        for k, v in params.items():
            print(f"  {k}: {v}")

        sess = requests.Session()

        # 세션 UA 설정
        if self.user_agent:
            sess.headers.update({"User-Agent": self.user_agent})

        # --- Solve START ---
        try:
            resp = sess.get(f"{self.server_url}/solve", params=params, timeout=30)
        except Exception as e:
            print(f"Error initiating solve: {e}")
            return None, None

        if resp.status_code != 200:
            body = resp.text if hasattr(resp, "text") else "<no body>"
            print(f"Error initiating solve: {resp.status_code} - {body}")
            return None, None

        # JSON 파싱
        try:
            data = resp.json()
        except Exception as e:
            print(f"Invalid JSON from server when initiating solve: {e}")
            return None, None

        taskid = data.get("taskid")
        if not taskid:
            print(f"Error: No taskid received - {data}")
            return None, None

        print(f"Task initiated: {taskid}")

        # --- Polling ---
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                poll_resp = sess.get(f"{self.server_url}/task/{taskid}", timeout=30)
            except Exception as e:
                print(f"Error checking task: {e}")
                time.sleep(poll_interval + random.uniform(0, 0.5))
                continue

            if poll_resp.status_code != 200:
                body = poll_resp.text if hasattr(poll_resp, "text") else "<no body>"
                print(f"Error checking task: {poll_resp.status_code} - {body}")
                time.sleep(poll_interval + random.uniform(0, 0.5))
                continue

            try:
                data = poll_resp.json()
            except Exception as e:
                print(f"Invalid JSON while polling task: {e}")
                time.sleep(poll_interval + random.uniform(0, 0.5))
                continue

            status = data.get("status")
            uuid = data.get("uuid")
            cookies = data.get("cookies", {})

            if status == "success":
                print(f"Task {taskid} solved successfully")
                return uuid, cookies

            if status == "failed":
                print(f"Task {taskid} failed")
                return None, None

            if status == "not_found":
                print(f"Task {taskid} not found")
                return None, None

            print(f"Task {taskid} status: {status} - Waiting...")
            time.sleep(poll_interval + random.uniform(0, 0.5))

        print(f"Timeout reached for task {taskid}")
        return None, None
