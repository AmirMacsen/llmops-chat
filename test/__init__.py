import jieba

# 待分词文本
text = "jieba分词能获取词在文档中的位置吗"

# 使用 tokenize 方法，返回生成器（包含词、起始位置、结束位置）
# mode="search" 表示启用搜索模式（更细粒度分词），默认 mode="default"
for item in jieba.tokenize(text, mode="default"):
    print(item)