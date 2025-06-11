from copy import deepcopy
import time
import logging
_LOGGER = logging.getLogger(__name__)


class HiSenseLogin:
    def __init__(self, session):
        self.session = session
    
    def get_timestamp(self):
        return int(time.time() * 1000)

    async def login(self, username, password):
        timestamp = self.get_timestamp()
        url='https://portal-account.hismarttv.com/mobile/signon'
        headers = {
            'Content-Type': 'application/json;charset=utf-8',
        }
        data = {
            'pdateTime': '0',
            'version': '1.0',
            'deviceType': '2',
            'appType': '100',
            'versionCode': '101',
            'adaptertRank': '3098',
            'deviceType':'1',
            'distributeId':'2001',
            'loginName': username,
            'serverCode':'9501',
            'signature': password,
        }
        params = {
            'lastUpdateTime': '0',
            'version': '1.0',
            'deviceType': '2',
            'appType': '100',
            'versionCode': '101',
            'adaptertRank': '4130',
            '_': str(timestamp),
        }
        async with self.session.post(url, headers=headers, json=data, params=params) as response:
            result = await response.json()
            result_code = result["data"]["resultCode"]
            if result_code == 0:
                access_token = result["data"]["tokenInfo"]["token"]
                refresh_token = result["data"]["tokenInfo"]["refreshToken"]
                return access_token, refresh_token
            else:
                return None

    async def get_home_id_list(self, access_token):
        timestamp = self.get_timestamp()
        url='http://api.wg.hismarttv.com/wg/dm/getHomeList'
        
        headers = {
                'Host': 'api.wg.hismarttv.com',
                'Connection': 'Keep-Alive',
                'Accept-Encoding': 'gzip',
                'User-Agent': 'okhttp/4.10.0',
            }
        params = {
            'sign': '',
            'languageId': '0',
            'version': '8.0',
            'accessToken': access_token,   
            'timezone':'28800',
            'format': '1',
            'timeStamp': str(timestamp),
        }
        async with self.session.get(url, headers=headers, params=params) as response:
            result = await response.json()
            result_code = result["response"]["resultCode"]
            if result_code == 0:
                home_list = result["response"]["homeList"]
                home_id_list = []
                for home in home_list:
                    home_id_list.append(home["homeId"])
                return home_id_list
            else:
                return None
            
    async def get_device_wifi_id_dict(self, access_token, home_id, device_keywords="空调"):
        timestamp = self.get_timestamp()
        url='http://api-wg.hismarttv.com/wg/dm/getHomeDeviceList'
        headers = {
                'Host': 'api-wg.hismarttv.com',
                'Connection': 'Keep-Alive',
                'Accept-Encoding': 'gzip',
                'User-Agent': 'okhttp/4.10.0',
            }
        params = {
            'sign': '',
            'languageId': '0',
            'version': '8.0',
            'accessToken': access_token,   
            'homeId': home_id,
            'timezone':'28800',
            'format': '1',
            'timeStamp': str(timestamp),
        }
        async with self.session.get(url, headers=headers, params=params) as response:
            result = await response.json()
            result_code = result["response"]["resultCode"]
            if result_code == 0:
                device_list = result["response"]["deviceList"]
                device_wifi_id_dict = dict()
                for device in device_list:
                    device_type_name = device["deviceTypeName"]
                    if device_keywords in device_type_name:
                        device_wifi_id_dict[device["deviceId"]] = device["wifiId"]
                return device_wifi_id_dict
            else:
                return None


