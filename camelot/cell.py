class Cell:
    """Cell.
    Defines a cell object with coordinates relative to a left-bottom
    origin, which is also PDFMiner's coordinate space.

    Parameters
    ----------
    x1 : float
        x-coordinate of left-bottom point.

    y1 : float
        y-coordinate of left-bottom point.

    x2 : float
        x-coordinate of right-top point.

    y2 : float
        y-coordinate of right-top point.

    Attributes
    ----------
    lb : tuple
        Tuple representing left-bottom coordinates.

    lt : tuple
        Tuple representing left-top coordinates.

    rb : tuple
        Tuple representing right-bottom coordinates.

    rt : tuple
        Tuple representing right-top coordinates.

    bbox : tuple
        Tuple representing the cell's bounding box using the
        lower-bottom and right-top coordinates.

    left : bool
        Whether or not cell is bounded on the left.

    right : bool
        Whether or not cell is bounded on the right.

    top : bool
        Whether or not cell is bounded on the top.

    bottom : bool
        Whether or not cell is bounded on the bottom.

    text_objects : list
        List of text objects assigned to cell.

    text : string
        Text assigned to cell.

    spanning_h : bool
        Whether or not cell spans/extends horizontally.

    spanning_v : bool
        Whether or not cell spans/extends vertically.
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
        self.text_objects = []
        self.text = ''
        self.spanning_h = False
        self.spanning_v = False

    def add_text(self, text):
        """Adds text to cell.

        Parameters
        ----------
        text : string
        """
        self.text = ''.join([self.text, text])

    def get_text(self):
        """Returns text assigned to cell.

        Returns
        -------
        text : string
        """
        return self.text

    def add_object(self, t_object):
        """Adds PDFMiner text object to cell.

        Parameters
        ----------
        t_object : object
        """
        self.text_objects.append(t_object)

    def get_objects(self):
        """Returns list of text objects assigned to cell.

        Returns
        -------
        text_objects : list
        """
        return self.text_objects

    def get_bounded_edges(self):
        """Returns the number of edges by which a cell is bounded.

        Returns
        -------
        bounded_edges : int
        """
        self.bounded_edges = self.top + self.bottom + self.left + self.right
        return self.bounded_edges
