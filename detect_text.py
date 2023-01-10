from PIL import Image

from character_shapes import REGULAR_FONT, Font


def get_text_blocks(image: Image, font: Font):
    lines = get_text_lines(image, font)
    while lines:
        new_block = [lines[0]]
        new_lines = []
        for x, y, line in lines[1:]:
            x0, y0, line0 = new_block[-1]
            x1 = x0 + font.width * len(line0)
            x_end = x * font.width * len(line)
            interval0, interval1 = sorted([(x, x_end), (x0, x1)])
            if y == y0 + font.height and interval0[1] > interval1[0]:
                new_block.append((x, y, line))
            else:
                new_lines.append((x, y, line))
        lines = new_lines
        yield new_block


def get_text_lines(image: Image, font: Font):
    lines = []
    for y in range(image.height - font.height + 1):
        x = 0
        while x < image.width - font.width + 1:
            for l_x, l_y, line in lines:
                if l_x - font.width < x <= l_x and y - l_y < font.height:
                    x = l_x + font.width * len(line)
                    break
            if x >= image.width - font.width + 1:
                break
            char = font.get_char(x, y, image)
            if char not in (' ', None):
                line = get_line(x, y, image, font)
                if line not in ".'`,|":
                    lines.append((x, y, line))
                    x += font.width * len(line)
            x += 1
    return lines


def get_line(x: int, y: int, image: Image, font: Font):
    line = font.get_char(x, y, image=image)
    spaces = 0
    while True:
        x += font.width
        if x > image.width - font.width:
            break
        char = font.get_char(x, y, image)
        if char == ' ':
            spaces += 1
            if spaces > 2:
                break
            if spaces == 2:
                last_char = line[-1]
                if last_char == '"':
                    if len(line) < 1:
                        break
                    last_char = line[-2]
                if last_char not in '.!?':
                    break
        elif char is not None:
            if spaces > 0:
                line += ' ' * spaces
                spaces = 0
            line += char
        else:
            break
    return line


if __name__ == '__main__':
    import sys
    for block in get_text_blocks(Image.open(sys.argv[1]), REGULAR_FONT):
        print(' '.join(line for x, y, line in block).replace('  ', ' '))
    # for block in get_text_blocks(Image.open(sys.argv[1]), BOLD_FONT):
    #     print(' '.join(line for x, y, line in block).replace('  ', ' '))
