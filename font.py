import Image

FONT_WIDTH      = 6
FONT_HEIGHT     = 8
MAX_PIXEL_VALUE = 255

CHARACTERS_INDEX = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz01234567890"

def convert_pixel(pixel):
    return (pixel[0] + pixel[1] + pixel[2]) / (MAX_PIXEL_VALUE * 3.0)

class Font(object):
    def __init__(self, filename):
        image = Image.open(filename)
        image_data = image.getdata()
        self.image_data = map(convert_pixel, image_data)
        width, height = image.size
        self.image_width = width

    def draw(self, string, service, red, green, blue):
        

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

font = Font("font.tif")
char_data = font.character_data('6')

for y in range(0, FONT_HEIGHT):
    line = "" 
    for x in range(0, FONT_WIDTH):
        character = "*"
        if char_data[(y * FONT_WIDTH) + x] > 0:
            character = " " 
        line += character
        line += " "
    print line 
