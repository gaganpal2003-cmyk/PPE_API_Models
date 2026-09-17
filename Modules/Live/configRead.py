import configparser


class ConfigData:
    def __init__(self, cur_path):
        try:
            config = configparser.ConfigParser()
            config.optionxform = str
            conf_path = f"{cur_path}/config/settings.ini"
            self.conf_path = conf_path
            config.read(str(conf_path))
            self.telegramTokenId = config.get("TELEGRAM", "APITOKEN")
            self.telegramChatId = config.get("TELEGRAM", "CHAT_ID")
            self.dbPath = config.get("MYSQL_DB_NAME", "DB_NAME")
            self.personModelPath = config.get("MODEL", "PERSON_MODEL")
            self.PPEModelPath = config.get("MODEL", "PPE_MODEL")
            self.threshold = config.get("THRESHOLD", "MIN_THRESHOLD")
            self.PPEthreshold = config.get("THRESHOLD", "PPE_THRESHOLD")
            self.cocoPath = config.get("COCO_PATH", "CLASS_FILE")
            self.objectList = config.get("OBJECTS", "TARGET_OBJECTS")
            self.impPPEList = config.get("OBJECTS", "IMP_PPE")
            self.liveFrameResolution = config.get("LIVE_FRAME_RESOLUTION", "WIDTH_AND_HEIGHT")
            self.defaultGif = config.get("DEFAULT_POPUP_GIF", "DEFAULT_GIF")
            self.detectedDataPath = config.get("DETECTED_DATA", "DETECTED_DATA_PATH")
            self.timeChunkToSaveFrame = config.get("TIME_CHUNKS", "TIME_LIMIT")
            self.handle_frame_skip = config.get("HANDLE FRAME", "FRAME_SKIP")
            self.max_len = config.get("PREVIOUS_FRAME_STORAGE", "MAX_LEN")
            self.time_duration_video_record = config.get("TIME_DURATION_VIDEO_RECORD", "TIME")
            self.record_video_resolution = config.get("RECORD_VIDEO_RESOLUTION", "SCALE")
        except Exception as e:
            raise e

    def get_db_name(self):
        return self.dbPath

    def get_person_model_path(self):
        return self.personModelPath

    def get_threshold(self):
        return self.threshold

    def get_coco_path(self):
        return self.cocoPath

    def get_object_list(self):
        return self.objectList

    def get_frame_resolution(self):
        return self.liveFrameResolution

    def get_default_gif(self):
        return self.defaultGif

    def get_detected_frame_path(self):
        return self.detectedDataPath

    def get_time_chunks(self):
        return self.timeChunkToSaveFrame

    def get_telegram_token_id(self):
        return self.telegramTokenId

    def get_telegram_chat_id(self):
        return self.telegramChatId

    def get_ppe_model_path(self):
        return self.PPEModelPath

    def get_imp_ppe_name(self):
        return self.impPPEList

    def get_ppe_threshold(self):
        return self.PPEthreshold

    def get_skip_handle_frame(self):
        return self.handle_frame_skip

    def get_max_len_for_previous_frame(self):
        return self.max_len

    def get_time_duration_video_record(self):
        return self.time_duration_video_record

    def get_record_video_resolution(self):
        return self.record_video_resolution

    def _update_ini_setting(self, section, key, value):
        import re
        try:
            with open(self.conf_path, 'r', encoding='utf-8') as f:
                content = f.read()

            sec_pattern = re.compile(rf'^\[{re.escape(section)}\]', re.MULTILINE)
            sec_match = sec_pattern.search(content)

            if sec_match:
                next_sec = re.search(r'^\[', content[sec_match.end():], re.MULTILINE)
                end_pos = sec_match.end() + next_sec.start() if next_sec else len(content)
                sec_body = content[sec_match.end():end_pos]

                key_pattern = re.compile(rf'^{re.escape(key)}\s*=.*$', re.MULTILINE)
                if key_pattern.search(sec_body):
                    new_sec_body = key_pattern.sub(f'{key} = {value}', sec_body)
                    content = content[:sec_match.end()] + new_sec_body + content[end_pos:]
                else:
                    if not sec_body.endswith('\n'):
                        content = content[:end_pos] + f'\n{key} = {value}\n' + content[end_pos:]
                    else:
                        content = content[:end_pos] + f'{key} = {value}\n' + content[end_pos:]
            else:
                if not content.endswith('\n'):
                    content += '\n'
                content += f'\n[{section}]\n{key} = {value}\n'

            with open(self.conf_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            print(f"Error updating ini setting [{section}] {key}:", e)

    def get_last_camera(self):
        try:
            config = configparser.ConfigParser()
            config.optionxform = str
            config.read(str(self.conf_path))
            if config.has_section("ACTIVE_CAMERA"):
                return config.get("ACTIVE_CAMERA", "LAST_CAMERA", fallback="").strip()
        except Exception as e:
            print("Error reading last camera:", e)
        return ""

    def set_last_camera(self, camera_name):
        self._update_ini_setting("ACTIVE_CAMERA", "LAST_CAMERA", str(camera_name).strip())

    def get_active_cameras(self):
        try:
            config = configparser.ConfigParser()
            config.optionxform = str
            config.read(str(self.conf_path))
            if config.has_section("ACTIVE_CAMERA"):
                cams = config.get("ACTIVE_CAMERA", "ACTIVE_CAMERAS", fallback="").strip()
                if cams:
                    return [c.strip() for c in cams.split(",") if c.strip()]
        except Exception as e:
            print("Error reading active cameras:", e)
        return []

    def set_active_cameras(self, camera_names):
        if isinstance(camera_names, (list, tuple, set)):
            cams_str = ",".join(str(c).strip() for c in camera_names if str(c).strip())
        else:
            cams_str = str(camera_names).strip()
        self._update_ini_setting("ACTIVE_CAMERA", "ACTIVE_CAMERAS", cams_str)

