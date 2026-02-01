import cv2
import numpy as np
import os
import subprocess
import sys

def get_coordinates(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        scale_factor = param['scale_factor']
        orig_x = int(x / scale_factor)
        orig_y = int(y / scale_factor)

        h, w = param['original_image'].shape[:2]
        if 0 <= orig_x < w and 0 <= orig_y < h:
            b, g, r = param['original_image'][orig_y, orig_x]
            print(f"显示窗口坐标: ({x}, {y})")
            print(f"原图实际坐标: ({orig_x}, {orig_y})")
            print(f"RGB颜色: ({r}, {g}, {b})")
            print("-" * 30)

            param['points'].append((orig_x, orig_y))
            param['display_img'] = param['scaled_image'].copy()
            _draw_points(param)

def _draw_points(param):
    for i, (orig_x, orig_y) in enumerate(param['points']):
        x_disp = int(orig_x * param['scale_factor'])
        y_disp = int(orig_y * param['scale_factor'])
        cv2.circle(param['display_img'], (x_disp, y_disp), 5, (0, 0, 255), -1)
        text = f"P{i+1}:({orig_x},{orig_y})"
        cv2.putText(param['display_img'], text, (x_disp + 10, y_disp),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

def main():
    # === Step 1: ADB 截图 ===
    print("[INFO] 正在通过 ADB 截取屏幕...")
    try:
        subprocess.run(['adb', 'shell', 'screencap', '-p', '/sdcard/screen.png'], check=True)
        subprocess.run(['adb', 'pull', '/sdcard/screen.png', 'temp_screen.png'], check=True)
        subprocess.run(['adb', 'shell', 'rm', '/sdcard/screen.png'], check=True)
    except subprocess.CalledProcessError:
        print("[ERROR] ADB 截图失败！请确保设备已连接并授权调试。")
        sys.exit(1)


    original_image = cv2.imread('temp_screen.png')
    if original_image is None:
        print("[ERROR] 无法加载截图")
        sys.exit(1)

    h, w = original_image.shape[:2]
    print(f"[INFO] 截图尺寸: {w} x {h}")

    max_display_w, max_display_h = 1920, 1080
    scale = min(max_display_w / w, max_display_h / h, 1.0)
    scaled_image = cv2.resize(original_image, (int(w * scale), int(h * scale)))

    params = {
        'original_image': original_image,
        'scaled_image': scaled_image,
        'display_img': scaled_image.copy(),
        'scale_factor': scale,
        'points': [],
        'orig_width': w,
        'orig_height': h
    }

    win_name = 'Screen Capture - Click to Pick | E=Undo Last | R=Reset | Q=Quit'
    cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)  # 关键：WINDOW_NORMAL 允许缩放
    cv2.resizeWindow(win_name, scaled_image.shape[1], scaled_image.shape[0])
    cv2.setMouseCallback(win_name, get_coordinates, param=params)

    print("\n  使用说明：")
    print("   - 左键点击：添加坐标点")
    print("   - 按 E：删除最后一个点")
    print("   - 按 R：清空所有点")
    print("   - 按 Q 或关闭窗口：退出\n")

    while True:
        cv2.imshow(win_name, params['display_img'])
        key = cv2.waitKey(50) & 0xFF

        if cv2.getWindowProperty(win_name, cv2.WND_PROP_VISIBLE) < 1:
            break

        if key == ord('q'):
            break

        elif key == ord('r'):
            params['points'] = []
            params['display_img'] = params['scaled_image'].copy()
            print("所有点已重置")

        elif key == ord('e') and params['points']:
            removed = params['points'].pop()
            params['display_img'] = params['scaled_image'].copy()
            _draw_points(params)
            print(f"↩已删除点: {removed}")

    cv2.destroyAllWindows()

    if os.path.exists('temp_screen.png'):
        os.remove('temp_screen.png')

    if params['points']:
        print(f"\n共选定 {len(params['points'])} 个点：")
        for i, (x, y) in enumerate(params['points']):
            b, g, r = original_image[y, x]
            print(f"点{i+1}: ({x}, {y}) - RGB:({r}, {g}, {b})")
    else:
        print("未选择任何坐标")

if __name__ == '__main__':
    main()