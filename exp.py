import abc


class Base(abc.ABC):
    @abc.abstractmethod
    def method() -> None:
        ...


class One(Base):
    def method() -> None:
        print('ok')


one = One()
print(one)
