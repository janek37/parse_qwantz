from PIL import Image

from character_shapes import REGULAR_SHAPES, REGULAR_WIDTH, REGULAR_HEIGHT, get_regular_bitmask


def get_text_blocks(image: Image):
    lines = get_text_lines(image)
    while lines:
        new_block = [lines[0]]
        new_lines = []
        for x, y, line in lines[1:]:
            x0, y0, line0 = new_block[-1]
            x1 = x0 + REGULAR_WIDTH * len(line0)
            x_end = x * REGULAR_WIDTH * len(line)
            interval0, interval1 = sorted([(x, x_end), (x0, x1)])
            if y == y0 + REGULAR_HEIGHT and interval0[1] > interval1[0]:
                new_block.append((x, y, line))
            else:
                new_lines.append((x, y, line))
        lines = new_lines
        yield new_block


def get_text_lines(image: Image):
    lines = []
    for y in range(image.height - REGULAR_HEIGHT + 1):
        x = 0
        while x < image.width - REGULAR_WIDTH + 1:
            for l_x, l_y, line in lines:
                if l_x - REGULAR_WIDTH < x <= l_x and y - l_y < REGULAR_HEIGHT:
                    x = l_x + REGULAR_WIDTH * len(line)
                    break
            if x >= image.width - REGULAR_WIDTH + 1:
                break
            bitmask = get_regular_bitmask(x, y, image=image)
            if bitmask in REGULAR_SHAPES:
                line = get_line(x, y, image)
                if line not in ".'`,|":
                    lines.append((x, y, line))
                    x += REGULAR_WIDTH * len(line)
            x += 1
    return lines


def get_line(x: int, y: int, image: Image):
    bitmask = get_regular_bitmask(x, y, image=image)
    line = REGULAR_SHAPES[bitmask]
    spaces = 0
    while True:
        x += REGULAR_WIDTH
        if x > image.width - REGULAR_WIDTH:
            break
        bitmask = get_regular_bitmask(x, y, image=image)
        if bitmask == 0:
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
        elif bitmask in REGULAR_SHAPES:
            if spaces > 0:
                line += ' ' * spaces
                spaces = 0
            line += REGULAR_SHAPES[bitmask]
        else:
            break
    return line
    # parse next line etc. (there may be some offset)


if __name__ == '__main__':
    import sys
    for block in get_text_blocks(Image.open(sys.argv[1])):
        print(' '.join(line for x, y, line in block).replace('  ', ' '))
