import ast
import operator

from langchain.tools import tool


MAX_EXPRESSION_LENGTH = 100


_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _evaluate(node):
    if isinstance(node, ast.Constant):

        if isinstance(node.value, (int, float)):
            return node.value

        raise ValueError(
            "Only numbers are allowed."
        )

    if isinstance(node, ast.BinOp):

        operator_function = _ALLOWED_OPERATORS.get(
            type(node.op)
        )

        if operator_function is None:
            raise ValueError(
                "This operator is not supported."
            )

        left = _evaluate(node.left)
        right = _evaluate(node.right)

        return operator_function(
            left,
            right,
        )

    if isinstance(node, ast.UnaryOp):

        operator_function = _ALLOWED_OPERATORS.get(
            type(node.op)
        )

        if operator_function is None:
            raise ValueError(
                "This operator is not supported."
            )

        operand = _evaluate(node.operand)

        return operator_function(
            operand
        )

    raise ValueError(
        "Invalid mathematical expression."
    )


@tool
def calculate(expression: str) -> str:
    """
    Safely calculate a mathematical expression.

    Use this tool when the user asks for arithmetic
    calculations.

    Input:
        expression: A mathematical expression such as
        "150 * 20" or "(100 + 50) / 5".

    Output:
        The calculated result or an error message.
    """

    if not expression or not expression.strip():
        return "Error: Expression cannot be empty."

    expression = expression.strip()

    if len(expression) > MAX_EXPRESSION_LENGTH:
        return "Error: Expression is too long."

    try:

        tree = ast.parse(
            expression,
            mode="eval",
        )

        result = _evaluate(
            tree.body
        )

        return str(result)

    except ZeroDivisionError:
        return "Error: Cannot divide by zero."

    except (
        SyntaxError,
        ValueError,
    ):
        return (
            "Error: Invalid mathematical expression."
        )

    except Exception as error:
        return (
            f"Error: Calculation failed: "
            f"{str(error)}"
        )