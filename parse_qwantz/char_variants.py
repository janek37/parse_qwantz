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
    ],
    ("Italic", False): [
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
}
