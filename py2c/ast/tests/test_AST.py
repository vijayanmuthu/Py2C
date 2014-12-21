"""Tests for the AST in py2c.ast
"""

#------------------------------------------------------------------------------
# Py2C - A Python to C++ compiler
# Copyright (C) 2014 Pradyun S. Gedam
#------------------------------------------------------------------------------

from py2c import ast

from py2c.tests import Test
from nose.tools import assert_raises, assert_equal, assert_not_equal


#------------------------------------------------------------------------------
# A bunch of nodes used during testing
#------------------------------------------------------------------------------
class BasicNode(ast.AST):
    """Basic node
    """
    _fields = [
        ('f1', int, ast.NEEDED),
    ]


class BasicNodeCopy(ast.AST):
    """Equivalent but not equal to BasicNode
    """
    _fields = [
        ('f1', int, ast.NEEDED),
    ]


class AllIntModifersNode(ast.AST):
    """Node with all modifiers
    """
    _fields = [
        ('f1', int, ast.NEEDED),
        ('f2', int, ast.OPTIONAL),
        ('f3', int, ast.ZERO_OR_MORE),
        ('f4', int, ast.ONE_OR_MORE),
    ]


class ParentNode(ast.AST):
    """Node with another node as child
    """
    _fields = [
        ('child', BasicNode, ast.NEEDED),
    ]


class InvalidModifierNode(ast.AST):
    """Node with invalid modifier
    """
    _fields = [
        ('f1', int, None),
    ]


