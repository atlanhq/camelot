class Cell:

    def __init__(self, x1, y1, x2, y2):
        self.lb = (x1, y1)
        self.lt = (x1, y2)
        self.rb = (x2, y1)
        self.rt = (x2, y2)
        self.bbox = (x1, y1, x2, y2)
        self.left = False
        self.right = False
        self.top = False
        self.bottom = False
        self.text = ''
        self.spanning_h = False
        self.spanning_v = False

    def add_text(self, text):
        self.text += text

    def get_text(self):
        return self.text

    def get_bounded_edges(self):
        return self.top + self.bottom + self.left + self.right
