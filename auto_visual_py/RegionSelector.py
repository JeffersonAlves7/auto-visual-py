from typing import Tuple, Optional
import numpy as np
import pyautogui
import cv2


class RegionSelector:
    """
    Classe responsável por permitir ao usuário selecionar uma região da tela com o mouse.
    """

    def __init__(self):
        """
        Inicializa os atributos para controle da seleção da região da tela.
        """
        self.start_point: Optional[Tuple[int, int]] = None
        self.end_point: Optional[Tuple[int, int]] = None
        self.cropping: bool = False
        self.image = None

    def _mouse_crop(self, event, x, y, flags, param):
        """
        Callback de evento do mouse usado para detectar e desenhar a região selecionada.

        Args:
            event: Evento do mouse (clique, movimento, soltura, etc).
            x (int): Posição x atual do cursor.
            y (int): Posição y atual do cursor.
            flags: Sinalizadores extras (não utilizados).
            param: Parâmetros extras (não utilizados).
        """
        if event == cv2.EVENT_LBUTTONDOWN:
            self.start_point = (x, y)
            self.cropping = True

        elif event == cv2.EVENT_MOUSEMOVE and self.cropping and self.image is not None and self.start_point is not None:
            temp = self.image.copy()
            cv2.rectangle(temp, self.start_point, (x, y), (0, 255, 0), 2)
            cv2.imshow("Select Region", temp)

        elif event == cv2.EVENT_LBUTTONUP:
            self.end_point = (x, y)
            self.cropping = False

    def select(self) -> Tuple[int, int, int, int]:
        """
        Captura uma imagem da tela, permite que o usuário selecione uma região com o mouse,
        e retorna as coordenadas da região selecionada.

        Returns:
            Tuple[int, int, int, int]: (left, top, width, height) da região selecionada.

        Raises:
            Exception: Caso o usuário pressione ESC para cancelar a seleção.
        """
        screenshot = pyautogui.screenshot()
        screen_np = np.array(screenshot)
        self.image = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)

        cv2.namedWindow("Select Region", cv2.WINDOW_NORMAL)
        cv2.setMouseCallback("Select Region", self._mouse_crop)

        print("🖱️ Selecione a área da tela clicando e arrastando o mouse (ESC para cancelar)...")

        while True:
            cv2.imshow("Select Region", self.image)
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                cv2.destroyAllWindows()
                raise Exception("Seleção cancelada pelo usuário.")
            elif not self.cropping and self.start_point and self.end_point:
                break

        cv2.destroyAllWindows()

        x1, y1 = self.start_point
        x2, y2 = self.end_point
        left = min(x1, x2)
        top = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        return (left, top, width, height)
