import math
import re
from decimal import Decimal, ROUND_HALF_UP

from flask import Flask, render_template, request

app = Flask(__name__)

SHOP = {
    "name": "Cà phê ",
    "address": "12 Lê Lợi, TP. Huế",
    "phone": "0234 123 4567",
}

MENU = [
    {"name": "Cà phê đen", "price": 20000},
    {"name": "Cà phê sữa", "price": 25000},
    {"name": "Bạc xỉu", "price": 28000},
    {"name": "Cold brew", "price": 35000},
    {"name": "Trà đào cam sả", "price": 38000},
    {"name": "Trà sen vàng", "price": 40000},
    {"name": "Sinh tố bơ", "price": 45000},
    {"name": "Bánh flan", "price": 15000},
]

PER_PAGE = 4
OPERATORS = ["+", "-", "*", "/"]


@app.context_processor
def inject_shop():
    return {"shop": SHOP}


@app.route("/")
def index():
    return render_template("index.html", menu=MENU)


@app.route("/menu")
def menu():
    pages = max(1, math.ceil(len(MENU) / PER_PAGE))
    page = request.args.get("page", 1, type=int)
    page = min(max(page, 1), pages)
    start = (page - 1) * PER_PAGE
    return render_template(
        "menu.html",
        menu=MENU[start:start + PER_PAGE],
        page=page,
        pages=pages,
    )


@app.route("/contact")
def contact():
    return render_template("contact.html")


# ---------- Chương 5 - Bài 1: Máy tính cơ bản ----------

def parse_number(text):
    """Chuyển chuỗi thành số, chấp nhận dấu phẩy thập phân (2,5).
    Trả về None nếu rỗng hoặc không phải số."""
    text = (text or "").strip().replace(",", ".")
    if not text:
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    return value if math.isfinite(value) else None


def fmt(x):
    """Hiển thị số gọn: 8.0 -> 8, 3.5 -> 3.5."""
    if x == int(x) and abs(x) < 1e15:
        return str(int(x))
    return repr(round(x, 10))


@app.route("/math", methods=["GET", "POST"])
def calculator():
    form = {"a": "", "op": "+", "b": ""}   # giữ lại giá trị đã nhập
    errors = {}                             # lỗi theo từng ô
    result = None

    if request.method == "POST":
        form["a"] = request.form.get("a", "")
        form["op"] = request.form.get("op", "")
        form["b"] = request.form.get("b", "")

        a = parse_number(form["a"])
        b = parse_number(form["b"])

        if a is None:
            errors["a"] = "Vui lòng nhập một số."
        if b is None:
            errors["b"] = "Vui lòng nhập một số."
        if form["op"] not in OPERATORS:
            errors["op"] = "Phép toán không hợp lệ."
        if not errors and form["op"] == "/" and b == 0:
            errors["b"] = "Không thể chia cho 0."

        if not errors:
            op = form["op"]
            if op == "+":
                value = a + b
            elif op == "-":
                value = a - b
            elif op == "*":
                value = a * b
            else:
                value = a / b
            result = f"{fmt(a)} {op} {fmt(b)} = {fmt(value)}"

    return render_template(
        "math.html", form=form, errors=errors, result=result, operators=OPERATORS
    )


# ---------- Chương 5 - Bài 2: Tính điểm học phần ----------

# (tên ô trong form, nhãn hiển thị, trọng số)
SCORE_FIELDS = [
    ("cc", "Chuyên cần (10%)", Decimal("0.1")),
    ("gk", "Giữa kỳ (30%)", Decimal("0.3")),
    ("ck", "Cuối kỳ (60%)", Decimal("0.6")),
]

NUMBER_RE = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)$")


def check_score(text):
    """Hàm kiểm tra dùng chung cho cả 3 ô.
    Trả về (giá trị, None) nếu hợp lệ hoặc (None, thông báo lỗi)."""
    text = (text or "").strip().replace(",", ".")   # chấp nhận dấu phẩy
    if not NUMBER_RE.match(text):
        return None, "Vui lòng nhập một số."
    value = Decimal(text)
    if value < 0 or value > 10:
        return None, "Điểm phải từ 0 đến 10."
    return value, None


def letter_grade(score):
    """Đổi điểm (đã làm tròn 1 chữ số) sang điểm chữ."""
    if score >= Decimal("8.5"):
        return "A"
    if score >= Decimal("7.0"):
        return "B"
    if score >= Decimal("5.5"):
        return "C"
    if score >= Decimal("4.0"):
        return "D"
    return "F"


@app.route("/diem", methods=["GET", "POST"])
def grade():
    form = {key: "" for key, _, _ in SCORE_FIELDS}
    errors = {}
    result = None

    if request.method == "POST":
        values = {}
        for key, _, _ in SCORE_FIELDS:
            form[key] = request.form.get(key, "")
            value, error = check_score(form[key])
            if error:
                errors[key] = error
            else:
                values[key] = value

        if not errors:
            total = sum(values[key] * weight for key, _, weight in SCORE_FIELDS)
            total = total.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

            if values["ck"] < 1:            # điểm liệt
                result = f"{total} · F (điểm thi dưới 1)"
            else:
                result = f"{total} · {letter_grade(total)}"

    return render_template(
        "diem.html", form=form, errors=errors, result=result, fields=SCORE_FIELDS
    )


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

# ---------- Chương 5 - Bài 3: Tính chỉ số BMI ----------
@app.route("/bmi", methods=["GET", "POST"])
def bmi():
    form = {"cao": "", "nang": ""}
    errors = {}
    result = None

    if request.method == "POST":
        form["cao"] = request.form.get("cao", "")
        form["nang"] = request.form.get("nang", "")

        # Chấp nhận dấu phẩy
        cao_str = form["cao"].strip().replace(",", ".")
        nang_str = form["nang"].strip().replace(",", ".")

        cao = None
        nang = None

        # Validate chiều cao (50-250)
        try:
            cao = float(cao_str)
            if not (50 <= cao <= 250):
                errors["cao"] = "Giá trị phải từ 50 đến 250."
        except ValueError:
            errors["cao"] = "Vui lòng nhập một số."

        # Validate cân nặng (10-300)
        try:
            nang = float(nang_str)
            if not (10 <= nang <= 300):
                errors["nang"] = "Giá trị phải từ 10 đến 300."
        except ValueError:
            errors["nang"] = "Vui lòng nhập một số."

        if not errors:
            # Chiều cao chuyển sang mét
            cao_m = cao / 100
            # Tính BMI = cân nặng / (chiều cao m)^2
            bmi_val = nang / (cao_m ** 2)
            bmi_rounded = round(bmi_val, 1)

            # Phân loại chuẩn Châu Á
            if bmi_rounded < 18.5:
                status = "Thiếu cân"
                color_class = "text-yellow"
            elif bmi_rounded < 23:
                status = "Bình thường"
                color_class = "text-green"
            elif bmi_rounded < 25:
                status = "Thừa cân"
                color_class = "text-yellow"
            else:
                status = "Béo phì"
                color_class = "text-red"

            # Cân nặng nên có (BMI 18.5 - 22.9)
            min_nang = round(18.5 * (cao_m ** 2), 1)
            max_nang = round(22.9 * (cao_m ** 2), 1)

            result = {
                "bmi": bmi_rounded,
                "status": status,
                "color_class": color_class,
                "min_nang": min_nang,
                "max_nang": max_nang
            }

    return render_template("bmi.html", form=form, errors=errors, result=result)

if __name__ == "__main__":
    app.run(debug=True)