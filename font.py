import Image

FONT_WIDTH      = 6
FONT_HEIGHT     = 8

CHARACTERS_INDEX = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz01234567890"

class Font(object):
    def __init__(self, filename):
        image = Image.open(filename)
        self.image_data = image.getdata()
        width, height = image.size
        self.image_width = width

    def draw(self, string, service, red, green, blue):
        pass

    def character_data(self, character):
        index = CHARACTERS_INDEX.index(character)
        char_start = index * FONT_WIDTH
        array = []
        
        for y in range(0, FONT_HEIGHT):
            start = char_start + (y * (self.image_width - 1))
            end = char_start + (y * (self.image_width - 1)) + FONT_WIDTH

            for x in range(start, end): 
                bit_data = self.image_data[x + y]
                if bit_data[0] > 0: 
                    array.append(1)
                else:
                    array.append(0)

        return array

font = Font("font.tif")
char_data = font.character_data('0')

for y in range(0, FONT_HEIGHT):
    line = "" 
    for x in range(0, FONT_WIDTH):
        character = "*"
        if char_data[(y * FONT_WIDTH) + x] > 0:
            character = " " 
        line += character
        line += " "
    print line 
