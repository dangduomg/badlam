"""Base, error and essential value classes"""


from abc import ABC
from typing import Self, TYPE_CHECKING, override, cast
from dataclasses import dataclass, field
from collections.abc import Callable

from lark import Token
from lark.tree import Meta

from bl_parser.nodes import _Expr

from .abc_protocols import (
    Result, Exit, SupportsBLCall, SupportsWrappedByPythonFunction
)

if TYPE_CHECKING:
    from ..main import ASTInterpreter


# pylint: disable=too-few-public-methods
# pylint: disable=too-many-public-methods
# pylint: disable=unused-argument


# section Helpers


def cast_to_instance(value: "ExpressionResult") -> "Instance":
    """Cast a value to an instance"""
    return cast("Instance", value)


# section Result


class ExpressionResult(Result, ABC):
    """Expression result base class"""

    def _unimplemented_binary_op(
        self, other: "ExpressionResult", interpreter: "ASTInterpreter",
        meta: Meta | None,
    ) -> "BLError":
        """Unimplemented binary operation stub"""
        match other:
            case BLError():
                return other
        return BLError(cast_to_instance(
            NotImplementedException.new([], interpreter, meta)
        ), meta)

    def get_attr(
        self, attr: str, interpreter: "ASTInterpreter", meta: Meta | None
    ) -> "ExpressionResult":
        """Access an attribute"""
        return BLError(cast_to_instance(
            NotImplementedException.new([], interpreter, meta)
        ), meta)

    def set_attr(
        self, attr: str, value: "ExpressionResult",
        interpreter: "ASTInterpreter", meta: Meta | None
    ) -> "ExpressionResult":
        """Set an attribute"""
        return self._unimplemented_binary_op(value, interpreter, meta)

    def call(
        self, args: list["Value"], interpreter: "ASTInterpreter",
        meta: Meta | None
    ) -> "ExpressionResult":
        """Call self as a function"""
        return BLError(cast_to_instance(
            NotImplementedException.new([], interpreter, meta)
        ), meta)

    def call_cps(
        self, args: list["Value"], interpreter: "ASTInterpreter",
        meta: Meta | None, then: Callable,
    ) -> "ExpressionResult":
        """Call self as a function"""
        return "running", then, (self.call(args, interpreter, meta),)

    def new(
        self, args: list["Value"], interpreter: "ASTInterpreter",
        meta: Meta | None
    ) -> "ExpressionResult":
        """Instantiate an object"""
        return BLError(cast_to_instance(
            NotImplementedException.new([], interpreter, meta)
        ), meta)

    def dump(
        self, interpreter: "ASTInterpreter", meta: Meta | None
    ) -> "ExpressionResult":
        """Conversion to representation for debugging"""
        return BLError(cast_to_instance(
            NotImplementedException.new([], interpreter, meta)
        ), meta)


# section Error


@dataclass(init=False)
class BLError(Exit, ExpressionResult):
    """Error result type"""

    value: "Instance"
    meta: Meta | None = None

    def __init__(self, value: "Instance", meta: Meta | None) -> None:
        self.value = value
        self.value.vars["meta"] = PythonValue(meta)
        self.meta = meta

    @override
    def get_attr(
        self, attr: str, interpreter: "ASTInterpreter", meta: Meta | None
    ) -> Self:
        return self

    @override
    def set_attr(
        self, attr: str, value: ExpressionResult,
        interpreter: "ASTInterpreter", meta: Meta | None,
    ) -> Self:
        return self

    @override
    def call(
        self, args: list["Value"], interpreter: "ASTInterpreter",
        meta: Meta | None
    ) -> Self:
        return self

    @override
    def call_cps(
        self, args: list["Value"], interpreter: "ASTInterpreter",
        meta: Meta | None, then: Callable,
    ) -> Self:
        return self

    @override
    def new(
        self, args: list["Value"], interpreter: "ASTInterpreter",
        meta: Meta | None
    ) -> Self:
        return self

    @override
    def dump(self, interpreter: "ASTInterpreter", meta: Meta | None) -> Self:
        return self


# section Values


class Value(ExpressionResult):
    """Value base class"""

    @override
    def dump(
        self, interpreter: "ASTInterpreter", meta: Meta | None
    ) -> "String | BLError":
        return String("<value>")


@dataclass(frozen=True)
class PythonValue(Value):
    """Python value wrapper"""

    value: object

    @override
    def dump(
        self, interpreter: "ASTInterpreter", meta: Meta | None
    ) -> "String":
        return String(f"<python value {self.value!r}>")


@dataclass(frozen=True)
class Bool(Value):
    """Boolean type"""

    value: bool

    @override
    def dump(
        self, interpreter: "ASTInterpreter", meta: Meta | None
    ) -> "String":
        if self.value:
            return String("true")
        return String("false")


