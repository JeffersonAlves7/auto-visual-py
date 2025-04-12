from auto_visual_py import ImageBuilder, ImageFinder


imageFinder: ImageFinder = ImageBuilder().from_dir("img").build()

btn_user = imageFinder.find_one(
    "dominio>header>navbar>button-user", mode="grayscale", confidence=0.6
)

if btn_user:
    btn_user.click()

btn_user_info = imageFinder.wait_print(
    "dominio/header/navbar/user/action/user-info.png", confidence=0.8
)

if btn_user_info:
    btn_user_info.click()
