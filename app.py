
from flask import Flask, make_response, json, request

from pycaptcha.strategy.captcha_strategy import CaptchaStrategy

app = Flask(__name__)

redis_url = 'redis://localhost:6379/0'

captchaStrategy = CaptchaStrategy(redis_url)

# 获取请求参数
def get_request_params(request):
    params_dict = {}
    # 从QueryString取
    try:
        params_dict.update(dict(request.args))
    except Exception as e:
        # logger.error("read data from form error")
        pass
    # 从form读取
    try:
        params_dict.update(dict(request.form))
    except Exception as e:
        # logger.error("read data from form error")
        pass
    # 从json中取
    try:
        params_dict.update(request.get_json())
    except Exception as e:
        # logger.error("read data from json error")
        pass
    #
    return params_dict

# 响应数据返回给前端，data可以是字典或类对象
def response(data_dict, status=200):
    resp = make_response(json.dumps(data_dict, ensure_ascii=False),status)
    resp.headers['Content-Type'] = 'application/json'
    return resp

@app.route('/api/auth/captcha/gen', methods=['POST','GET'])
def gen():  # put application's code here
    data = captchaStrategy.get_captcha()
    #
    return response(data)

@app.route('/api/auth/captcha/login', methods=['POST','GET'])
def login():  # put application's code here
    params_dict = get_request_params(request)
    captcha_id = params_dict.get('captcha_id')
    result = captchaStrategy.second_verify(captcha_id)
    if result:
        return response({'code':200,'message':'登录成功'})
    else:
        return response({'code':500,'message':'登录失败'})

@app.route('/api/auth/captcha/check', methods=['POST'])
def check():
    params_dict = get_request_params(request)
    token = params_dict.get('id')
    data = params_dict.get('data')
    track_list = data.get("trackList")
    if token is None or data is None or track_list is None or not isinstance(track_list,list):
        return response({'code':500,'message':'人机验证失败'})
    #
    points = []
    for track in track_list:
        if 'type' not in track:
            continue
        type = track.get('type')
        if type == 'up' or type == 'click':
            points.append({'x':track.get('x'),'y':track.get('y')})
    #
    if len(points) == 0:
        return response({'code': 500, 'message': '人机验证失败'})
    #
    captcha_id = captchaStrategy.verify(token,points)
    #
    if captcha_id is None:
        return response({'code': 500, 'message': '人机验证失败'})
    #
    return response({'code': 200, 'message': '人机验证通过','data':{'id':captcha_id,'success':True}})



if __name__ == '__main__':
    app.run()