BOOLS = Bool(False), Bool(True)


@dataclass(frozen=True)
class Null(Value):
    """Null value"""

    @override
    def dump(
        self, interpreter: "ASTInterpreter", meta: Meta | None
    ) -> "String":
        return String("null")


NULL = Null()


@dataclass(frozen=True)
class String(Value):
    """String type"""

    value: str

    @override
    def dump(
        self, interpreter: "ASTInterpreter", meta: Meta | None
    ) -> "String":
        return String(f"{self.value!r}")


# section Functions


@dataclass(frozen=True)
class Call:
    """Call site type for tracebacks"""
    function: SupportsBLCall
    meta: Meta | None


@dataclass
class PythonFunction(Value):
    """Python function wrapper type"""

    function: SupportsWrappedByPythonFunction
    this: "Instance | None" = None

    @override
    def call(
        self, args: list[Value], interpreter: "ASTInterpreter",
        meta: Meta | None
    ) -> ExpressionResult:
        return self.function(meta, interpreter, self.this, *args)

    def bind(self, this: "Instance") -> "PythonFunction":
        """Return a version of PythonFunction bound to an object"""
        return PythonFunction(self.function, this)

    @override
    def dump(
        self, interpreter: "ASTInterpreter", meta: Meta | None
    ) -> String:
        return String(f"<python function {self.function!r}>")


@dataclass
class BLFunction(Value):
    """baba-lang function type"""

    form_arg: Token
    body: _Expr
    env: "Env | None"
    src: str
    name: String = String("λ")
    this: "Instance | None" = None

    @override
    def call(
        self, args: list[Value], interpreter: "ASTInterpreter",
        meta: Meta | None
    ) -> ExpressionResult:
        return self.call_cps(args, interpreter, meta, lambda x: x)

    def call1_cps(
        self, arg: Value, interpreter: "ASTInterpreter",
        meta: Meta | None,
    ) -> ExpressionResult:
        """Call using CPS with only 1 argument"""
        return self.call([arg], interpreter, meta)

    @override
    def call_cps(
        self, args: list[Value], interpreter: "ASTInterpreter",
        meta: Meta | None, then: Callable,
    ):
        """Call using CPS"""
        # Add the function to the "call stack"
        interpreter.calls.append(Call(self, meta))
        # Create an environment (call frame)
        old_env = interpreter.locals
        env = Env(interpreter, parent=self.env)
        # Populate it with arguments
        form_arg = self.form_arg
        try:
            env.new_var(form_arg, args[0])
        except ValueError:
            return "running", then, (BLError(cast_to_instance(
                IncorrectTypeException.new([], interpreter, meta)
            ), meta),)
        # If function is bound to an object, add that object
        if self.this is not None:
            env.new_var("this", self.this)
        # Run the body
        interpreter.locals = env
        res = interpreter.visit(self.body)
        # Clean it up
        interpreter.locals = old_env
        # Return!
        match res:
            case Value():
                interpreter.calls.pop()
                return "running", then, (res,)
            case BLError():
                return "running", then, (res,)
        return "running", then, (BLError(cast_to_instance(
            NotImplementedException.new([], interpreter, meta)
        ), meta),)

    def bind(self, this: "Instance") -> "BLFunction":
        """Return a version of BLFunction bound to an object"""
        return BLFunction(
            self.form_arg, self.body, self.env, self.src, this
        )

    @override
    def dump(self, interpreter: "ASTInterpreter", meta: Meta | None) -> String:
        if self.this is not None:
            this_to_str = self.this.dump(interpreter, meta).value
            return String(f"<method '{self.name}' bound to {this_to_str}>")
        return String(self.src)


# section OOP


@dataclass
class Class(Value):
    """baba-lang class"""

    name: String
    super: "Class | None" = None
    vars: dict[str, Value] = field(default_factory=dict)

    @override
    def get_attr(
        self, attr: str, interpreter: "ASTInterpreter", meta: Meta | None
    ) -> ExpressionResult:
        try:
            return self.vars[attr]
        except KeyError:
            if self.super is not None:
                return self.super.get_attr(attr, interpreter, meta)
            return BLError(cast_to_instance(
                AttrNotFoundException.new([], interpreter, meta)
            ), meta)

    @override
    def new(
        self, args: list[Value], interpreter: "ASTInterpreter",
        meta: Meta | None
    ) -> ExpressionResult:
        inst = Instance(self, {})
        if "__init__" in self.vars:  # __init__ is the constructor method
            constr = inst.get_attr("__init__", interpreter, meta)
            match res := constr.call(args, interpreter, meta):
                case BLError():
                    return res
        return inst

    @override
    def dump(self, interpreter: "ASTInterpreter", meta: Meta | None) -> String:
        return String(f"<class {self.name.value}>")


