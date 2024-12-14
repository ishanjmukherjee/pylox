from lox.expr import Binary, Call, Expr, ExprVisitor, Grouping, Literal, Unary


class AstPrinter(ExprVisitor[str]):
    def print(self, expr: Expr) -> str:
        return expr.accept(self)

    def visit_call(self, expr: Call) -> str:
        # Print function calls in prefix notation like:
        # (call function_name arg1 arg2 ...)
        # map() to apply self.print to each element in expr.arguments
        args = " ".join(map(self.print, expr.arguments))
        return f"(call {self.print(expr.callee)} {args})"

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
