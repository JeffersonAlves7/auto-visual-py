from .AutoVisualimage import AutoVisualImage
from typing import Optional, Self, Literal
from .OpencvFinder import select_region
from .errors import PathNotFoundError
from .types import RetryConfig

import pyautogui
import time
import os
import re


class ImageFinder:
    def __init__(self, path: str):
        self.path = path
        self._cache: dict[str, list[AutoVisualImage]] = {}

    def find(
        self,
        identifier: str,
        use_regex: Optional[bool] = None,
        mode: Optional[Literal["default", "grayscale", "hue_shift"]] = None,
        confidence: Optional[float] = None,
        hue_shift: Optional[float] = None,
        retry_config: Optional[RetryConfig] = None,
    ) -> list[AutoVisualImage]:
        if not use_regex:
            use_regex = False

        cache_key = f"{identifier}|regex={use_regex}|mode={mode}|conf={confidence}|hue={hue_shift}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        results = []

        if use_regex:
            pattern = re.compile(identifier)
            for root, _, files in os.walk(self.path):
                for file_name in files:
                    full_path = os.path.join(root, file_name).replace("\\", "/")
                    if pattern.search(full_path):
                        results.append(
                            AutoVisualImage(
                                src=full_path,
                                mode=mode,
                                confidence=confidence,
                                hue_shift=hue_shift,
                                retry_config=retry_config,
                            )
                        )
        else:
            parts = identifier.split(">")
            for root, _, files in os.walk(self.path):
                for file_name in files:
                    full_path = os.path.join(root, file_name).replace("\\", "/")
                    if parts[-1] in file_name:
                        if len(parts) == 1 or all(p in full_path for p in parts[:-1]):
                            results.append(
                                AutoVisualImage(
                                    src=full_path,
                                    mode=mode,
                                    confidence=confidence,
                                    hue_shift=hue_shift,
                                    retry_config=retry_config,
                                )
                            )

        self._cache[cache_key] = results
        return results

    def find_one(
        self,
        identifier: str,
        use_regex: Optional[bool] = None,
        mode: Optional[Literal["default", "grayscale", "hue_shift"]] = None,
        confidence: Optional[float] = None,
        hue_shift: Optional[float] = None,
        index: Optional[int] = None,
    ) -> AutoVisualImage | None:
        if not use_regex:
            use_regex = False

        if not index:
            index = 0

        results = self.find(
            identifier=identifier,
            use_regex=use_regex,
            mode=mode,
            confidence=confidence,
            hue_shift=hue_shift,
        )

        if 0 <= index < len(results):
            return results[index]

        return None

    def wait_print(
        self,
        output_path: str,
        mode: Optional[Literal["default", "grayscale", "hue_shift"]] = None,
        confidence: Optional[float] = None,
        retry_config: Optional[RetryConfig] = None,
        delay_after: Optional[int] = None,
    ) -> Optional[AutoVisualImage]:
        """
        Pausa o programa, permite que o usuário selecione uma área da tela e retorna um AutoVisualImage com essa imagem.
        """
        print("\n🔍 Prepare a tela onde deseja capturar o botão ou elemento visual.")
        input("Pressione ENTER quando estiver pronto para selecionar a área...")

        file_path: str = os.path.join(self.path, output_path)

        if os.path.exists(file_path):
            return AutoVisualImage(
                src=file_path,
                mode=mode,
                confidence=confidence,
                retry_config=retry_config,
            )

        try:
            left, top, width, height = select_region()
        except Exception as e:
            print(f"❌ Erro ao selecionar a região: {e}")
            return None

        print(f"📸 Região selecionada: ({left}, {top}, {width}, {height})")
        screenshot = pyautogui.screenshot(region=(left, top, width, height))

        screenshot.save(file_path)

        if not delay_after:
            delay_after = 1

        time.sleep(delay_after)

        return AutoVisualImage(
            src=file_path, mode=mode, confidence=confidence, retry_config=retry_config
        )


class ImageBuilder:
    def __init__(self):
        self.path: str | None = None

    def from_dir(self, path: str) -> Self:
        self.path = path
        return self

    def from_s3(self, bucket_path: str, output_dir: str) -> Self:
        try:
            import boto3  # type: ignore
            from botocore.exceptions import NoCredentialsError  # type: ignore
        except ImportError:
            raise ImportError(
                "boto3 is not installed. To use from_s3(), please install it with `pip install boto3`."
            )

        s3 = boto3.client("s3")
        bucket_parts = bucket_path.strip("/").split("/", 1)
        bucket = bucket_parts[0]
        prefix = bucket_parts[1] if len(bucket_parts) > 1 else ""

        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                s3_key = obj["Key"]
                relative_path = s3_key[len(prefix) :].lstrip("/")
                local_path = os.path.join(output_dir, relative_path)

                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                s3.download_file(bucket, s3_key, local_path)

        self.path = output_dir
        return self

    def build(self) -> ImageFinder:
        if not self.path:
            raise PathNotFoundError("Path not set. Use from_dir() or from_s3().")
        return ImageFinder(self.path)
