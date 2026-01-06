import threading
import time

# 加载并处理拼音数据
# 从 pinyin-data 项目的GitHub仓库下载核心数据文件 `pinyin.txt`：
# 下载地址：https://github.com/mozillazg/pinyin-data/blob/master/pinyin.txt

def load_pinyin_dict(pinyin_file_path):
    """
    读取 pinyin.txt 文件，构建一个 拼音 -> [汉字列表] 的反向字典。
    pinyin.txt 的格式示例：U+4E2D: zhōng,zhòng  # 中
    """
    pinyin_to_hanzi = {}
    with open(pinyin_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # 解析行：如 "U+4E2D: zhōng,zhòng  # 中"
            parts = line.split('#', 1)
            if len(parts) < 2:
                continue
            code_point_part, hanzi = parts[0].strip(), parts[1].strip()
            # 获取编码点和拼音字符串
            code_point, pinyin_str = code_point_part.split(':', 1)
            code_point = code_point.strip()  # 如 "U+4E2D"
            pinyin_str = pinyin_str.strip()  # 如 "zhōng,zhòng"
            # 将十六进制编码点转换为汉字
            try:
                hanzi_char = chr(int(code_point[2:], 16))  # 去掉"U+"
            except ValueError:
                continue
            # 处理多音字：将拼音字符串按逗号分割
            pinyin_list = [p.strip() for p in pinyin_str.split(',')]
            for py in pinyin_list:
                # 为了方便比较，可以将拼音转换为不含声调的形式
                # 这里使用一个简单函数去除声调，也可以利用 pypinyin 的 style 参数
                py_normalized = remove_tone(py)  # 例如将 "zhōng" -> "zhong"
                if py_normalized not in pinyin_to_hanzi:
                    pinyin_to_hanzi[py_normalized] = []
                if hanzi_char not in pinyin_to_hanzi[py_normalized]:
                    pinyin_to_hanzi[py_normalized].append(hanzi_char)
    return pinyin_to_hanzi


def remove_tone(pinyin_with_tone):
    """
    一个简单的函数，去除拼音中的声调符号（第一声到第四声）和轻声标识（数字5）。
    注意：这是一个基础实现，对于复杂情况可能需要更健壮的库。
    """
    # 移除数字声调（风格 TONE2/TONE3）
    no_tone = ''.join([c for c in pinyin_with_tone if not c.isdigit()])
    # 替换带声调的字母为基本字母（这里仅处理常见情况，非完整列表）
    tone_map = {
        'ā': 'a', 'á': 'a', 'ǎ': 'a', 'à': 'a',
        'ē': 'e', 'é': 'e', 'ě': 'e', 'è': 'e',
        'ī': 'i', 'í': 'i', 'ǐ': 'i', 'ì': 'i',
        'ō': 'o', 'ó': 'o', 'ǒ': 'o', 'ò': 'o',
        'ū': 'u', 'ú': 'u', 'ǔ': 'u', 'ù': 'u',
        'ǖ': 'v', 'ǘ': 'v', 'ǚ': 'v', 'ǜ': 'v',
        'ü': 'v'
    }
    result = ''.join([tone_map.get(c, c) for c in no_tone])
    return result


# if __name__ == '__main__':
#     print()
#
#     # 构建拼音到汉字的字典
#     dict_data = load_pinyin_dict('pinyin.txt')
#
#     he = 'he'
#     he_size = len(dict_data['he'])
#     yi = 'yi'
#     yi_size = len(dict_data['yi'])
#     wei = 'wei'
#     wei_size = len(dict_data['wei'])
#     total = he_size * yi_size * wei_size
#     print(total)
#
#     heyiweis = []
#
#     with open('何意味.txt', 'w', encoding='utf-8') as f:
#         for i in range (0, he_size):
#             for j in range (0, yi_size):
#                 for k in range (0, wei_size):
#                     s = dict_data['he'][i] + dict_data['yi'][j] + dict_data['wei'][k]
#                     f.write(s + ' ')
#                     heyiweis.append(s)
#
#                     # 进度条显示
#                     current = i * yi_size * wei_size + j * wei_size + k + 1
#                     percent = current / total * 100
#                     bar_length = 50
#                     filled_length = int(bar_length * current // total)
#                     bar = '█' * filled_length + '░' * (bar_length - filled_length)
#
#                     # 使用 \r 覆盖上一行
#                     print(f'\r进度: |{bar}| {current}/{total} ({percent:.1f}%)', end='', flush=True)
#
#                 f.write('\n')
#             f.write('\n')
#
#     print()

if __name__ == '__main__':
    print("优化版本")

    dict_data = load_pinyin_dict('pinyin.txt')

    he_size = len(dict_data['he'])
    yi_size = len(dict_data['yi'])
    wei_size = len(dict_data['wei'])
    total = he_size * yi_size * wei_size


    # 按i分批处理
    def process_batch(i_start, i_end, results_list, lock):
        batch_results = []
        for i in range(i_start, i_end):
            for j in range(yi_size):
                line_results = []
                for k in range(wei_size):
                    s = dict_data['he'][i] + dict_data['yi'][j] + dict_data['wei'][k]
                    line_results.append(s)
                batch_results.append((i, j, line_results))

        with lock:
            results_list.extend(batch_results)


    start_time = time.time()

    # 创建线程处理不同批次
    num_threads = 8
    threads = []
    results = []
    lock = threading.Lock()
    batch_size = he_size // num_threads + 1

    for t in range(num_threads):
        i_start = t * batch_size
        i_end = min((t + 1) * batch_size, he_size)
        if i_start < he_size:
            thread = threading.Thread(
                target=process_batch,
                args=(i_start, i_end, results, lock)
            )
            threads.append(thread)
            thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    # 按原始顺序排序
    results.sort(key=lambda x: (x[0], x[1]))

    # 写入文件
    with open('何意味.txt', 'w', encoding='utf-8') as f:
        current_i = -1
        for i, j, line_chars in results:
            if i != current_i and current_i != -1:
                f.write('\n')
            f.write(' '.join(line_chars) + ' ')
            f.write('\n')
            current_i = i

    end_time = time.time()
    print(f"优化版本完成时间: {end_time - start_time:.2f}秒")
    print(f"总组合数: {total}")
