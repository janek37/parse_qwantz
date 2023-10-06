from parse_qwantz.box import Box
from parse_qwantz.match_lines import Character
from parse_qwantz.pixels import Pixel

# size and offset
PANELS = [
    ((239, 239), (3, 2)),
    ((126, 239), (246, 2)),
    ((358, 239), (375, 2)),
    ((190, 239), (3, 244)),
    ((295, 239), (196, 244)),
    ((239, 239), (494, 244)),
]

FOOTER = ((735, 12), (0, 488))

CHARACTERS = [
    [Character('T-Rex', (Box(Pixel(104, 90), Pixel(170, 238)),))],
    [
        Character('T-Rex', (
            Box(Pixel(30, 105), Pixel(75, 119)),
            Box(Pixel(4, 119), Pixel(105, 150)),
            Box(Pixel(4, 150), Pixel(60, 238)),
        )),
    ],
    [
        Character('T-Rex', (Box(Pixel(80, 55), Pixel(115, 213)), Box(Pixel(115, 75), Pixel(130, 90)))),
        Character('Dromiceiomimus', (Box(Pixel(325, 146), Pixel(357, 238)), Box(Pixel(250, 180), Pixel(325, 185)))),
    ],
    [
        Character('T-Rex', (Box(Pixel(0, 65), Pixel(35, 190)),)),
        Character('Utahraptor', (Box(Pixel(103, 81), Pixel(138, 165)), Box(Pixel(138, 140), Pixel(165, 180)))),
        Character('Girl', (Box(Pixel(0, 213), Pixel(8, 238)),)),
    ],
    [
        Character('T-Rex', (
            Box(Pixel(40, 70), Pixel(90, 103)),
            Box(Pixel(40, 104), Pixel(70, 140)),
            Box(Pixel(40, 141), Pixel(80, 180)),
        )),
        Character('T-Rex', (
            Box(Pixel(130, 155), Pixel(133, 210), inactive_sides=("left", "top", "bottom")),
            Box(Pixel(100, 197), Pixel(130, 213)),
        )),
        Character('Utahraptor', (
            Box(Pixel(198, 77), Pixel(233, 145)),
            Box(Pixel(225, 145), Pixel(250, 190)),
            Box(Pixel(185, 115), Pixel(198, 125)),
        )),
    ],
    [
        Character('T-Rex', (
            Box(Pixel(80, 64), Pixel(134, 84)),
            Box(Pixel(80, 84), Pixel(100, 169)),
            Box(Pixel(100, 84), Pixel(120, 120)),
            Box(Pixel(100, 110), Pixel(125, 120)),
        )),
    ],
]