# Base class for all objects
ObjectClass = Class(String("Object"))


# Base class for all exceptions


def exc_init(
    meta: Meta | None, interpreter: "ASTInterpreter", this: "Instance | None",
    /, msg: String, *_
) -> Null | BLError:
    """Initialize an exception"""
    if this is not None:
        this.vars["msg"] = msg
        return NULL
    return BLError(cast_to_instance(
        NotImplementedException.new([], interpreter, meta)
    ), meta)


def exc_dump(
    meta: Meta | None, interpreter: "ASTInterpreter", this: "Instance | None",
    /, *_
) -> String | BLError:
    """Debugging representation of exception"""
    if this is not None:
        return String(f"{this.class_.name.value}")
    return BLError(cast_to_instance(
        NotImplementedException.new([], interpreter, meta)
    ), meta)


exc_methods: dict[str, Value] = {
    "__init__": PythonFunction(exc_init),
    "__dump__": PythonFunction(exc_dump),
}

ExceptionClass = Class(String("Exception"), ObjectClass, exc_methods)

# Exceptions
NotImplementedException = Class(
    String("NotImplementedException"), ExceptionClass
)
AttrNotFoundException = Class(String("AttrNotFoundException"), ExceptionClass)
VarNotFoundException = Class(String("VarNotFoundException"), ExceptionClass)
IncorrectTypeException = Class(
    String("IncorrectTypeException"), ExceptionClass
)


@dataclass(init=False)
class Instance(Value):
    """baba-lang instance"""

    # pylint: disable=too-many-public-methods

    class_: Class
    vars: dict[str, Value]

    def __init__(self, class_: Class, vars_: dict[str, Value]):
        self.class_ = class_
        self.vars = vars_

    @override
    def get_attr(
        self, attr: str, interpreter: "ASTInterpreter", meta: Meta | None
    ) -> ExpressionResult:
        try:
            return self.vars[attr]
        except KeyError:
            match res := self.class_.get_attr(attr, interpreter, meta):
                case SupportsBLCall():
                    return res.bind(self)
                case _:
                    return res

    @override
    def set_attr(
        self, attr: str, value: ExpressionResult,
        interpreter: "ASTInterpreter", meta: Meta | None,
    ) -> ExpressionResult:
        match value:
            case BLError():
                return value
            case Value():
                self.vars[attr] = value
                return value
        return super().set_attr(attr, value, interpreter, meta)

    @override
    def dump(
        self, interpreter: "ASTInterpreter", meta: Meta | None
    ) -> String | BLError:
        res = self._call_method_if_exists("__dump__", [], interpreter, meta)
        if not isinstance(res, String):
            if isinstance(res, BLError):
                if res.value.class_ == AttrNotFoundException:
                    class_to_str = self.class_.dump(interpreter, meta).value
                    return String(f"<object of {class_to_str}>")
                return res
            return BLError(cast_to_instance(
                IncorrectTypeException.new([], interpreter, meta)
            ), meta)
        return res

    def _call_method_if_exists(
        self, name: str, args: list[Value], interpreter: "ASTInterpreter",
        meta: Meta | None
    ) -> ExpressionResult:
        match res := self.get_attr(name, interpreter, meta):
            case SupportsBLCall():
                return res.bind(self).call(args, interpreter, meta)
        return res


# section Environment


@dataclass(frozen=True)
class Var:
    """Interpreter immutable binding"""
    value: Value


class Env:
    """Interpreter environment"""

    interpreter: "ASTInterpreter"
    vars: dict[str, Var]
    parent: "Env | None"

    def __init__(
        self, interpreter: "ASTInterpreter",
        vars_: dict[str, Var] | None = None, parent: "Env | None" = None,
    ):
        if vars_ is None:
            self.vars = {}
        else:
            self.vars = vars_
        self.interpreter = interpreter
        self.parent = parent

    def new_var(self, name: str, value: Value) -> None:
        """Create a child environment with a new variable"""
        return Env(self.interpreter, self.vars | {name: Var(value)}, self)

    def get_var(self, name: str, meta: Meta | None) -> ExpressionResult:
        """Retrieve the value of a variable"""
        resolve_result = self.resolve_var(name, meta)
        match resolve_result:
            case Var(value=value):
                return value
            case BLError():
                return resolve_result

    def resolve_var(self, name: str, meta: Meta | None) -> Var | BLError:
        """Resolve a variable name"""
        if name in self.vars:
            return self.vars[name]
        if self.parent is not None:
            return self.parent.resolve_var(name, meta)
        return BLError(cast_to_instance(
            VarNotFoundException.new([], self.interpreter, meta)
        ), meta)

    def copy(self) -> "Env":
        """Copy the environment (for capturing variables in closures)"""
        return Env(self.interpreter, self.vars.copy(), self.parent)
