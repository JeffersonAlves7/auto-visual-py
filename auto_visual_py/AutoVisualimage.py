from typing import Literal, Optional, Self
import time
from .types import RetryConfig
import os

try:
    import pyautogui
    from PIL import Image, ImageOps
except ImportError:
    raise ImportError(
        "Você precisa instalar pyautogui e pillow: pip install pyautogui pillow"
    )

try:
    import pytesseract

    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

TEMP_EXISTS = False


class AutoVisualImage:
    def __init__(
        self,
        src: str,
        mode: Optional[Literal["default", "grayscale", "hue_shift"]] = None,
        hue_shift: Optional[float] = None,
        confidence: Optional[float] = None,
        retry_config: Optional[RetryConfig] = None,
    ):
        self.src = src
        self.mode = mode if mode else "default"
        self.hue_shift = hue_shift if hue_shift else 0.0
        self.confidence = confidence if confidence else 0.9
        self.retry_config = retry_config if retry_config else (0, 0)

    def get_position(self) -> Optional[tuple[int, int]]:
        """
        Retorna o centro da imagem se for encontrada na tela. Sem retentativas.
        """
        if not os.path.isfile(self.src):
            print(f"[AutoVisualImage] Arquivo não encontrado: {self.src}")
            return None

        try:
            location = pyautogui.locateCenterOnScreen(
                self._save_temp_image(),
                confidence=self.confidence,
                grayscale=(self.mode == "grayscale"),
            )  # type: ignore
            return location if location else None
        except Exception as e:
            print(f"[AutoVisualImage] Erro ao localizar imagem: {e}")
            return None

    def click(self) -> bool:
        """
        Tenta encontrar a imagem e clicar nela com retentativas.
        """
        attempts, delay = self.retry_config

        for attempt in range(1, attempts + 2):
            pos = self.get_position()

            if pos:
                try:
                    pyautogui.click(pos)
                    print(f"[AutoVisualImage] Clique realizado na tentativa {attempt}.")
                    return True
                except Exception as e:
                    print(f"[AutoVisualImage] Erro ao clicar: {e}")
            else:
                print(
                    f"[AutoVisualImage] Imagem não encontrada na tentativa {attempt}."
                )

            if attempt <= attempts:
                print(f"[AutoVisualImage] Aguardando {delay}s para tentar novamente...")
                time.sleep(delay)

        print(
            f"[AutoVisualImage] Não foi possível clicar na imagem após {attempts + 1} tentativas."
        )
        return False

    def get_text(self) -> str:
        """
        Utiliza OCR para extrair texto da imagem.
        """
        if not OCR_AVAILABLE:
            raise ImportError(
                "pytesseract não está instalado. Use `pip install pytesseract`."
            )

        if not os.path.isfile(self.src):
            print(f"[AutoVisualImage] Arquivo não encontrado: {self.src}")
            return ""

        try:
            image = Image.open(self.src)
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            print(f"[AutoVisualImage] Erro ao processar OCR: {e}")
            return ""

    def build(
        self,
        mode: Optional[Literal["default", "grayscale", "hue_shift"]] = None,
        hue_shift: Optional[float] = None,
        confidence: Optional[float] = None,
        retry_config: Optional[RetryConfig] = None,
    ) -> Self:
        """
        Create a copy of the class but with other properties
        in resume you can get the same Image but with other confidence, mode...
        """

        return AutoVisualImage(
            src=str(self.src),
            mode=mode,
            hue_shift=hue_shift,
            confidence=confidence,  # type: ignore
            retry_config=retry_config,
        )

    # region Private section
    def _load_image(self) -> Image.Image:
        img = Image.open(self.src)

        if self.mode == "grayscale":
            img = ImageOps.grayscale(img)

        elif self.mode == "hue_shift":
            img = AutoVisualImage._apply_hue_shift(img, self.hue_shift)

        return img

    def _save_temp_image(self) -> str:
        """Salva a imagem tratada temporariamente para ser usada com pyautogui."""

        img = self._load_image()
        temp_path = "temp/_temp_autovisual.png"
        global TEMP_EXISTS
        if not TEMP_EXISTS:
            if os.path.exists("temp"):
                TEMP_EXISTS = True
            else:
                os.makedirs("./temp")
        img.save(temp_path)

        return temp_path

    @staticmethod
    def _apply_hue_shift(img: Image.Image, shift: float) -> Image.Image:
        import colorsys
        import numpy as np

        img = img.convert("RGB")
        np_img = np.array(img) / 255.0

        r, g, b = np_img[:, :, 0], np_img[:, :, 1], np_img[:, :, 2]
        h, s, v = colorsys.rgb_to_hsv(r.mean(), g.mean(), b.mean())
        h = (h + shift) % 1.0
        r, g, b = colorsys.hsv_to_rgb(h, s, v)

        return Image.fromarray((np.stack([r, g, b], axis=-1) * 255).astype("uint8"))

    # endregion
