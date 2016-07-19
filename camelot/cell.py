class Cell:
    """Cell

    Parameters
    ----------
    x1 : int

    y1 : int

    x2 : int

    y2 : int

    Attributes
    ----------
    lb : tuple

    lt : tuple

    rb : tuple

    rt : tuple

    bbox : tuple

    left : bool

    right : bool

    top : bool

    bottom : bool

    text : string

    spanning_h : bool

    spanning_v : bool
    """

    def __init__(self, x1, y1, x2, y2):

        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
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
        """Adds text to cell object.

        Parameters
        ----------
        text : string
        """
        self.text = ''.join([self.text, text])

    def get_text(self):
        """Returns text from cell object.

        Returns
        -------
        text : string
        """
        return self.text

    def get_bounded_edges(self):
        """Returns number of edges by which a cell is bounded.

        Returns
        -------
        bounded_edges : int
        """
        return self.top + self.bottom + self.left + self.right
