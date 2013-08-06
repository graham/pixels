import Image

FONT_WIDTH      = 6
FONT_HEIGHT     = 8
MAX_PIXEL_VALUE = 255

CHARACTERS_INDEX = " ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz01234567890!?."

def convert_pixel(pixel):
    return 1.0 - (pixel[0] + pixel[1] + pixel[2]) / (MAX_PIXEL_VALUE * 3.0)

class PixelFont(object):
    def __init__(self, filename):
        image = Image.open(filename)
        image_data = image.getdata()
        self.image_data = map(convert_pixel, image_data)
        width, height = image.size
        self.image_width = width

    def draw(self, string, start_x, start_y, service, red, green, blue):
        for i in range(0, len(string)):
            character = string[i]
            char_data = self.character_data(character)
            for x in range(0, FONT_WIDTH):
                for y in range(0, FONT_HEIGHT):
                    point_x = (i * FONT_WIDTH) + x + start_x
                    point_y = y + start_y
                    value = char_data[x + (y * FONT_WIDTH)]

                    if point_x < 0 or point_x >= service.width or point_y < 0 or point_y >= service.height: 
                        continue

                    service.set_pixel(point_x, point_y, value * red, value * green, value * blue)

    def character_data(self, character):
        index = CHARACTERS_INDEX.index(character)
        char_start = index * FONT_WIDTH
        array = []
        
        for y in range(0, FONT_HEIGHT):
            start = char_start + (y * (self.image_width - 1))
            end = char_start + (y * (self.image_width - 1)) + FONT_WIDTH

            row_data = self.image_data[(start + y):(end + y)]
            array.extend(row_data)

        return array
