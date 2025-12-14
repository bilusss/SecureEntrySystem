from polyfactory.factories.pydantic_factory import ModelFactory
from app.schemas import EmployeeBase, EmployeeCreate

class EmployeeFactory(ModelFactory[EmployeeCreate]):
    __model__ = EmployeeCreate


