# PhotoViewer

仿 Windows 10 相片檢視器的輕量圖片檢視器，以 PyQt6 撰寫，支援 GIF／WebP 動圖與幻燈片播放。

## 功能

- 支援 jpg、png、bmp、gif、webp、tif、ico、svg
- 滑鼠滾輪縮放、放大後可拖曳平移；Ctrl+0 回到適合視窗
- 幻燈片（F5／F11／F12 全螢幕），間隔 1–30 秒八段可選，Space 暫停／繼續
- Delete 鍵：圖片移到資源回收筒，並自動切到下一張（幻燈片中亦可）
- 從檔案總管的**搜尋結果**開啟圖片時，會讀取該搜尋視窗的結果，跨資料夾瀏覽與播放幻燈片
- 排序一律依檔名自然排序（p1、p2、…、p10）

## 安裝（Windows）

需要 Python 3.10 以上。

1. 執行 `photo_viewer_build.bat`：安裝相依套件（PyQt6、pyinstaller、comtypes），以 PyInstaller 打包，並安裝到 `%LOCALAPPDATA%\PhotoViewer`。
2. 按兩下 `photo_viewer_register.reg`，把 PhotoViewer 加進「開啟檔案」清單，並保留檔案總管的縮圖。
3. 重新啟動 explorer.exe（或登出再登入）。

直接執行原始碼：

```
pip install PyQt6 comtypes
python photo_viewer.py [圖片或資料夾路徑]
```

## 快捷鍵

| 按鍵 | 功能 |
| --- | --- |
| ← / → | 上一張／下一張 |
| Space | 幻燈片暫停／繼續（非幻燈片時為下一張） |
| F5 / F11 / F12 | 開始／停止全螢幕幻燈片 |
| Esc | 離開幻燈片或全螢幕 |
| Delete | 移到資源回收筒並顯示下一張 |
| Ctrl+O / Ctrl+Shift+O | 開啟圖片／開啟資料夾 |
| Ctrl+0 | 適合視窗 |
