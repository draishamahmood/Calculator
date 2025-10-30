import streamlit as st
import ast
import operator as op

st.set_page_config(page_title="Streamlit Calculator", page_icon="🧮", layout="centered")

# --- Safe evaluator (only arithmetic) ---
# Allowed operators
ALLOWED_BIN_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
}
ALLOWED_UNARY_OPS = {
    ast.UAdd: op.pos,
    ast.USub: op.neg,
}

class SafeEval(ast.NodeVisitor):
    def __init__(self, max_nodes: int = 200):
        self.max_nodes = max_nodes
        self.visited = 0

    def generic_visit(self, node):
        self.visited += 1
        if self.visited > self.max_nodes:
            raise ValueError("Expression too large.")
        super().generic_visit(node)

    def visit_Expr(self, node):
        return self.visit(node.value)

    def visit_Constant(self, node):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numbers are allowed.")

    # For Python <3.8 compatibility (Num nodes)
    def visit_Num(self, node):
        return node.n

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        op_type = type(node.op)
        if op_type not in ALLOWED_BIN_OPS:
            raise ValueError("Operator not allowed.")
        # Basic guard against huge exponentials
        if op_type is ast.Pow and (abs(left) > 1e6 or abs(right) > 10):
            raise ValueError("Exponent too large.")
        return ALLOWED_BIN_OPS[op_type](left, right)

    def visit_UnaryOp(self, node):
        operand = self.visit(node.operand)
        op_type = type(node.op)
        if op_type not in ALLOWED_UNARY_OPS:
            raise ValueError("Unary operator not allowed.")
        return ALLOWED_UNARY_OPS[op_type](operand)

    def visit_Call(self, node):
        raise ValueError("Function calls are not allowed.")

    def visit_Name(self, node):
        raise ValueError("Variables are not allowed.")

def safe_eval(expr: str):
    # Normalize some common symbols
    normalized = (
        expr.replace("×", "*")
            .replace("÷", "/")
            .replace("–", "-")
            .replace("—", "-")
            .replace("^", "**")  # allow caret for power
    )
    try:
        tree = ast.parse(normalized, mode="eval")
        evaluator = SafeEval()
        result = evaluator.visit(tree.body)
        # Optionally round very long floats for display
        if isinstance(result, float):
            result = round(result, 12)
        return result
    except ZeroDivisionError:
        return "Error: Division by zero"
    except Exception as e:
        return f"Error: {e}"

# --- Session State ---
if "expr" not in st.session_state:
    st.session_state.expr = "0"
if "history" not in st.session_state:
    st.session_state.history = []

def append_to_expr(token: str):
    if st.session_state.expr == "0" and token not in (".", ")", "**", "%"):
        st.session_state.expr = token
    else:
        st.session_state.expr += token

def backspace():
    st.session_state.expr = st.session_state.expr[:-1] or "0"

def clear():
    st.session_state.expr = "0"

def evaluate():
    expr = st.session_state.expr.strip()
    result = safe_eval(expr)
    st.session_state.history.insert(0, f"{expr} = {result}")
    st.session_state.history = st.session_state.history[:15]  # keep last 15
    st.session_state.expr = str(result) if not str(result).startswith("Error") else st.session_state.expr

# --- UI ---
st.title("🧮 Streamlit Calculator")

# Style tweaks for bigger buttons
st.markdown(
    """
    <style>
    .stButton > button {
        width: 100%;
        height: 3rem;
        font-size: 1.2rem;
    }
    .expr-input input {
        font-size: 1.5rem !important;
        height: 3rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Display and keyboard input
st.text_input("Expression", key="expr", label_visibility="collapsed", placeholder="0", help="Type an arithmetic expression and press = or Enter.", kwargs={"class":"expr-input"})

left, right = st.columns([2, 1])

with left:
    # Button grid
    rows = [
        ["7", "8", "9", "/", "AC"],
        ["4", "5", "6", "*", "⌫"],
        ["1", "2", "3", "-", "("],
        ["0", ".", "=", "+", ")"],
    ]
    for row in rows:
        cols = st.columns(5)
        for i, token in enumerate(row):
            if token == "AC":
                if cols[i].button("AC"):
                    clear()
            elif token == "⌫":
                if cols[i].button("⌫"):
                    backspace()
            elif token == "=":
                if cols[i].button("="):
                    evaluate()
            else:
                if cols[i].button(token):
                    append_to_expr(token)

    # Extra operators row
    cols = st.columns(5)
    extras = ["**", "%", "÷", "×", " // "]
    labels = ["xʸ", "%", "÷", "×", "//"]
    for i, token in enumerate(extras):
        if cols[i].button(labels[i]):
            if token.strip() == "//":
                append_to_expr("//")
            else:
                append_to_expr(token)

with right:
    st.subheader("History")
    if st.session_state.history:
        for item in st.session_state.history:
            st.markdown(f"- {item}")
    else:
        st.caption("No calculations yet.")

st.caption("Tips: Type directly into the box, or use the buttons. Use '^' for power (e.g., 2^10), '//' for floor division, and '%' for modulo.")
