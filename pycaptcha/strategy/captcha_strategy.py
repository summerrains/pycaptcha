#!/usr/bin/env python
from __future__ import annotations

__author__ = "summerrains"

import random

from pycaptcha.config import SimpleCaptchaConfig, BlockPuzzleCaptchaConfig, ClickWordCaptchaConfig
from pycaptcha.strategy.block_puzzle_captcha import BlockPuzzleCaptcha
from pycaptcha.strategy.click_word_captcha import ClickWordCaptcha
from pycaptcha.strategy.simple_captcha import SimpleCaptcha
from pycaptcha.utils.redis_util import RedisUtil


class CaptchaStrategy:

    def __init__(self,redis=None,simpleConfigs: SimpleCaptchaConfig = SimpleCaptchaConfig,
                 blockConfigs: BlockPuzzleCaptchaConfig = BlockPuzzleCaptchaConfig,
                 clickConfigs: ClickWordCaptchaConfig = ClickWordCaptchaConfig):
        self.redis = redis
        if redis is not None and isinstance(redis, str):
            self.redis = RedisUtil(None,redis)
        else:
            self.redis = RedisUtil(redis,None)
        #
        self.simpleConfigs = simpleConfigs
        self.blockConfigs = blockConfigs
        self.clickConfigs = clickConfigs
        #

    def get_simple_captcha(self) -> dict:
        simpleCaptcha = SimpleCaptcha(self.redis,self.simpleConfigs)
        data = simpleCaptcha.get()
        print("{}_{}".format(data.get("token"),data.get("data")))
        data.update({'data': None})
        return data

    def get_block_captcha(self) -> dict:
        blockPuzzleCaptcha = BlockPuzzleCaptcha(self.redis, self.blockConfigs)
        data = blockPuzzleCaptcha.get()
        print("{}_{}".format(data.get("token"), data.get("data")))
        data.update({'data': None})
        return data

    def get_click_captcha(self) -> dict:
        clickWordCaptcha = ClickWordCaptcha(self.redis, self.clickConfigs)
        data = clickWordCaptcha.get()
        print("{}_{}".format(data.get("token"), data.get("data")))
        data.update({'data': None})
        return data

    def get_captcha(self) -> dict:
        n = random.randint(0, 1000)
        if n % 2 == 0:
            data = self.get_block_captcha()
        else:
            data = self.get_click_captcha()
        data.update({'data': None})
        return {
            'id': data.get('token'),
            'captcha': data,
        }

    def verify(self,token=None,params:list=None) -> str | None:
        '''
        verify code
        :param token:
        :param params: BlockPuzzleCaptcha is [{'x':x,'y':y}] ,ClickWordCaptcha is ['x':x1,'y':y1,'x':x2,'y':y2] , SimpleCaptcha is [{'code':code}]
        :return: return captcha_id if verify success , else return None
        '''
        prefix = token.split("-")[0]
        #
        if prefix == SimpleCaptcha.__CAPTCHA_TYPE__:
            simpleCaptcha = SimpleCaptcha(self.redis, self.simpleConfigs)
            return simpleCaptcha.verify(token, params[0])
        #
        if prefix == BlockPuzzleCaptcha.__CAPTCHA_TYPE__:
            blockPuzzleCaptcha = BlockPuzzleCaptcha(self.redis, self.blockConfigs)
            return blockPuzzleCaptcha.verify(token,params[0])
        #
        if prefix == ClickWordCaptcha.__CAPTCHA_TYPE__:
            clickWordCaptcha = ClickWordCaptcha(self.redis, self.clickConfigs)
            return clickWordCaptcha.verify(token,params)
        #
        return None


    def second_verify(self,captcha_id) -> bool:
        prefix = captcha_id.split("-")[0]
        #
        if prefix == BlockPuzzleCaptcha.__CAPTCHA_TYPE__:
            blockPuzzleCaptcha = BlockPuzzleCaptcha(self.redis, self.blockConfigs)
            return blockPuzzleCaptcha.second_verify(captcha_id)
        #
        if prefix == ClickWordCaptcha.__CAPTCHA_TYPE__:
            clickWordCaptcha = ClickWordCaptcha(self.redis, self.clickConfigs)
            return clickWordCaptcha.second_verify(captcha_id)
        #
        simpleCaptcha = SimpleCaptcha(self.redis, self.simpleConfigs)
        return simpleCaptcha.second_verify(captcha_id)
