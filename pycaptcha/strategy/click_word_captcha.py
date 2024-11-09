#!/usr/bin/env python
from __future__ import annotations

__author__ = "summerrains"

import base64
import os
import json
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

from pycaptcha import BASE_DIR
from pycaptcha.strategy.simple_captcha import SimpleCaptcha
from pycaptcha.utils.image_util import ImageUtil, open_image, image_to_rgba, set_art_text
from pycaptcha.utils.ramdom_util import generate_random_int, generate_random_background_color
from pycaptcha.utils.uuid_util import generate_uuid
from pycaptcha.config import ClickWordCaptchaConfig


class ClickWordCaptcha:
    """ 点击文字行为验证码 """

    __CAPTCHA_TYPE__ = "WORD_IMAGE_CLICK"

    base64_image_prefix = "data:image/jpeg;base64,{data}"
    base64_image_prefix_png = "data:image/png;base64,{data}"
    base64_image__type = "png"
    _data_encoding = "utf-8"

    def __init__(self, redis=None, configs: ClickWordCaptchaConfig = ClickWordCaptchaConfig) -> None:
        self.redis = redis
        self.background_image_list = list()
        self.__init_configs(configs)
        self.set_up()

    def __init_configs(self, configs: ClickWordCaptchaConfig = ClickWordCaptchaConfig) -> None:
        if not configs:
            self.click_word_captcha_cache_key = ClickWordCaptchaConfig.click_word_captcha_cache_key
            self.click_word_captcha_cache_key_expire = ClickWordCaptchaConfig.click_word_captcha_cache_key_expire
            self.font_ttf_root_path = ClickWordCaptchaConfig.font_ttf_root_path
            self.click_word_captcha_font_number = ClickWordCaptchaConfig.click_word_captcha_font_number
            self.click_word_captcha_text = ClickWordCaptchaConfig.click_word_captcha_text
            self.click_word_captcha_font_size = ClickWordCaptchaConfig.click_word_captcha_font_size
            self.background_image_root_path = ClickWordCaptchaConfig.background_image_root_path
        self.click_word_captcha_cache_key = configs.click_word_captcha_cache_key
        self.click_word_captcha_cache_key_expire = configs.click_word_captcha_cache_key_expire
        self.font_ttf_root_path = configs.font_ttf_root_path
        self.click_word_captcha_font_number = configs.click_word_captcha_font_number
        self.click_word_captcha_text = configs.click_word_captcha_text
        self.click_word_captcha_font_size = configs.click_word_captcha_font_size
        self.background_image_root_path = configs.background_image_root_path
        return None

    def set_up(self) -> None:
        backgroundImageRoot = self.get_resources(self.background_image_root_path)

        def process_file(res, path, info=None, err=None):
            if os.path.isdir(path):
                return
            res.append(path)

        for root, dirs, files in os.walk(backgroundImageRoot):
            for file in files:
                path = os.path.join(root, file)
                process_file(self.background_image_list, path)
        return None

    def get_resources(self, path_str: str) -> os.path:
        return os.path.join(BASE_DIR, path_str)

    def get_background_image(self) -> ImageUtil:
        max = len(self.background_image_list) - 1
        if max <= 0:
            max = 1
        src = self.background_image_list[generate_random_int(0, max)]
        src_image = open_image(src)
        image_util_obj = ImageUtil(
            src=src,
            src_image=src_image,
            rgba_image=image_to_rgba(src_image),
            width=src_image.size[0],
            height=src_image.size[1],
            font_path=self.get_resources(self.font_ttf_root_path),
        )
        return image_util_obj

    def get_random_words(self, word_count: int) -> list:
        word_list = []
        word_set = set()
        list_words = list(self.click_word_captcha_text)
        length = len(list_words)
        while True:
            word = list_words[generate_random_int(0, length - 1)]
            word_set.add(word)
            if len(word_set) >= word_count:
                for w in word_set:
                    word_list.append(w)
                break
        return word_list

    def random_word_points(self, width: int, height: int, i: int, count: int) -> dict:
        avg_width = width / (count + 1)
        font_size_half = self.click_word_captcha_font_size / 2
        x = y = 0
        if avg_width < font_size_half:
            x = generate_random_int(int(1+font_size_half), int(width))
        else:
            if i == 0:
                x = generate_random_int(int(1+font_size_half), int(avg_width*(i+1)-font_size_half))
            else:
                x = generate_random_int(int(avg_width*i+font_size_half), int(avg_width*(i+1)-font_size_half))
        y = generate_random_int(int(self.click_word_captcha_font_size), int(height-font_size_half))
        return {"x": x, "y": y}

    def get_image_data(self, background_image: ImageUtil) -> tuple:
        word_count = self.click_word_captcha_font_number
        if word_count < 6:
            word_count += 6
        # nums 要排除的
        nums = []
        while True:
            if len(nums) == word_count - 4:
                break
            num = generate_random_int(0, word_count-1)
            #
            exists = False
            for n in nums:
                if n == num:
                    exists = True
                    break
            if not exists:
                nums.append(num)
        #
        current_words = self.get_random_words(word_count)

        points_list = []
        word_list = []

        i = 0
        for _, word in enumerate(current_words):
            point = self.random_word_points(background_image.width, background_image.height, i, word_count)
            set_art_text(background_image, word, self.click_word_captcha_font_size, point,generate_random_background_color())

            exists = False
            for n in nums:
                if n == i:
                    exists = True
                    break
            if not exists:
                points_list.append(point)
                word_list.append(word)

            i = i+1

        return points_list, word_list

    def get_cache_key(self, token: str) -> str:
        return f"{self.click_word_captcha_cache_key}:{token}"

    def generate_background_size_picture(self,width: int = 120, height: int = 35) -> Image:
        """ 生成制定大小背景图 """
        return Image.new('RGB', (width, height), (255,255,255))

    def get_template_image(self,font_size: int = 35, word_list: list = None, width: int = 286, height: int = 76):
        """ 提示文字 """
        im = self.generate_background_size_picture(width, height)
        dio = ImageDraw.Draw(im)
        font_family = ImageFont.truetype(SimpleCaptcha.get_font_size_resource(), size=font_size)
        temp = []
        for i in range(len(word_list)):
            random_code_str = word_list[i]
            dio.text((10 + i * 66, 0), random_code_str, (128,128,128), font=font_family)
            temp.append(random_code_str)
        #
        im = SimpleCaptcha.noise(im,width,height,20,50)
        # 转base64
        f = BytesIO()
        im.save(f, self.base64_image__type)
        data = f.getvalue()
        f.close()
        encode_data = base64.b64encode(data)
        data = str(encode_data, encoding=self._data_encoding)
        return self.base64_image_prefix_png.format(data=data)

    def get(self) -> dict:
        background_image = self.get_background_image()
        points_list, word_list = self.get_image_data(background_image=background_image)
        #
        originalImageBase64 = background_image.base64_encode_image(background_image.rgba_image)
        templateImageWidth = 286
        templateImageHeight = 76
        jigsawImageBase64 = self.get_template_image(60,word_list,templateImageWidth,templateImageHeight)
        #
        result = {
            "type": ClickWordCaptcha.__CAPTCHA_TYPE__,
            'backgroundImageWidth': background_image.width,
            'backgroundImageHeight': background_image.height,
            'templateImageWidth': templateImageWidth,
            'templateImageHeight': templateImageHeight,
            'token': "{}-{}".format(ClickWordCaptcha.__CAPTCHA_TYPE__,generate_uuid()),
            'data': points_list,
            'backgroundImage': self.base64_image_prefix.format(data=originalImageBase64),
            'templateImage': jigsawImageBase64,
            'backgroundImageTag':'default',
            'templateImageTag':'default',
        }
        #
        cache_key = self.get_cache_key(result["token"])
        self.redis.set(cache_key, json.dumps(points_list), self.click_word_captcha_cache_key_expire)
        return result

    def check(self, token: str, point_jsons: list) -> bool:
        cache_key = self.get_cache_key(token)
        cache_value_bytes = self.redis.get(cache_key)
        if not cache_value_bytes:
            return False

        cache_value = json.loads(cache_value_bytes.decode(self._data_encoding))

        for index, point in enumerate(cache_value):
            target_point = point_jsons[index]
            font_size = self.click_word_captcha_font_size
            if (
                target_point.get("x")-font_size > point.get("x") or
                target_point.get("x") > point.get("x")+font_size or
                target_point.get("y")-font_size > point.get("y") or
                target_point.get("y") > point.get("y")+font_size
            ):
                return False
        return True

    def second_verify(self,captcha_id) -> bool:
        '''
        verify captcha_id
        :param captcha_id: the value of function verify return
        :return: return true if verify success
        '''
        captcha_id = captcha_id or ""
        cache_key = self.get_cache_key(captcha_id)
        cache_value_bytes = self.redis.get(cache_key)
        if not cache_value_bytes:
            return False
        self.redis.delete(cache_key)
        return True

    def verify(self, token: str, point_jsons: list) -> str | None:
        '''
        verify click, x and y offset in 25
        :param params:
        :return: return captcha_id if verify success , else return None
        '''
        flag = self.check(token, point_jsons)
        if not flag:
            return None
        cache_key = self.get_cache_key(token)
        self.redis.delete(cache_key)
        # create captcha_id
        captcha_id = "{}-{}".format(ClickWordCaptcha.__CAPTCHA_TYPE__,generate_uuid())
        cache_key = self.get_cache_key(captcha_id)
        self.redis.setex(cache_key, token, self.click_word_captcha_cache_key_expire)
        return captcha_id
