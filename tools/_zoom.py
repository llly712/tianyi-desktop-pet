from PIL import Image

im = Image.open("D:/tianyi-pet/mouth_sheet2.png")
names = ["idle", "kakuage1.0", "kakuage0.5", "nikori1.0", "nikori0.2", "smile_old"]
cw, ch = 360, 270
out = Image.new("RGB", (240 * 6, 200), (0, 0, 0))
for i in range(6):
    c, r = i % 3, i // 3
    tile = im.crop((c * cw, r * ch, c * cw + cw, r * ch + ch))
    m = tile.crop((120, 60, 240, 160)).resize((240, 200), Image.LANCZOS)
    out.paste(m, (i * 240, 0))
out.save("D:/tianyi-pet/mouth_zoom.png")
print("saved", names, flush=True)