#------------------------------------------------------------------------------
# Tests
#------------------------------------------------------------------------------
class TestASTNode(Test):
    """Tests for behavior of ast.AST subclasses
    """

    def check_valid_initialization(self, cls, args, kwargs, expected_dict):
        try:
            node = cls(*args, **kwargs)
        except ast.WrongTypeError:
            self.fail("Unexpectedly raised exception")
        else:
            for name, value in expected_dict.items():
                assert_equal(getattr(node, name), value)

    def test_valid_initialization(self):
        """Tests ast.AST.__init__'s behaviour on valid initialization
        """
        yield from self.yield_tests(self.check_valid_initialization, [
            (BasicNode, [], {}, {}),
            (BasicNode, [1], {}, {"f1": 1}),
            (BasicNode, [], {"f1": 1}, {"f1": 1}),
            (AllIntModifersNode, [1, None, (), (2,)], {}, {
                "f1": 1, "f2": None, "f3": (), "f4": (2,)
            }),
            (AllIntModifersNode, [1, 2, (3, 4, 5), (6, 7, 8)], {}, {
                "f1": 1, "f2": 2, "f3": (3, 4, 5), "f4": (6, 7, 8),
            })
        ])

    def check_invalid_initialization(self, cls, args, kwargs, error, required_phrases):
        with assert_raises(error) as context:
            cls(*args, **kwargs)

        self.assert_message_contains(context.exception, required_phrases)

    def test_invalid_initialization(self):
        """Tests ast.AST.__init__'s behaviour on invalid initialization
        """
        yield from self.yield_tests(self.check_invalid_initialization, [
            (AllIntModifersNode, [1], {}, ast.WrongTypeError, "0 or 4 positional")
        ])

    def check_valid_assignment(self, attr, value):
        node = AllIntModifersNode()

        try:
            setattr(node, attr, value)
        except ast.WrongTypeError:
            self.fail("Raised WrongTypeError for valid assignment")
        else:
            assert_equal(getattr(node, attr), value, "Expected value to be set after assignment")

    def test_valid_assignment(self):
        """Tests ast.AST.__setattr__'s behaviour on valid assignments to fields
        """
        yield from self.yield_tests(self.check_valid_assignment, [
            ("f1", 0),
            ("f1", 1),
            ("f2", 0),
            ("f2", 1),
            ("f2", None),
            ("f3", ()),
            ("f3", (1,)),
            ("f3", (1, 2, 3, 4)),
            ("f3", []),
            ("f3", [1]),
            ("f3", [1, 2, 3, 4]),
            ("f4", (1,)),
            ("f4", (1, 2, 3, 4)),
            ("f4", [1]),
            ("f4", [1, 2, 3, 4]),
        ])

    def check_invalid_assignment(self, cls, attr, value, error, required_phrases=[]):  # noqa
        node = cls()
        with assert_raises(error) as context:
            setattr(node, attr, value)

        self.assert_message_contains(context.exception, required_phrases)

    def test_invalid_assignment(self):
        """Tests ast.AST.__setattr__'s behaviour on invalid assignments to fields
        """
        yield from self.yield_tests(self.check_invalid_assignment, [
            (BasicNode, "bar", 1, ast.FieldError, ["bar", "no field"]),
            (AllIntModifersNode, "f1", "", ast.WrongTypeError),
            (AllIntModifersNode, "f1", "", ast.WrongTypeError),
            (AllIntModifersNode, "f2", "", ast.WrongTypeError),
            (AllIntModifersNode, "f3", "", ast.WrongTypeError),
            (AllIntModifersNode, "f3", (""), ast.WrongTypeError),
            (AllIntModifersNode, "f3", [""], ast.WrongTypeError),
            (AllIntModifersNode, "f4", "", ast.WrongTypeError),
            (AllIntModifersNode, "f4", (), ast.WrongTypeError),
            (AllIntModifersNode, "f4", [], ast.WrongTypeError),
            (AllIntModifersNode, "f4", (""), ast.WrongTypeError),
            (AllIntModifersNode, "f4", [""], ast.WrongTypeError),
            (AllIntModifersNode, "f1", "", ast.WrongTypeError),
            (AllIntModifersNode, "f1", "", ast.WrongTypeError),

        ])

    def check_valid_finalize(self, node, final_attrs):
        try:
            node.finalize()
        except ast.ASTError:
            raise AssertionError(
                "Raised ASTError on finalize when values were OK."
            )
        else:
            for attr, val in final_attrs.items():
                assert_equal(getattr(node, attr), val)

    def test_valid_finalize(self):
        """Tests ast.AST.finalize's behaviour on valid attributes.
        """
        yield from self.yield_tests(self.check_valid_finalize, [
            (AllIntModifersNode(1, 2, [], [3]), {
                "f1": 1, "f2": 2, "f3": (), "f4": (3,)
            }),
            (AllIntModifersNode(f1=1, f4=[2]), {
                "f1": 1, "f2": None, "f3": (), "f4": (2,)
            })
        ])

    def check_invalid_finalize(self, node, required_phrases):
        with assert_raises(AttributeError) as context:
            node.finalize()

        self.assert_message_contains(context.exception, required_phrases)

    def test_invalid_finalize(self):
        """Tests ast.AST.finalize's behaviour on invalid attributes \
        and modifiers.
        """
        yield from self.yield_tests(self.check_invalid_finalize, [
            # "!f2" means check that "f2" is not in the error msg...
            (AllIntModifersNode(), ["f1", "f4", "missing", "!f2", "!f3"]),
            (ParentNode(BasicNode()), ["missing", "f1", "BasicNode", "!ParentNode"]),  # noqa
            # XXX: Add a check for child missing attribute in list, tuple...
            (InvalidModifierNode(), ["f1", "InvalidModifierNode", "unknown modifier"])  # noqa
        ])

    def check_node_equality(self, node1, node2, equal):
        node1.finalize()
        node2.finalize()

        if equal:
            assert_equal(node1, node2)
        else:
            assert_not_equal(node1, node2)

    def test_node_equality(self):
        """Tests ast.AST.__eq__'s behaviour
        """
        yield from self.yield_tests(self.check_node_equality, [
            (BasicNode(1), BasicNode(1), True),
            (ParentNode(BasicNode(1)), ParentNode(BasicNode(1)), True),
            (BasicNode(0), BasicNode(1), False),
            (ParentNode(BasicNode(0)), ParentNode(BasicNode(1)), False),
            (BasicNode(1), BasicNodeCopy(1), False),
        ])

    def check_node_repr(self, node, expected):
        assert_equal(repr(node), expected)

    def test_node_repr(self):
        """Tests ast.AST's string representation
        """
        yield from self.yield_tests(self.check_node_repr, [
            (BasicNode(), "BasicNode()"),
            (AllIntModifersNode(), "AllIntModifersNode()"),
            (ParentNode(), "ParentNode()"),
            (BasicNodeCopy(), "BasicNodeCopy()"),
            (InvalidModifierNode(), "InvalidModifierNode()"),
            (
                AllIntModifersNode(f1=1, f2=None),
                "AllIntModifersNode(f1=1, f2=None)"
            ),
            (
                AllIntModifersNode(f1=1, f2=None, f3=[3], f4=(4, 5, 6)),
                "AllIntModifersNode(f1=1, f2=None, f3=[3], f4=(4, 5, 6))"
            )
        ])


if __name__ == '__main__':
    from py2c.tests import runmodule
    runmodule()