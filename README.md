# PhotoViewer

**English** | [繁體中文](README.zh-TW.md)

A lightweight image viewer modeled on the Windows 10 Photo Viewer, written in PyQt6, with support for animated GIF / WebP and slideshows.

## Features

- Supports jpg, png, bmp, gif, webp, tif, ico and svg
- "Fit to window" by default: images larger than the window are scaled down and smaller images are scaled up, keeping the aspect ratio, until one side touches the window edge
- Mouse-wheel zoom and drag-to-pan when zoomed in; Ctrl+0 returns to fit to window
- Slideshow (F5 / F11 / F12 for full screen) with eight interval steps from 1 to 30 seconds; Space pauses / resumes. After leaving full screen the window stays maximized
- "Close all images" button: closes every open PhotoViewer window at once (the other windows are closed normally, not killed)
- Delete key: moves the image to the Recycle Bin and automatically shows the next one (also works during a slideshow)
- Rotate 90° left / right: the rotation is written back to the file, so it persists after reopening
  - JPEG: only the EXIF orientation tag is changed, so the image is not recompressed and quality is unchanged (the few JPEGs that have EXIF data but no orientation field are re-saved once at quality 95)
  - PNG, BMP and TIFF are re-saved losslessly; WebP is re-saved in lossless mode
  - Animated GIF / WebP, SVG and ICO cannot be rotated
- When an image is opened from File Explorer **search results**, PhotoViewer reads that search window's result list, so you can browse and run slideshows across folders
- Files are sorted by natural filename order (p1, p2, …, p10). When search results span several folders, all files in one folder are shown in filename order before moving to the next folder (folders are also in natural name order)

## Keyboard shortcuts

| Key | Action |
| --- | --- |
| ← / → | Previous / next image |
| Space | Pause / resume slideshow (next image outside a slideshow) |
| F5 / F11 / F12 | Start / stop full-screen slideshow |
| Esc | Leave slideshow or full screen (back to a maximized window) |
| Delete | Move to Recycle Bin and show the next image |
| Ctrl+L / Ctrl+R | Rotate 90° left / right (written to the file) |
| Ctrl+O / Ctrl+Shift+O | Open image / open folder |
| Ctrl+0 | Fit to window |

The right-click menu also has: slideshow speed, open containing folder, rotate 90° left / right, copy image, delete image and close all images.

---

## Reinstalling on a new computer (from scratch)

After a broken computer or a fresh Windows install, follow these steps in order to get back to the same setup. It takes about 10 minutes and needs no administrator rights (everything is installed for the current user).

### 1. Install Python and Git

- **Python 3.10 or later**: download the installer from <https://www.python.org/downloads/windows/>.
  On the first screen of the installer, **be sure to tick "Add python.exe to PATH"**, or the build script in step 3 will not find Python.
- **Git**: download and install from <https://git-scm.com/download/win>; the default options are fine.
  (If you would rather not install Git, click Code → Download ZIP on the GitHub page, extract it and skip to step 3.)

Then open a new Command Prompt and check that both commands respond:

```
python --version
git --version
```

### 2. Download the source code

```
git clone https://github.com/alexwudev/PhotoViewer.git
```

Any location works (for example the Desktop). All following steps are done inside this `PhotoViewer` folder.

### 3. Build and install

Double-click **`photo_viewer_build.bat`** in the folder. It will:

1. install PyQt6, pyinstaller and comtypes with pip;
2. build `dist\PhotoViewer\PhotoViewer.exe` with PyInstaller;
3. copy the whole program to `%LOCALAPPDATA%\PhotoViewer\` (that is, `C:\Users\<your account>\AppData\Local\PhotoViewer\`).

When you see `Done! Installed to: ...PhotoViewer.exe`, it worked; press any key to close the window.
Building takes a minute or two, and a lot of scrolling output is normal.

### 4. Register in the "Open with" list

Double-click **`photo_viewer_register.reg`** and click "Yes" when Registry Editor shows its warning.
This step:

- makes PhotoViewer appear in the right-click "Open with" list for images;
- keeps File Explorer's image thumbnails (instead of turning them all into the program icon).

Paths in the file are written as `%LOCALAPPDATA%`, so it works for any account name without editing.

### 5. Restart File Explorer

Task Manager → find "Windows Explorer" → right-click "Restart" (or simply sign out and back in).

### 6. Make it the default image viewer

Right-click any image → **Open with** → **Choose another app** → select **Photo Viewer** → tick **"Always use this app to open .jpg files"** → OK.

Do this once per file extension (setting the common ones such as .jpg, .jpeg, .png, .gif and .webp is enough).
You can also change them all at once under Settings → Apps → Default apps.

### 7. Check

- Double-clicking an image should open it in PhotoViewer;
- Type a keyword in the File Explorer search box and open an image from the results: the title bar should show "（搜尋結果）" (search results), and → should move across folders.

---

## Updating

After editing `photo_viewer.py` or pulling a new version:

```
git pull
```

Then double-click `photo_viewer_build.bat` again to rebuild and reinstall; there is no need to import the `.reg` again.
(If the build reports that a file is in use, close all open PhotoViewer windows first.)

## Running from source without packaging

```
pip install PyQt6 comtypes
python photo_viewer.py [image or folder path]
```

`comtypes` is only used for browsing search results across folders; without it the program still runs, falling back to single-folder mode.

## Troubleshooting

| Problem | Solution |
| --- | --- |
| The bat file says `python` cannot be found | "Add to PATH" was not ticked when installing Python; run the installer again, choose Modify and tick it, or reinstall |
| Photo Viewer is missing from the right-click "Open with" list | Make sure the `.reg` was imported in step 4, then restart File Explorer |
| File Explorer thumbnails turned into the program icon | Import the `.reg` again and restart File Explorer |
| Opening an image from search results only shows images from the same folder | The search window must still be open when you open the image; if the search has not finished, only the results listed so far are read |
| You want an image back after pressing Delete | It is in the Recycle Bin; right-click it and choose "Restore" |

## Uninstalling

1. Delete the folder `%LOCALAPPDATA%\PhotoViewer`.
2. In Registry Editor (regedit), delete these keys:
   - `HKEY_CURRENT_USER\Software\Classes\Applications\PhotoViewer.exe`
   - `HKEY_CURRENT_USER\Software\Classes\Applications\PhotoViewerWebp.exe`
   - `HKEY_CURRENT_USER\Software\Classes\PhotoViewer.Image`
3. Under Settings → Apps → Default apps, switch images back to another program.

## Files

| File | Purpose |
| --- | --- |
| `photo_viewer.py` | Main program (single file) |
| `photo_viewer_build.bat` | Installs dependencies, builds and installs to `%LOCALAPPDATA%` |
| `PhotoViewer.spec` | PyInstaller build settings (`python -m PyInstaller --noconfirm PhotoViewer.spec`) |
| `photo_viewer_register.reg` | Registers the "Open with" entry and thumbnail settings |
