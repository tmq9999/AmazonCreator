class ToolHelper:
    
	def generator_positions(self, thread):
		POPUP_WIDTH = 400
		POPUP_HEIGHT = 300
		COLUMNS = 4
		MARGIN_X = 10
		MARGIN_Y = 10
		START_X = 0
		START_Y = 0
		positions = []
		for i in range(thread):
			row = i // COLUMNS
			col = i % COLUMNS
			x = START_X + col * (POPUP_WIDTH + MARGIN_X)
			y = START_Y + row * (POPUP_HEIGHT + MARGIN_Y)
			positions.append((x, y))
		return positions