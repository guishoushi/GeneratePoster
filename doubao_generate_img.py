import random

import requests
from DrissionPage import ChromiumPage, ChromiumOptions
import time
import os
import base64
from datetime import datetime
from add_logo import add_logo_to_poster


def generate_img(data):
    # print('\n\n\n开始生成图片中，请稍等...\n')
    yield '开始生成图片中，请稍等...\n'
    # 创建一个临时的ChromiumOptions对象，用于一些初始化配置
    temp_options = ChromiumOptions()
    temp_options.set_browser_path('C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe')
    # 设置为无头模式，即浏览器在后台运行，不会显示界面，常用于自动化任务中不需要可视化界面的场景
    temp_options.headless()
    # 设置禁止沙盒模式，在某些环境（比如一些Linux环境下）运行时可能需要此配置来避免权限等相关问题
    # temp_options.set_argument('--no-sandbox')
    # 使用配置好的临时选项创建一个ChromiumPage对象，可理解为一个浏览器页面实例，后续可以在这个页面上进行操作
    temp_page = ChromiumPage(temp_options)
    # 通过在这个临时页面上运行JavaScript代码获取当前的用户代理（User-Agent）字符串，它包含了浏览器相关标识等信息
    user_agent = temp_page.run_js("return navigator.userAgent")
    # 关闭这个临时页面，因为后续还要重新创建正式使用的页面，这里只是为了获取用户代理信息
    temp_page.quit()
    # 创建一个 Chromium 浏览器页面对象

    options = ChromiumOptions()
    #  设置浏览器路径,注释掉默认使用Chrome浏览器
    options.set_browser_path('C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe')
    # 设置为无头模式
    options.headless()
    # 以下三行是一些可选的配置，这里被注释掉了，具体说明如下：
    # 禁用GPU（某些情况下需要），例如在一些无头环境中可能不需要GPU加速，或者GPU相关驱动有问题时可以禁用它来避免报错等情况
    # options.set_argument('--disable-gpu')
    # 禁用自动化标志，有些网站可能会检测浏览器是否被自动化控制，设置这个可以尝试绕过这种检测
    # options.set_argument('--disable-blink-features=AutomationControlled')
    # 禁用沙盒模式（适用于Linux），前面已经介绍过其作用，这里再次设置以确保配置生效
    # options.set_argument('--no-sandbox')
    # 将之前获取到的用户代理字符串中的'Headless'字样替换掉，这样可以让用户代理看起来更像普通浏览器，可能有助于绕过部分网站检测
    # print(user_agent)
    yield user_agent
    options.set_user_agent(user_agent.replace('Headless', ''))
    # 使用配置好的选项创建一个真正用于操作的浏览器页面对象
    page = ChromiumPage(options)

    # print('开启页面服务')
    yield '开启系统服务'

    # 开启服务
    page.get('https://www.doubao.com')
    page.set.window.max()
    login_btn = page.ele('xpath://*[@id="root"]/div[1]/div/div[3]/div[1]/div[1]/div/div/div[2]/div/div/div[2]/div[1]')
    if login_btn:
        if "你好，我是豆包" in login_btn.text:
            # print('账号未登录！！！！')
            yield '账号未登录！！！！'
            login_btn = page.ele('xpath://button[@data-testid="to_login_button"]')
            login_btn.click()
            yield '开始登录账号'
            qrcode_btn = page.ele('xpath://div[@class="switcher-y5Irzw"]')
            qrcode_btn.click(by_js=True)
            yield "切换二维码登录方式"
            qr_img = page.ele('xpath://img[@class="qrcode-wtCofi"]').attr('src')
            qr_base64_str = qr_img.split(',')[-1]
            with open("decoded_image.jpg", "wb") as f:
                f.write(base64.b64decode(qr_base64_str))
            yield '二维码生成完毕！'
    try:
        # print('定位图像生成按钮')
        yield '定位图像生成标签'
        # 查找搜索框元素并输入关键词
        gen_img_btn = page.ele('text:图像生成')
        # print('点击图像生成按钮')
        yield '操作图像生成标签'
        gen_img_btn.click()

        # 使用 JavaScript 获取当前聚焦元素的 XPath

        # 定位元素并输入文本
        # print('定位输入框并输入文本')
        yield '定位输入框并输入提示词'
        textbox = page.ele('xpath://div[@role="textbox"]')
        prompt = data['prompt']

        textbox.input(prompt)

        # 查找搜索按钮并点击
        # print('点击提交按钮')
        yield '开始提交生成任务'
        search_button = page.ele('css:#flow-end-msg-send')
        search_button.click()

        # 等待搜索结果加载
        img_num = data['img_num']
        if img_num == 2:
            wait_time = 0.2
        elif img_num == 4:
            wait_time = 0.4
        elif img_num == 6:
            wait_time = 0.5
        else:
            wait_time = 0.6
        total = 100
        for i in range(1, total + 1):
            # 计算完成比例，并将其转换为整数以避免浮点数问题
            progress = int((i / total) * 100)

            # 确保进度条宽度与总进度相匹配
            bar_width = 50  # 进度条宽度设置为50个字符
            completed = '=' * int(progress / (100 / bar_width))
            remaining = ' ' * (bar_width - len(completed))

            # 打印进度条，确保每次更新在同一行
            yield f"海报生成中: [{completed}{remaining}] {progress}%"
            # 在页面中执行JavaScript代码，将指定容器的滚动条滚动到底部。
            page.run_js("""
                    const container = document.querySelector('div.scrollable-nYx8_v');
                    container.scrollTop = container.scrollHeight;
                """)

            # 增加随机延迟，模拟工作负载
            time.sleep(random.uniform(wait_time, wait_time + 0.1))
        yield f"海报生成中，请耐心等待......"
        # print('定位生成好的图片')
        img_list = page.eles('xpath://img[@data-testid="in_painting_picture"]', timeout=30)
        # print('图片列表长度', len(img_list))
        yield '定位生成好的图片'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # print('获取到的img_list: ', img_list)
        for i in img_list:

            img_url = i.attr('src')
            # print('获取到图片的src')
            yield '已成功获取到图片的src'
            response = requests.get(img_url, headers=headers)
            # 获取当前时间戳
            timestamp = time.time()

            # 将时间戳转换为本地时间
            local_time = datetime.fromtimestamp(timestamp)

            # 获取当天日期，格式为 YYYY-MM-DD
            date_str = local_time.strftime('%Y-%m-%d')

            # 创建以当天日期命名的文件夹
            date_folder_path = date_str

            # 获取小时信息
            hour_str = local_time.strftime('%H时')

            # 创建以小时命名的文件夹
            hour_folder_path = os.path.join("海报图片", date_folder_path, hour_str)
            if not os.path.exists(hour_folder_path):
                os.makedirs(hour_folder_path)

            # 将本地时间格式化为字符串，采用特定格式
            time_str = local_time.strftime('%Y-%m-%d/%H时%M分%S秒.%f')[:-3]
            for name in ['白色logo', '黑色logo']:
                # 提取文件名部分
                file_name = time_str.split('时')[-1] + name + '.jpg'
                # 组合完整的文件路径
                file_path = os.path.join(hour_folder_path, file_name)

                # 粘贴西点logo
                yield add_logo_to_poster(response.content, file_path, name, logo_size=0.8)
                #  打开海报并显示
                os.startfile(file_path)
                time.sleep(0.1)
            img_path = os.path.join(hour_folder_path, time_str.split('时')[-1] + "原图.jpg")
            with open(img_path, 'wb') as f:
                f.write(response.content)
            os.startfile(img_path)
    except Exception as e:
        yield e
    finally:
        title_id = page.url.split('/')[-1]
        # print(title_id)
        yield title_id
        # 定位到当前对话的菜单选项
        page.ele(f'xpath://*[@id="conversation_{title_id}"]/div[2]').click()
        # print('定位到菜单按钮')
        yield '定位到菜单选项'
        time.sleep(0.3)
        # 点击删除按钮
        page.ele('xpath://div[@class="semi-popover-content"]/div/ul/li[6]').click()
        # print('点击删除按钮')
        yield '操作删除选项'
        time.sleep(0.3)
        # 点击确认删除按钮
        page.ele('xpath://*[@id="dialog-0"]/div/div[3]/div/button[2]').click()
        # print('点击确认删除按钮')
        yield '对话删除成功'
        time.sleep(0.3)
        # 关闭浏览器
        page.quit()
        # print('关闭服务')
        yield '服务已关闭！'