class HiSenseAC:
    def __init__(self, wifi_id, device_id, refresh_token, session):
        self.wifi_id = wifi_id
        mac_string=wifi_id[-12:]
        self.mac=':'.join(mac_string[i:i+2] for i in range(0, len(mac_string), 2))
        self.device_id = device_id
        self.refresh_token = refresh_token
        self.access_token = None
        self.session = session
        app_name_encoding = "%E6%B5%B7%E4%BF%A1%E6%99%BA%E6%85%A7%E5%AE%B6"
        # app_name = "海信智慧家"
        # app_name_encoding = urllib.parse.quote(app_name)
        self.headers = {
            'Host': 'api-wg.hismarttv.com',
            'Content-Type': 'application/json',
            'Connection': 'keep-alive',
            'Accept': '*/*',
            'User-Agent': f"{app_name_encoding}/4 CFNetwork/1492.0.1 Darwin/23.3.0",
            'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
        }
        self.refresh_headers = {
            'Host': 'bas-wg.hismarttv.com',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Connection': 'keep-alive',
            'Accept': '*/*',
            'User-Agent': f"{app_name_encoding}/4 CFNetwork/1492.0.1 Darwin/23.3.0",
            'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br'
        }
        self.url_head = "https://api-wg.hismarttv.com/agw/dsg/outer"
        self.power_url = f"{self.url_head}/sendDeviceModelCmd?accessToken="
        self.command_url = f"{self.url_head}/uploadRemoteLogicCmd?accessToken="
        self.check_url = f"{self.url_head}/getDeviceLogicalStatusArray?accessToken="
        self.refresh_url = "https://bas-wg.hismarttv.com/aaa/refresh_token2"
        self.power_data_template = {
            "wifiId": wifi_id,
            "deviceId": device_id,
            "extendParam": "1",
            "cmdVersion": "0",
        }
        self.check_data_template = {
            "deviceList": [
                {
                    "wifiId": wifi_id,
                    "deviceId": device_id,
                }
            ]
        }
        self.command_data_template = {
            "wifiId": wifi_id,
            "deviceId": device_id,
            "extendParm": "1",
            "cmdVersion": "1684085201",
        }
        self.status = {
            "power_on": False,
        }
        self.hvac_mode_lookup = {
            0: "FAN_ONLY",
            1: "HEAT",
            2: "COOL",
            3: "DRY",
            4: "AUTO",
        }
        self.fan_mode_lookup = {
            0: "AUTO",
            1: "DIFFUSE",
            2: "LOW",
            3: "MEDIUM",
            4: "HIGH",
        }

    async def _send_command(self, url, command_data):
        post_url = f"{url}{self.access_token}"
        async with self.session.post(post_url, headers=self.headers, json=command_data) as response:
            result = await response.json()
            result_code = result["response"]["resultCode"]
            if result_code == 0:
                self.__update(result)
                return True
            else:
                return False

    async def _robust_send_command(self, url, command_data):
        if not await self._send_command(url, command_data):
            _LOGGER.info("Attempting to refresh token and retry command")
            if await self.refresh():
                return await self._send_command(url, command_data)
            else:
                _LOGGER.error("Failed to refresh token")
                return False

    def __update(self, result):
        try:
            result_list_str = result["response"]["preStatus"]
        except KeyError:
            try:
                result_list_str = result["response"]["deviceStatusList"][0]["deviceStatus"]

            except KeyError:
                return False
        result_list = [int(i) for i in result_list_str.split(',')]
        self.status["desired_temperature"] = result_list[9]
        self.status["indoor_temperature"] = result_list[10]
        self.status["hvac_mode_id"] = result_list[4]
        self.status["hvac_mode"] = self.hvac_mode_lookup[self.status["hvac_mode_id"]]
        self.status["fan_mode_id"] = result_list[0]
        self.status["fan_mode"] = self.fan_mode_lookup[self.status["fan_mode_id"]]
        self.status["screen_on"] = result_list[58] == 1
        self.status["power_on"] = result_list[5] == 1
        self.status["aux_heat"] = result_list[45] == 1
        self.status["nature_wind"] = result_list[44] == 1
        self.status["swing_mode_id"] = result_list[209]
        # TODO  需要找到防直吹对应的index
        self.status["prevent_direct_wind"] = result_list[45] == 1

    async def turn_on(self):
        command_data = deepcopy(self.power_data_template)
        command_data["attributes"] = "{\"onAndOff\":\"On\"}"
        self.status["power_on"] = True
        await self._robust_send_command(self.power_url, command_data)
        _LOGGER.info("空调已开机")

    async def turn_off(self):
        command_data = deepcopy(self.power_data_template)
        command_data["attributes"] = "{\"onAndOff\":\"Off\"}"
        self.status["power_on"] = False
        await self._robust_send_command(self.power_url, command_data)

    async def send_logic_command(self, id: int, param: int):
        command_data = deepcopy(self.command_data_template)
        command_data["cmdList"] = [
            {"cmdId": id, "cmdOrder": 0, "cmdParm": param, "delayTime": 0}
        ]
        await self._robust_send_command(self.command_url, command_data)

    async def check_status(self):
        await self._robust_send_command(self.check_url, self.check_data_template)

    def get_status(self):
        return self.status

    async def refresh(self):
        refresh_data = {
            'refreshToken': self.refresh_token,
            'appKey': "1234567890",
            'format': '1',
        }
        try:
            async with self.session.post(self.refresh_url,
                                         headers=self.refresh_headers,
                                         data=refresh_data) as response:
                result = await response.json()
                self.access_token = result[0]["token"]
                _LOGGER.debug(f"Get access token: {self.access_token}")
                return True
        except:
            _LOGGER.error("Failed to refresh token")
            return False
