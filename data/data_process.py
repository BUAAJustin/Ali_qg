# coding=utf-8

import json

seps, strips = u'\n。！？!?；;，, ', u'；;，, '

def text_segmentate(text, maxlen, seps='\n', strips=None):
    """
    Divide the text into short sentences according to punctuation
    :param text：string
    :param maxlen: num, the max length of sentences
    :param seps: punctuation
    :param strips: the blank
    :return:
    """
    text = text.strip().strip(strips)
    if seps and len(text) > maxlen:
        pieces = text.split(seps[0])   # 以\n为界得到的结果[text1, text2, ...]
        text, texts = '', []
        for i, p in enumerate(pieces):
            if text and p and len(text) + len(p) > maxlen - 1:
                texts.extend(text_segmentate(text, maxlen, seps[1:], strips))
                text = ''
            if i + 1 == len(pieces):
                text += p
            else:
                text = text + p + seps[0]

        if text:
            texts.extend(text_segmentate(text, maxlen, seps[1:], strips))
        return texts

    else:
        return [text]

def answer_process(answer, max_a_len):

    assert(len(answer)>max_a_len)
    answer_corrected = ''
    #print(text_segmentate(answer,  max_a_len, seps, strips))
    for i in text_segmentate(answer,  max_a_len, seps, strips):
        if len(answer_corrected)+len(i) < max_a_len:
            answer_corrected += i
        else:
            return answer_corrected
    answer_corrected = answer_corrected.replace('\n','')
    answer_corrected = answer_corrected.replace('\t', '')
    #answer_corrected = answer_corrected.replace('\\', '')
    return answer_corrected

def context_process(context, answer, max_p_len, max_a_len):

    context_segmented = text_segmentate(context, max_p_len, seps, strips)
    #if len(context_segmented) == 1
    #print(len(context_segmented))
    context_corrected = ''
    a_found_in_c = False
    for i, text in enumerate(context_segmented):
        if answer in text or text in answer:
            a_found_in_c = True
            context_corrected = text
            for j in range(2):
                if j == 0:  # 如果条件允许，context添加上一个text_segmented
                    if i>0 and len(context_corrected)+len(context_segmented[i-1])< max_p_len:
                        context_corrected = context_segmented[i-1] + context_corrected
                    else:
                        continue
                elif j == 1: # 如果条件允许，context添加下一个text_segmented
                    if i != len(context_segmented)-1 and len(context_corrected)+len(context_segmented[i+1])< max_p_len:
                        context_corrected = context_corrected + context_segmented[i+1]
                    else:
                        continue
                else: # 如果条件允许，context添加上二个text_segmented
                    if i>1 and len(context_corrected)+len(context_segmented[i-2])< max_p_len:
                        context_corrected = context_segmented[i-2] + context_corrected
                    else:
                        continue
            break
    if not a_found_in_c:  # 如果在text_segmented里没找到answer, 直接取第一个值
        for i in context_segmented:
            if len(context_corrected) + len(i) < max_p_len - max_a_len:
                context_corrected += i
            else:
                break

    context_corrected = context_corrected.replace('\n','')
    context_corrected = context_corrected.replace('\t', '')
    context_corrected = context_corrected.replace('\\', '')

    #print(context_corrected)
    return context_corrected

def data_process(file, max_p_len, max_a_len, mode):
    """
    :param file: the directory of the data file(json)
    :param max_p_len: the max length of the context
    :param mode: the mode of data('train' or 'test')
    :return data: list
        format: train: [(id, context1, answer1, question1), ....]
                test: [(id, context1, answer1), ...]
    """
    datasets = json.load(open(file, encoding='utf-8'))

    seps, strips = u'\n。！？!?；;，, ', u'；;，, '
    data_tuple = []

    for segment in datasets:
        for pa in segment['annotations']:
            if len(pa['A']) > max_a_len:
                pa['A'] = answer_process(pa['A'], max_a_len)

            context_corrected = context_process(segment['text'], pa['A'], max_p_len, max_a_len)
            if mode == 'test':
                data_tuple.append((segment['id'], context_corrected, pa['A']))
            elif mode == 'train':
                data_tuple.append((segment['id'], context_corrected, pa['A'], pa['Q']))
    return data_tuple


def write_to_file(data, mode):
    if mode == 'train':
        file = './ali_qg_train.txt'
    elif  mode == 'test':
        file = './ali_qg_test.txt'
    else:
        file = ''
    count = 0
    with open(file, 'w', encoding='utf-8') as f:
        for i, data in enumerate(data):
            context = data[1].replace('\n', '')
            context = context.replace('\t', '')
            answer = data[2].replace('\n', '')
            answer = answer.replace('\t', '')
            if mode == 'train':
                question = data[3].replace('\n', '')
                question = question.replace('\t', '')
                f.write(context + "[SEP]" + answer + "#####" + question + "\n")   # 五个#####作为分隔ca 和 q的分隔符
                count += 1
            if mode == 'test':
                f.write(context + "[SEP]" + answer + "#####" + "\n")
                count += 1
    print(count)

def output_2_standard(output_file, json_file, json_out_name):  # 处理输出数据格式
    json_data = json.load(open(json_file, encoding='utf-8'))
    count = 0
    with open(output_file, 'r', encoding='utf-8') as f:
        questions = f.readlines()
        print(len(questions))
        for i, data in enumerate(json_data):
            for j, qa in enumerate(data['annotations']):
                qa["Q"] = questions[count].strip().replace(" ", "")
                count += 1
    print(count)

    with open(json_out_name, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, sort_keys=True, indent=4, separators=(',', ':'), ensure_ascii=False)

train_file = "./round1_train_0907.json"
test_file = "./round1_test_0907.json"

train_data = data_process(train_file, 280, 100, 'train')
test_data = data_process(test_file, 280, 100, 'test')

write_to_file(train_data, 'train')
write_to_file(test_data, 'test')
