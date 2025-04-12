from typing import Tuple, Optional, Literal
from .AutoVisualimage import AutoVisualImage
from .types import RetryConfig

import numpy as np
import pyautogui
import cv2
import uuid

# Variáveis globais para a seleção
start_point = None
end_point = None
cropping = False


def _mouse_crop(event, x, y, flags, param):
    global start_point, end_point, cropping

    if event == cv2.EVENT_LBUTTONDOWN:
        start_point = (x, y)
        cropping = True

    elif event == cv2.EVENT_MOUSEMOVE and cropping:
        temp = param.copy()
        cv2.rectangle(temp, start_point, (x, y), (0, 255, 0), 2)  # type: ignore
        cv2.imshow("Select Region", temp)

    elif event == cv2.EVENT_LBUTTONUP:
        end_point = (x, y)
        cropping = False
        cv2.destroyAllWindows()


def select_region() -> Tuple[int, int, int, int]:
    """
    Permite que o usuário selecione uma região da tela com o mouse e retorna (left, top, width, height)
    """
    screenshot = pyautogui.screenshot()
    screen_np = np.array(screenshot)
    screen_bgr = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)

    cv2.namedWindow("Select Region", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("Select Region", _mouse_crop, param=screen_bgr)

    print("🖱️ Selecione a área da tela clicando e arrastando o mouse...")

    while cropping or end_point is None:
        cv2.imshow("Select Region", screen_bgr)
        if cv2.waitKey(1) & 0xFF == 27:  # ESC para cancelar
            break

    cv2.destroyAllWindows()

    if start_point and end_point:
        x1, y1 = start_point
        x2, y2 = end_point
        left = min(x1, x2)
        top = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        return (left, top, width, height)
    else:
        raise Exception("Nenhuma região selecionada")
