# iOS 26 彩虹壁纸颜色提取器

根据歌曲专辑封面提取主要颜色，并把这些颜色映射到一组固定的彩虹壁纸调色板中。

这个脚本适合用来给 iOS 26 新的彩虹壁纸生成配色参考：输入一张专辑图片，脚本会采样图片像素，找到每个像素最接近的调色板颜色，然后统计出现频率最高的颜色。

## 功能

- 将专辑封面颜色映射到固定调色板，而不是直接输出图片里的任意颜色。
- 默认使用 Oklab 色彩距离，匹配结果更接近人眼感知。
- 输出颜色排名、HEX、RGB、占比和像素数量。
- 支持 JSON 输出，方便接入其他自动化流程。
- 可以保存一张被调色板颜色重新映射后的预览图。
- 支持透明图片，可通过 alpha 阈值忽略透明像素。

## 环境要求

- Python 3.9+
- NumPy
- Pillow

安装依赖：

```bash
python3 -m pip install -r requirements.txt
```

## 使用方法

基础用法：

```bash
python3 color_frequency.py path/to/album-cover.jpg
```

输出前 6 个主要颜色：

```bash
python3 color_frequency.py path/to/album-cover.jpg --top 6
```

输出 JSON：

```bash
python3 color_frequency.py path/to/album-cover.jpg --top 6 --json
```

保存一张调色板映射后的预览图：

```bash
python3 color_frequency.py path/to/album-cover.jpg --top 6 --save-map mapped-cover.png
```

如果图片很大，可以每隔 3 个像素采样一次来加快速度：

```bash
python3 color_frequency.py path/to/album-cover.jpg --sample-step 3
```

## 输出示例

```text
 1. #F4007A rgb(244, 0, 122) 18.42% (18420 px)
 2. #22A2F9 rgb(34, 162, 249) 12.77% (12770 px)
 3. #FEE600 rgb(254, 230, 0) 9.31% (9310 px)
```

默认会在终端里显示颜色块。如果不想显示颜色块：

```bash
python3 color_frequency.py path/to/album-cover.jpg --no-blocks
```

## 参数说明

```text
image                    输入图片路径
-n, --top                输出颜色数量，默认：3
--metric {oklab,rgb}     最近颜色匹配算法，默认：oklab
--sample-step N          每隔 N 个像素采样一次
--alpha-threshold N      忽略 alpha 低于 N 的像素，默认：1
--chunk-size N           每批处理的像素数量，默认：200000
--json                   输出 JSON
--no-blocks              不显示终端颜色块
--save-map PATH          保存调色板映射后的图片
```

## 说明

调色板直接写在 `color_frequency.py` 的 `PALETTE_HEX` 中，一共有 75 个颜色。它们来自三张色卡截图里的圆形色块，取样时从每个圆形中心取色，并排除了背景色。

如果是为了设置彩虹壁纸配色，建议先用 `--top 3` 或 `--top 6` 看主要颜色，再根据专辑氛围手动挑选，而不是完全只按最高频颜色决定。

