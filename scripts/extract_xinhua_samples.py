# -*- coding: utf-8 -*-
"""
提取《新华财经》中涉及中烟工业的样稿（DOCX）到 JSON/JSONL/TXT
- 自动按空行/标题分段（更鲁棒）
- 生成 data/xinhua_samples_extracted.json
- 生成 data/xhf_samples/raw/article_XXX.txt
- 可多次运行，自动创建目录
依赖: python-docx
"""
import os
import sys
import json
import re

def ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def friendly_path(p: str) -> str:
    # 兼容 ~ 与相对路径
    return os.path.abspath(os.path.expanduser(p))

def try_import_docx():
    try:
        from docx import Document  # type: ignore
        return Document
    except Exception as e:
        print("未安装依赖 python-docx 或导入失败。")
        print("请执行：pip install python-docx")
        print(f"错误详情：{e}")
        sys.exit(1)

def looks_like_title(s: str) -> bool:
    # 极简标题启发：居中/加粗/长度 <= 30 / 末尾无句号；或第1行
    if len(s) <= 30 and not s.endswith(("。", ".", "！", "?", "？", "！")):
        # 常见财经标题中常见符号/风格
        if re.search(r"[：:｜\-\—]|（.*）|\(.*\)", s) or True:
            return True
    return False

def split_articles(paragraphs):
    """
    根据空行 + 标题启发式拆分为多篇文章
    """
    articles = []
    buf = []
    for i, para in enumerate(paragraphs):
        t = para.strip()
        if not t:
            # 空行作为分隔：若当前缓冲有内容，则落一次
            if buf:
                articles.append("\n".join(buf).strip())
                buf = []
            continue
        if looks_like_title(t) and buf:
            # 新标题且缓冲有内容 -> 开启新篇
            articles.append("\n".join(buf).strip())
            buf = [t]
        else:
            buf.append(t)
    if buf:
        articles.append("\n".join(buf).strip())
    # 过滤掉过短片段
    articles = [a for a in articles if len(a) >= 50]
    return articles

def extract_docx_samples(docx_path: str):
    Document = try_import_docx()
    p = friendly_path(docx_path)
    if not os.path.isfile(p):
        print(f"未找到DOCX文件：{p}")
        print("请确认文件路径是否正确。")
        sys.exit(2)

    doc = Document(p)
    paras = [para.text for para in doc.paragraphs]
    articles = split_articles(paras)

    ensure_dir("data")
    ensure_dir("data/xhf_samples/raw")

    # 主 JSON
    out_json = "data/xinhua_samples_extracted.json"
    payload = {"source": p, "total_articles": len(articles), "articles": articles}
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # JSONL + 单文档 TXT
    out_jsonl = "data/xhf_samples/xinhua_samples.jsonl"
    ensure_dir(os.path.dirname(out_jsonl))
    with open(out_jsonl, "w", encoding="utf-8") as jf:
        for i, a in enumerate(articles, 1):
            rec = {"id": f"xhf_{i:03d}", "text": a}
            jf.write(json.dumps(rec, ensure_ascii=False) + "\n")
            with open(f"data/xhf_samples/raw/article_{i:03d}.txt", "w", encoding="utf-8") as tf:
                tf.write(a)

    # 预览
    print(f"成功提取 {len(articles)} 篇文章")
    print(f"主 JSON：{out_json}")
    print(f"JSONL：{out_jsonl}")
    print(f"逐篇TXT：data/xhf_samples/raw/article_XXX.txt")
    for i, a in enumerate(articles[:3], 1):
        print("\n" + "=" * 50)
        print(f"文章 {i} 预览（前200字）：\n{a[:200]}...")

if __name__ == "__main__":
    # 默认路径（你可以改成实际DOCX路径）
    default_path = r".\新华财经.docx"
    docx_path = sys.argv[1] if len(sys.argv) > 1 else default_path
    extract_docx_samples(docx_path)
