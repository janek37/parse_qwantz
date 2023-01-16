from PIL import Image

DIM = (735, 500)

MASK_FILENAME = 'img/mask.png'

MASK_IMAGE = Image.open(MASK_FILENAME)


def apply_mask(image: Image):
    all_white = Image.new(mode='RGB', size=DIM, color=(255, 255, 255))
    return Image.composite(image, all_white, MASK_IMAGE)
