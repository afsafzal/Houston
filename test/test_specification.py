import pytest
import z3

from houston.exceptions import InvalidExpression, UnsupportedVariableType
from houston.specification import Specification, Expression

import z3

def test_expression():
    expr_string = "(= a true)"
    expr = Expression(expr_string)
    assert expr.expression == expr_string
    with pytest.raises(InvalidExpression):
        assert Expression("((= a true)")
        pytest.fail("expected InvalidExpression")

    ctx = z3.Context()
    var = Expression.create_z3_var(ctx, int, 'var')
    assert var.sort() == z3.IntSort(ctx=ctx)
    assert str(var) == 'var'
    assert var.ctx == ctx
    assert var.ctx != z3.main_ctx
    assert Expression.create_z3_var(None, bool, 'var').sort() == z3.BoolSort()
    assert Expression.create_z3_var(None, str, 'var').sort() == z3.StringSort()
    assert Expression.create_z3_var(None, float, 'var').sort() == z3.RealSort()
    with pytest.raises(UnsupportedVariableType):
        assert Expression.create_z3_var(None, list, 'var')
        pytest.fail("expected UnsupportedVariableType")

def test_specification():
    spec = Specification("s1", "(= a true)",
                         "(= b false)", lambda a, s, e, c: 5.5)
    assert spec.timeout(None, None, None, None) == 5.5
    assert spec.name == 's1'

    with pytest.raises(InvalidExpression):
        assert Specification("s2", "(= a true))", "(= b false)")
        pytest.fail("expected InvalidExpression")

