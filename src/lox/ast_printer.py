from lox.expr import Binary, Expr, ExprVisitor, Grouping, Literal, Unary


class AstPrinter(ExprVisitor[str]):
    def print(self, expr: Expr) -> str:
        return expr.accept(self)

    def visit_binary(self, expr: Binary) -> str:
        return self.parenthesize(expr.operator.lexeme, expr.left, expr.right)

    def visit_grouping(self, expr: Grouping) -> str:
        return self.parenthesize("group", expr.expression)

    def visit_literal(self, expr: Literal) -> str:
        if expr.value is None:
            return "nil"
        return str(expr.value)

    def visit_unary(self, expr: Unary) -> str:
        return self.parenthesize(expr.operator.lexeme, expr.right)

    def parenthesize(self, name: str, *exprs: Expr) -> str:
        builder = []
        builder.append("(")
        builder.append(name)

        for expr in exprs:
            builder.append(" ")
            builder.append(expr.accept(self))

        builder.append(")")
        return "".join(builder)
