from .base import Base


class test(Base):

    def __init__(self):
        super().__init__("test")
        self.get('/')(self.hello)
        self.get('/hello')(self.hello)

    def hello(self):
        return "test2 hello"
