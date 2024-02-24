VARIANTS = {
    ("Regular", False): [
        (
            "!",
            [
                0,
                0b0100000000000,
                0,
                0b0011111001000,
                0,
                0,
                0,
                0,
            ],
        ),
        (
            '"',
            [
                0,
                0,
                0b0111000000000,
                0,
                0,
                0b1110000000000,
                0,
                0,
            ],
        ),
        (
            "'",
            [
                0,
                0,
                0,
                0b0110000000000,
                0,
                0,
                0,
                0,
            ],
        ),
        (
            ",",
            [
                0,
                0b0000000000010,
                0b0000000011000,
                0b0000000011100,
                0,
                0,
                0,
                0,
            ],
        ),
        (
            ",",
            [
                0,
                0,
                0b0000000011000,
                0b0000000011100,
                0,
                0,
                0,
                0,
            ],
        ),
        (
            ",",
            [
                0,
                0,
                0b0000000011001,
                0b0000000011100,
                0,
                0,
                0,
                0,
            ],
        ),
        (
            ".",
            [
                0,
                0,
                0b0000000011000,
                0b0000000011000,
                0,
                0b0000000000100,
                0,
                0,
            ],
        ),
        (
            "-",
            [
                0,
                0b0000001000000,
                0b0000001000000,
                0b0000001000000,
                0b0000001000000,
                0b0000001000000,
                0,
                0,
            ],
        ),
        (
            "D",
            [
                0,
                0b0011111111000,
                0b0010000001000,
                0b0011000001000,
                0b0011000001000,
                0b0001000010000,
                0b0000111100000,
                0,
            ]
        ),
        (
            "H",
            [
                0,
                0b0001111111100,
                0b0000010000000,
                0b0000010000000,
                0b0000010000000,
                0b0000010000000,
                0b0001111111100,
                0,
            ],
        ),
        (
            "I",
            [
                0,
                0,
                0,
                0b0010000001000,
                0b0011111111000,
                0b0010000001000,
                0b0010000001000,
                0,
            ],
        ),
        (
            "a",
            [
                0,
                0b0000000110000,
                0b0001001001000,
                0b0001001001000,
                0b0001001001000,
                0b0000111111000,
                0b0000011001000,
                0,
            ],
        ),
        (
            "b",
            [
                0,
                0b1111111111100,
                0b0000010001000,
                0b0000100000100,
                0b0000100000100,
                0b0000100000100,
                0b0000011111000,
                0,
            ],
        ),
        (
            "b",
            [
                0,
                0b0111111111000,
                0b0000100010000,
                0b1001000001000,
                0b0001000001000,
                0b0001000001000,
                0b0000111110000,
                0,
            ],
        ),
        (
            "b",
            [
                0,
                0b0111111111000,
                0b0000100010000,
                0b0001000001000,
                0b0001000001000,
                0b0001000001000,
                0b0000111110000,
                0,
            ],
        ),
        (
            "d",
            [
                0,
                0b0000111110000,
                0b0001000001000,
                0b0000100000100,
                0b0000100000100,
                0b0000010001000,
                0b0111111111100,
                0,
            ],
        ),
        (
            "d",
            [
                0,
                0b0000111110000,
                0b0001000001000,
                0b0001000001000,
                0b0001000001000,
                0b0000100010000,
                0b0111111111000,
                0,
            ],
        ),
        (
            "e",
            [
                0,
                0b0000011110000,
                0b0001101001000,
                0b0001101001000,
                0b0001001001000,
                0b0001001001000,
                0b0000111001000,
                0,
            ],
        ),
        (
            "e",
            [
                0,
                0b0001111110000,
                0b0001101001000,
                0b0001001001000,
                0b0001001001000,
                0b0001001001000,
                0b0000111001000,
                0,
            ],
        ),
        (
            "f",
            [
                0b0001000000000,
                0b0111111111000,
                0b1001000000000,
                0b1001000000000,
                0b1001000000000,
                0b1001000000000,
                0b0000000000000,
                0,
            ],
        ),
        (
            "g",
            [
                0,
                0b0000111110000,
                0b0001000001000,
                0b0001000001001,
                0b0001000001001,
                0b0000100010001,
                0b0001111111110,
                0,
            ],
        ),
        (
            "g",
            [
                0,
                0b0000111110010,
                0b0001000001010,
                0b0001000001010,
                0b0001000001010,
                0b0000100010100,
                0b0001111111100,
                0,
            ],
        ),
        (
            "g",
            [
                0,
                0b0000111110000,
                0b0001000001000,
                0b0001000001000,
                0b0001000001000,
                0b0000100010000,
                0b0001111111110,
                0,
            ],
        ),
        (
            "g",
            [
                0,
                0b0000111110000,
                0b0001000001000,
                0b0001000001000,
                0b0001000001000,
                0b0000100010000,
                0b0001111111011,
                0,
            ],
        ),
        (
            "h",
            [
                0,
                0b0111111111000,
                0b0000100000000,
                0b0001000000000,
                0b0001000000000,
                0b0001000000000,
                0b0000111111000,
                0,
            ],
        ),
        (
            "i",
            [
                0,
                0,
                0b0001000000000,
                0b1101000000000,
                0b1101111111000,
                0,
                0,
                0,
            ],
        ),
        (
            "i",
            [
                0,
                0b0001000000000,
                0b0001000000000,
                0b0101000000000,
                0b0101111111000,
                0b0001000000000,
                0,
                0,
            ],
        ),
        (
            "i",
            [
                0,
                0b0001000000000,
                0b0001000000000,
                0b0101000000000,
                0b0101111111000,
                0,
                0,
                0,
            ],
        ),
        (
            "j",
            (
                0,
                0b0001000000000,
                0b0001000000000,
                0b1101000000000,
                0b1101111111110,
                0,
                0,
                0,
            )
        ),
        (
            "k",
            [
                0,
                0b0111111111000,
                0b0000001000000,
                0b0000010100000,
                0b0000100010000,
                0b0001000001000,
                0,
                0,
            ],
        ),
        (
            "l",
            [
                0,
                0b1001100000000,
                0b1001100000000,
                0b1001100000000,
                0b1111111111000,
                0,
                0,
                0,
            ],
        ),
        (
            "m",
            [
                0b0001111111000,
                0b0000100000000,
                0b0001000000000,
                0b0001111111000,
                0b0001000000000,
                0b0001000000000,
                0b0001111111000,
            ],
        ),
        (
            "o",
            [
                0b0000111110000,
                0b0001000001000,
                0b0001000001000,
                0b0001000001000,
                0b0001000001000,
                0b0000111100000,
                0,
                0b0000000000100,
            ],
        ),
        (
            "p",
            [
                0b0000000000010,
                0b0001111111110,
                0b0000100010000,
                0b0001000001000,
                0b0001000001000,
                0b0001000001000,
                0b0000111110000,
                0,
            ],
        ),
        (
            "p",
            [
                0b0000000000000,
                0b0001111111110,
                0b0000100010000,
                0b0001000001000,
                0b0001000001000,
                0b0001000001000,
                0b0000111110000,
                0,
            ],
        ),
        (
            "r",
            [
                0,
                0b0001111111110,
                0b0000100000110,
                0b0001000000000,
                0b0001000000000,
                0b0001100000000,
                0,
                0,
            ],
        ),
        (
            "s",
            [
                0,
                0b0000101000100,
                0b0001001000100,
                0b0001000100100,
                0b0001000100100,
                0b0001000011000,
                0,
                0,
            ],
        ),
        (
            "s",
            [
                0b0000000001000,
                0b0000110001000,
                0b0001010001000,
                0b0001001001000,
                0b0001001001000,
                0b0001000110000,
                0,
                0,
            ],
        ),
        (
            "t",
            [
                0b0001000000000,
                0b0001000000000,
                0b0001000000000,
                0b0011111110000,
                0b0001000001000,
                0b0001000001000,
                0b0001000001000,
                0,
            ],
        ),
        (
            "t",
            [
                0b0001000000000,
                0b0001000000000,
                0b0011111110000,
                0b0001000001000,
                0b0001000001000,
                0b0000000001000,
                0,
                0,
            ],
        ),
        (
            "t",
            [
                0,
                0b0001000000000,
                0b0011111110000,
                0b0001000001000,
                0b0001000001000,
                0b0001000001000,
                0,
                0,
            ],
        ),
        (
            "t",
            [
                0,
                0,
                0b0011111110000,
                0b0001000001000,
                0b0001000001000,
                0b0001000001000,
                0,
                0,
            ],
        ),
        (
            "u",
            [
                0,
                0b0001111110000,
                0b0000000001000,
                0b0000000001000,
                0b0000000001000,
                0b0000000010000,
                0b0000111111000,
                0,
            ],
        ),
        (
            "v",
            [
                0,
                0b0000111000000,
                0b0000000110000,
                0b0000000001000,
                0b0000000110000,
                0b0000111000000,
                0b0001000000000,
                0,
            ],
        ),
        (
            "x",
            [
                0b0000000000000,
                0b0001000001000,
                0b0000100010000,
                0b0000011100000,
                0b0000011100000,
                0b0000100010000,
                0b0001000000000,
                0b0000000000000,
            ],
        ),
        (
            "y",
            [
                0b0001000000000,
                0b0000110000000,
                0b0000001100000,
                0b0000000011100,
                0b0000000011000,
                0b0000001100000,
                0b0000110000000,
                0b0001000000000,
            ],
        ),
        (
            "y",
            [
                0b0001000000001,
                0b0000110000001,
                0b0000001101011,
                0b0000000011110,
                0b0000000011000,
                0b0000001100000,
                0b0000110000000,
                0b0000000000000,
            ],
        ),
        (
            "y",
            [
                0b0001000000000,
                0b0000110000001,
                0b0000001100011,
                0b0000000011110,
                0b0000000011000,
                0b0000001100000,
                0b0000110000000,
                0b0001000000000,
            ],
        ),
        (
            "y",
            [
                0b0001000000000,
                0b0000110000000,
                0b0000001100010,
                0b0000000111110,
                0b0000000111000,
                0b0000001100000,
                0b0000110000000,
                0b0001000000000,
            ],
        ),
        (
            "y",
            [
                0b0001000000000,
                0b0000110000000,
                0b0000001100010,
                0b0000000011110,
                0b0000000011000,
                0b0000001100000,
                0b0000110000000,
                0b0001000000000,
            ],
        ),
        (
            "y",
            [
                0b0001000000001,
                0b0000110000001,
                0b0000001100011,
                0b0000000011110,
                0b0000000011000,
                0b0000000110000,
                0b0000011000000,
                0b0000100000000,
            ],
        ),
        (
            "°",
            [
                0,
                0b0011100000000,
                0b0100010000000,
                0b0100010000000,
                0b0100010000000,
                0b0011100000000,
                0,
                0,
            ]
        ),
    ],
    ("Regular", True): [
        (
            "!",
            [
                0,
                0,
                0,
                0b0111111011000,
                0b0111111011000,
                0,
                0,
                0,
                0,
            ],
        ),
        (
            "-",
            [
                0,
                0b0000001000000,
                0b0000001000000,
                0b0000001000000,
                0b0000001000000,
                0b0000001000000,
                0b0000001000000,
                0,
                0,
            ],
        ),
        (
            "L",
            [
                0,
                0b0011111111000,
                0b0011111111000,
                0b0000000001000,
                0b0000000001000,
                0b0000000001000,
                0b0000000001000,
                0,
                0,
            ],
        ),
        (
            "L",
            [
                0,
                0b0011111111000,
                0b0011111111000,
                0b0000000001000,
                0b0000000001000,
                0b0000000001000,
                0,
                0,
                0,
            ],
        ),
        (
            "S",
            [
                0b0000000000100,
                0b0001100001000,
                0b0011110001000,
                0b0010010001000,
                0b0010010001000,
                0b0010011001000,
                0b0010001111000,
                0b0010000110000,
                0,
            ],
        ),
        (
            "p",
            [
                0,
                0b0001111111110,
                0b0001111111110,
                0b0001100011000,
                0b0001000001100,
                0b0001000001100,
                0b0001111111000,
                0b0000111110000,
                0,
            ],
        ),
        (
            "*",
            [
                0,
                0b0010000000000,
                0b0011110000000,
                0b0111110000000,
                0b0111100000000,
                0b0111110000000,
                0b0011110000000,
                0b0010000000000,
                0,
            ],
        ),
    ],
    ("Italic", False): [
        (
            "e",
            [
                0,
                0b000101110000,
                0b000111000000,
                0b001001001000,
                0b001001001000,
                0b001101001000,
                0b00011001000,
                0,
            ],
        ),
        (
            "y",
            [
                0b001000000000,
                0b001100000001,
                0b000011110001,
                0b000000001110,
                0b000000111000,
                0b000001000000,
                0b000110000000,
                0b001000000000,
            ],
        ),
        (
            "E",
            [
                0,
                0b0011101111000,
                0b0010011001000,
                0b0010001001000,
                0b0010001001000,
                0b0010001001000,
                0b0000000001000,
                0,
            ],
        ),
        (
            "S",
            [
                0,
                0b0011100001000,
                0b0010010001000,
                0b0010010001000,
                0b0010010001000,
                0b0010001011000,
                0b0000000100000,
                0,
            ]
        )
    ],
    ("Mini", False): [
        (
            ",",
            [
                0,
                0,
                0b000000110,
                0,
                0,
            ],
        ),
    ],
    ("Small", False): [
        (
            "b",
            [
                0,
                0b11111111100,
                0b00001000100,
                0b00010000100,
                0b00010000100,
                0b00001111000,
                0,
            ],
        ),
        (
            "-",
            [
                0,
                0b00000100000,
                0b00000100000,
                0b00000100000,
                0b00000100000,
                0,
                0,
            ]
        )
    ],
}
