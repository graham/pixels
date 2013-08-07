from pixelpusher import pixel, bound, is_pixel_blank, multiply_pixel

class PostProcess(object):
	@staticmethod
	def apply(service, new_frame):
		return new_frame

class Blur(PostProcess):
	@staticmethod
	def safe_get_pixel(line, size, index):
		if index < 0 or index >= size:
			return pixel(0, 0, 0)
		return line[index]

	@staticmethod
	def apply_blur(frame_data, service, x_dir):
		new_map = []
		for y in range(0, service.height):
			line = frame_data[(service.width * y):(service.width * (y + 1))]
			new_line = []
			for x in range(0, service.width):
				pix = line[x]
				if is_pixel_blank(pix):
					one_ahead = Blur.safe_get_pixel(line, service.width, (x + (1 * x_dir)))
					two_ahead = Blur.safe_get_pixel(line, service.width, (x + (2 * x_dir)))
					three_ahead = Blur.safe_get_pixel(line, service.width, (x + (3 * x_dir)))
					four_ahead = Blur.safe_get_pixel(line, service.width, (x + (4 * x_dir)))

					if not is_pixel_blank(one_ahead):
						pix = multiply_pixel(one_ahead, 0.05)
					elif not is_pixel_blank(two_ahead):
						pix = multiply_pixel(two_ahead, 0.03)
					elif not is_pixel_blank(three_ahead):
						pix = multiply_pixel(three_ahead, 0.02)
					elif not is_pixel_blank(four_ahead):
						pix = multiply_pixel(four_ahead, 0.01)

				new_line.append(pix)

			new_map += new_line

		return new_map

	@staticmethod
	def apply(service, new_frame):
		return new_frame

class BlurLeft(Blur):
	@staticmethod
	def apply(service, new_frame):
		return Blur.apply_blur(new_frame, service, 1)

class BlurRight(Blur):
	@staticmethod
	def apply(service, new_frame):
		return Blur.apply_blur(new_frame, service, -1)
