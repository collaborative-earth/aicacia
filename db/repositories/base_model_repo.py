

from typing import Any, Generic, TypeVar

from sqlmodel import SQLModel


T = TypeVar('T', bound=SQLModel)


class BaseModelRepository(Generic[T]):
    def __init__(self, model_cls: type[T]) -> None:
        self.model_cls = model_cls  # The SQLModel subclass

    def list_all(self, session) -> list[T]:
        return session.query(self.model_cls).all()

    def delete(self, session, instance: T) -> None:
        session.delete(instance)
        session.commit()

    def get_by_id(self, session, id: Any) -> T | None:
        return session.get(self.model_cls, id)

    def add(self, session, instance: T) -> T:
        session.add(instance)
        session.commit()
        session.refresh(instance)
        return instance

    def update(self, session, instance: T, **kwargs) -> T:
        for key, value in kwargs.items():
            setattr(instance, key, value)
        session.commit()
        session.refresh(instance)
        return instance

    def add_all(self, session, instances: list[T]) -> list[T]:
        session.add_all(instances)
        session.commit()
        for instance in instances:
            session.refresh(instance)
        return instances
