"""Seed dữ liệu mẫu cho topics/quizzes/questions — phục vụ demo & kiểm thử Giai đoạn 3.

Chạy: python scripts/seed_quizzes.py
Idempotent:
  - Topic: bỏ qua nếu đã tồn tại (theo tên).
  - Quiz: bỏ qua tạo mới nếu đã tồn tại (theo title), nhưng vẫn duyệt qua các
    câu hỏi trong QUIZ_SEED và thêm vào quiz đã tồn tại nếu câu hỏi (theo
    prompt) chưa có trong quiz đó — an toàn khi chạy lại nhiều lần, và cho
    phép bổ sung câu hỏi mới vào quiz đã seed trước đó.
"""
import json
import sys
from pathlib import Path

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import models  # noqa: F401 — đăng ký model với Base.metadata
from database import Base, SessionLocal, engine
from models.question import Question
from models.quiz import Quiz
from models.topic import Topic

# Tên chủ đề lấy từ field "topic" trong test_questions.json — giữ nhất quán taxonomy.
TOPIC_NAMES = [
    "biến", "kiểu dữ liệu", "điều kiện", "vòng lặp", "hàm", "mảng", "con trỏ",
    "bộ nhớ", "struct", "đệ quy", "file", "input/output", "string",
]

QUIZ_SEED = [
    {
        "topic": "biến",
        "title": "Kiểm tra nhanh: Biến trong C",
        "questions": [
            {
                "question_type": "mcq",
                "prompt": (
                    "Từ khoá nào trong C dùng để khai báo một hằng số (giá trị không thể "
                    "thay đổi sau khi gán)? (A) static (B) const (C) extern (D) volatile"
                ),
                "reference_answer": "B",
                "grading_rubric": None,
                "difficulty": 1,
            },
            {
                "question_type": "mcq",
                "prompt": (
                    "Một biến được khai báo bên trong một hàm (biến cục bộ) có phạm vi "
                    "(scope) sử dụng như thế nào? (A) Có thể truy cập từ mọi hàm trong "
                    "chương trình (B) Chỉ tồn tại và truy cập được trong hàm khai báo nó "
                    "(C) Tự động trở thành biến toàn cục sau khi hàm kết thúc (D) Phải khai "
                    "báo lại ở hàm main mới dùng được"
                ),
                "reference_answer": "B",
                "grading_rubric": None,
                "difficulty": 3,
            },
            {
                "question_type": "short_answer",
                "prompt": "Phân biệt biến local (cục bộ) và biến global (toàn cục) trong C.",
                "reference_answer": (
                    "Biến local được khai báo trong một hàm/khối lệnh, chỉ tồn tại và truy "
                    "cập được trong phạm vi đó, bị huỷ khi hàm kết thúc. Biến global được "
                    "khai báo bên ngoài mọi hàm, tồn tại suốt thời gian chạy chương trình "
                    "và có thể truy cập từ mọi hàm."
                ),
                "grading_rubric": json.dumps(
                    {"keywords": ["cục bộ", "toàn cục", "phạm vi"]}, ensure_ascii=False
                ),
                "difficulty": 2,
            },
            {
                "question_type": "short_answer",
                "prompt": (
                    "Khi một biến cục bộ trong hàm được khai báo với từ khoá `static`, giá "
                    "trị của nó thay đổi như thế nào giữa các lần gọi hàm? Giải thích."
                ),
                "reference_answer": (
                    "Biến static cục bộ chỉ được khởi tạo một lần duy nhất, và giá trị của "
                    "nó được giữ lại (không bị reset) giữa các lần gọi hàm khác nhau, khác "
                    "với biến cục bộ thông thường sẽ bị tạo lại mỗi lần gọi hàm."
                ),
                "grading_rubric": json.dumps(
                    {"keywords": ["static", "giữ giá trị", "lần gọi"]}, ensure_ascii=False
                ),
                "difficulty": 4,
            },
            {
                "question_type": "code",
                "prompt": (
                    "Viết đoạn code C khai báo một biến số nguyên `int tuoi = 20;` và một "
                    "biến số thực `float diem = 8.5;`, sau đó in cả hai giá trị ra màn hình "
                    "bằng printf."
                ),
                "reference_answer": None,
                "grading_rubric": json.dumps(
                    {"required_patterns": ["int", "float", "printf"], "run_check": False},
                    ensure_ascii=False,
                ),
                "difficulty": 2,
            },
            {
                "question_type": "code",
                "prompt": (
                    "Viết đoạn code C minh hoạ phạm vi biến: khai báo một biến toàn cục "
                    "`int x = 1;`, trong hàm `main` khai báo một biến cục bộ cũng tên `x` "
                    "với giá trị khác, rồi in giá trị của biến cục bộ này ra màn hình bằng "
                    "printf."
                ),
                "reference_answer": None,
                "grading_rubric": json.dumps(
                    {"required_patterns": ["int", "printf"], "run_check": False},
                    ensure_ascii=False,
                ),
                "difficulty": 4,
            },
        ],
    },
    {
        "topic": "kiểu dữ liệu",
        "title": "Kiểm tra nhanh: Kiểu dữ liệu trong C",
        "questions": [
            {
                "question_type": "mcq",
                "prompt": (
                    "Trong C, kiểu dữ liệu nào dùng để lưu trữ số có phần thập phân với độ "
                    "chính xác cao hơn `float`? (A) int (B) char (C) double (D) short"
                ),
                "reference_answer": "C",
                "grading_rubric": None,
                "difficulty": 1,
            },
            {
                "question_type": "mcq",
                "prompt": (
                    "Kết quả của biểu thức `7 / 2` khi cả hai số đều là kiểu `int` trong C "
                    "là gì? (A) 3.5 (B) 3 (C) 4 (D) 3.0"
                ),
                "reference_answer": "B",
                "grading_rubric": None,
                "difficulty": 3,
            },
            {
                "question_type": "short_answer",
                "prompt": (
                    "Phân biệt ngắn gọn 4 kiểu dữ liệu cơ bản trong C: `int`, `float`, "
                    "`double`, `char`."
                ),
                "reference_answer": (
                    "int lưu số nguyên; float lưu số thực với độ chính xác đơn (khoảng 6-7 "
                    "chữ số); double lưu số thực với độ chính xác kép (khoảng 15-16 chữ "
                    "số); char lưu một ký tự (1 byte), thực chất là một số nguyên nhỏ biểu "
                    "diễn mã ASCII."
                ),
                "grading_rubric": json.dumps(
                    {"keywords": ["số nguyên", "số thực", "ký tự"]}, ensure_ascii=False
                ),
                "difficulty": 2,
            },
            {
                "question_type": "short_answer",
                "prompt": (
                    "Hiện tượng tràn số (overflow) xảy ra như thế nào với kiểu `unsigned "
                    "int` khi giá trị vượt quá giới hạn tối đa? Giải thích."
                ),
                "reference_answer": (
                    "Khi giá trị của unsigned int vượt quá giá trị tối đa có thể lưu (ví dụ "
                    "UINT_MAX), nó sẽ quay vòng (wrap around) về 0 và tiếp tục tăng, do bộ "
                    "nhớ chỉ có số bit cố định để lưu, không báo lỗi tràn."
                ),
                "grading_rubric": json.dumps(
                    {"keywords": ["tràn số", "quay vòng", "unsigned"]}, ensure_ascii=False
                ),
                "difficulty": 4,
            },
            {
                "question_type": "code",
                "prompt": (
                    "Viết đoạn code C khai báo các biến: `int a = 5;`, `float b = 2.5f;`, "
                    "`char c = 'A';`, rồi in cả ba giá trị ra màn hình bằng printf với định "
                    "dạng phù hợp (`%d`, `%f`, `%c`)."
                ),
                "reference_answer": None,
                "grading_rubric": json.dumps(
                    {"required_patterns": ["int", "float", "printf"], "run_check": False},
                    ensure_ascii=False,
                ),
                "difficulty": 2,
            },
            {
                "question_type": "code",
                "prompt": (
                    "Viết đoạn code C khai báo hai biến `int a = 7, b = 2;`, rồi tính và in "
                    "ra kết quả phép chia `a / b` dưới dạng số thực (ép kiểu một trong hai "
                    "biến sang `float` hoặc `double` trước khi chia) bằng printf."
                ),
                "reference_answer": None,
                "grading_rubric": json.dumps(
                    {"required_patterns": ["int", "float", "printf"], "run_check": False},
                    ensure_ascii=False,
                ),
                "difficulty": 4,
            },
        ],
    },
    {
        "topic": "điều kiện",
        "title": "Kiểm tra nhanh: Cấu trúc điều kiện trong C",
        "questions": [
            {
                "question_type": "mcq",
                "prompt": (
                    "Trong cấu trúc `switch-case`, từ khoá nào dùng để thoát khỏi switch "
                    "ngay sau khi một case được thực hiện, tránh chạy tiếp các case sau? "
                    "(A) return (B) continue (C) break (D) exit"
                ),
                "reference_answer": "C",
                "grading_rubric": None,
                "difficulty": 1,
            },
            {
                "question_type": "mcq",
                "prompt": (
                    "Toán tử ba ngôi `?:` trong biểu thức `int x = (a > b) ? a : b;` có ý "
                    "nghĩa gì? (A) Gán a cho x nếu a > b, ngược lại gán b (B) Luôn gán a "
                    "cho x (C) So sánh a và b rồi gán kết quả boolean cho x (D) Gây lỗi cú "
                    "pháp vì C không hỗ trợ toán tử này"
                ),
                "reference_answer": "A",
                "grading_rubric": None,
                "difficulty": 3,
            },
            {
                "question_type": "short_answer",
                "prompt": (
                    "So sánh cấu trúc `if-else if-else` và `switch-case`: khi nào nên dùng "
                    "cái nào?"
                ),
                "reference_answer": (
                    "if-else if-else linh hoạt hơn, dùng được với mọi loại điều kiện (so "
                    "sánh khoảng, biểu thức logic phức tạp); switch-case chỉ so sánh một "
                    "biến với các giá trị hằng cụ thể (số nguyên, ký tự, enum), nhưng code "
                    "rõ ràng và dễ đọc hơn khi có nhiều trường hợp rời rạc."
                ),
                "grading_rubric": json.dumps(
                    {"keywords": ["if-else", "switch", "điều kiện"]}, ensure_ascii=False
                ),
                "difficulty": 2,
            },
            {
                "question_type": "short_answer",
                "prompt": (
                    "Giải thích cơ chế \"short-circuit\" (đoạn mạch) của toán tử `&&` và "
                    "`||` trong C."
                ),
                "reference_answer": (
                    "Với &&, nếu vế trái sai (0), C không cần đánh giá vế phải vì kết quả "
                    "chắc chắn sai; với ||, nếu vế trái đúng (khác 0), C không cần đánh giá "
                    "vế phải vì kết quả chắc chắn đúng. Nhờ đó tránh được lỗi (như chia cho "
                    "0) và tăng hiệu suất."
                ),
                "grading_rubric": json.dumps(
                    {"keywords": ["&&", "||", "đánh giá"]}, ensure_ascii=False
                ),
                "difficulty": 4,
            },
            {
                "question_type": "code",
                "prompt": (
                    "Viết đoạn code C đọc một số nguyên từ bàn phím bằng scanf, dùng "
                    "`if-else` để kiểm tra và in ra số đó là chẵn hay lẻ."
                ),
                "reference_answer": None,
                "grading_rubric": json.dumps(
                    {"required_patterns": ["if", "scanf", "printf"], "run_check": False},
                    ensure_ascii=False,
                ),
                "difficulty": 3,
            },
            {
                "question_type": "code",
                "prompt": (
                    "Viết đoạn code C đọc điểm số (kiểu `float`, từ 0 đến 10) từ bàn phím, "
                    "dùng `if-else` (hoặc `switch-case` kết hợp ép kiểu) để xếp loại: >=8.5 "
                    "Giỏi, >=7 Khá, >=5 Trung bình, còn lại Yếu, rồi in kết quả."
                ),
                "reference_answer": None,
                "grading_rubric": json.dumps(
                    {"required_patterns": ["if", "scanf", "printf"], "run_check": False},
                    ensure_ascii=False,
                ),
                "difficulty": 5,
            },
        ],
    },
    {
        "topic": "vòng lặp",
        "title": "Kiểm tra nhanh: Vòng lặp trong C",
        "questions": [
            {
                "question_type": "mcq",
                "prompt": "Vòng lặp nào sau đây luôn chạy ít nhất một lần, kể cả khi điều kiện sai ngay từ đầu?",
                "reference_answer": "do-while",
                "grading_rubric": None,
                "difficulty": 1,
            },
            {
                "question_type": "short_answer",
                "prompt": "Nêu sự khác nhau cơ bản giữa vòng lặp `for` và vòng lặp `while` trong C.",
                "reference_answer": (
                    "Vòng lặp for thường dùng khi biết trước số lần lặp, gộp khởi tạo, "
                    "điều kiện và bước nhảy trên cùng một dòng; while dùng khi chưa biết "
                    "trước số lần lặp, chỉ kiểm tra điều kiện trước mỗi vòng."
                ),
                "grading_rubric": json.dumps(
                    {"keywords": ["số lần lặp", "điều kiện", "khởi tạo"]}, ensure_ascii=False
                ),
                "difficulty": 2,
            },
            {
                "question_type": "code",
                "prompt": (
                    "Viết đoạn code C dùng vòng lặp `for` để in ra các số từ 1 đến 5, "
                    "mỗi số một dòng (dùng printf)."
                ),
                "reference_answer": None,
                "grading_rubric": json.dumps(
                    {"required_patterns": ["for", "printf"], "run_check": False}, ensure_ascii=False
                ),
                "difficulty": 2,
            },
            {
                "question_type": "mcq",
                "prompt": (
                    "Trong vòng lặp, sự khác biệt giữa lệnh `break` và `continue` là gì? "
                    "(A) break thoát khỏi vòng lặp, continue bỏ qua phần còn lại của lần "
                    "lặp hiện tại và tiếp tục lần lặp kế tiếp (B) Cả hai đều thoát khỏi "
                    "vòng lặp hoàn toàn (C) break bỏ qua lần lặp hiện tại, continue thoát "
                    "hoàn toàn (D) Cả hai đều không có tác dụng trong vòng lặp for"
                ),
                "reference_answer": "A",
                "grading_rubric": None,
                "difficulty": 3,
            },
            {
                "question_type": "short_answer",
                "prompt": (
                    "Vòng lặp vô hạn (infinite loop) là gì? Nêu một nguyên nhân thường gặp "
                    "và cách tránh."
                ),
                "reference_answer": (
                    "Vòng lặp vô hạn là vòng lặp mà điều kiện kết thúc không bao giờ trở "
                    "thành sai (false), khiến chương trình lặp mãi không dừng. Nguyên nhân "
                    "thường gặp là quên cập nhật biến điều khiển (ví dụ quên i++) hoặc "
                    "điều kiện luôn đúng. Cách tránh: đảm bảo biến điều khiển được cập "
                    "nhật đúng và điều kiện dừng có thể đạt được."
                ),
                "grading_rubric": json.dumps(
                    {"keywords": ["vô hạn", "điều kiện", "biến điều khiển"]}, ensure_ascii=False
                ),
                "difficulty": 4,
            },
            {
                "question_type": "code",
                "prompt": (
                    "Viết đoạn code C dùng hai vòng lặp `for` lồng nhau để in ra bảng cửu "
                    "chương từ 1 đến 5 (mỗi dòng dạng `i x j = i*j`, với i, j chạy từ 1 đến "
                    "5)."
                ),
                "reference_answer": None,
                "grading_rubric": json.dumps(
                    {"required_patterns": ["for", "printf"], "run_check": False}, ensure_ascii=False
                ),
                "difficulty": 5,
            },
        ],
    },
    {
        "topic": "hàm",
        "title": "Kiểm tra nhanh: Hàm trong C",
        "questions": [
            {
                "question_type": "mcq",
                "prompt": (
                    "Khi một hàm trong C không trả về giá trị nào, kiểu trả về của hàm đó "
                    "được khai báo là gì? (A) null (B) void (C) empty (D) none"
                ),
                "reference_answer": "B",
                "grading_rubric": None,
                "difficulty": 1,
            },
            {
                "question_type": "mcq",
                "prompt": (
                    "Khi truyền một biến kiểu `int` vào hàm theo cách thông thường (truyền "
                    "theo giá trị - pass by value), thay đổi giá trị của tham số bên trong "
                    "hàm có ảnh hưởng đến biến gốc ở ngoài không? (A) Có, vì C luôn truyền "
                    "tham chiếu (B) Không, vì hàm nhận một bản sao của giá trị (C) Chỉ ảnh "
                    "hưởng nếu biến là toàn cục (D) Chỉ ảnh hưởng nếu hàm có kiểu trả về int"
                ),
                "reference_answer": "B",
                "grading_rubric": None,
                "difficulty": 3,
            },
            {
                "question_type": "short_answer",
                "prompt": "Prototype (khai báo nguyên mẫu) của hàm trong C là gì và có vai trò gì?",
                "reference_answer": (
                    "Prototype là dòng khai báo hàm (kiểu trả về, tên hàm, danh sách tham "
                    "số) trước khi hàm được sử dụng hoặc định nghĩa đầy đủ, thường đặt ở "
                    "đầu file hoặc trong file header. Vai trò: cho phép trình biên dịch "
                    "kiểm tra kiểu dữ liệu khi gọi hàm trước khi gặp định nghĩa thực sự của "
                    "hàm."
                ),
                "grading_rubric": json.dumps(
                    {"keywords": ["prototype", "khai báo", "kiểu trả về"]}, ensure_ascii=False
                ),
                "difficulty": 2,
            },
            {
                "question_type": "short_answer",
                "prompt": "Biến cục bộ khai báo với `static` bên trong một hàm khác với biến cục bộ thông thường như thế nào?",
                "reference_answer": (
                    "Biến static cục bộ trong hàm chỉ được khởi tạo một lần và giữ nguyên "
                    "giá trị giữa các lần gọi hàm (lưu trong vùng nhớ tĩnh), trong khi biến "
                    "cục bộ thông thường được tạo mới và mất giá trị mỗi khi hàm kết thúc "
                    "(lưu trên stack)."
                ),
                "grading_rubric": json.dumps(
                    {"keywords": ["static", "giữ giá trị", "stack"]}, ensure_ascii=False
                ),
                "difficulty": 4,
            },
            {
                "question_type": "code",
                "prompt": (
                    "Viết một hàm C `int cong(int a, int b)` trả về tổng của hai số "
                    "nguyên, và gọi hàm này trong `main` để in kết quả của `cong(3, 4)`."
                ),
                "reference_answer": None,
                "grading_rubric": json.dumps(
                    {"required_patterns": ["int", "return", "printf"], "run_check": False},
                    ensure_ascii=False,
                ),
                "difficulty": 2,
            },
            {
                "question_type": "code",
                "prompt": (
                    "Viết một hàm C `void hoanDoi(int *a, int *b)` dùng con trỏ để hoán "
                    "đổi (swap) giá trị của hai biến nguyên, và gọi hàm này trong `main`, "
                    "in ra giá trị hai biến trước và sau khi hoán đổi."
                ),
                "reference_answer": None,
                "grading_rubric": json.dumps(
                    {"required_patterns": ["void", "*", "printf"], "run_check": False},
                    ensure_ascii=False,
                ),
                "difficulty": 4,
            },
        ],
    },
    {
        "topic": "mảng",
        "title": "Kiểm tra nhanh: Mảng trong C",
        "questions": [
            {
                "question_type": "mcq",
                "prompt": (
                    "Trong C, chỉ số (index) của phần tử đầu tiên trong một mảng bắt đầu "
                    "từ số nào? (A) 1 (B) -1 (C) 0 (D) Tuỳ theo kiểu dữ liệu"
                ),
                "reference_answer": "C",
                "grading_rubric": None,
                "difficulty": 1,
            },
            {
                "question_type": "mcq",
                "prompt": (
                    "Khi khai báo `int arr[5];`, kích thước của mảng `arr` sau đó có thể "
                    "thay đổi (tăng/giảm số phần tử) trong quá trình chạy chương trình "
                    "không? (A) Có, dùng lệnh resize() (B) Không, kích thước mảng tĩnh được "
                    "cố định ngay khi khai báo (C) Có, nhưng chỉ giảm được (D) Có, nếu khai "
                    "báo lại ở vòng lặp"
                ),
                "reference_answer": "B",
                "grading_rubric": None,
                "difficulty": 3,
            },
            {
                "question_type": "short_answer",
                "prompt": "Mảng (array) trong C là gì? Làm thế nào để truy cập một phần tử cụ thể trong mảng?",
                "reference_answer": (
                    "Mảng là một tập hợp các phần tử có cùng kiểu dữ liệu, được lưu liên "
                    "tiếp trong bộ nhớ và truy cập thông qua một tên chung. Truy cập phần "
                    "tử bằng cú pháp tên_mảng[chỉ_số], với chỉ số bắt đầu từ 0."
                ),
                "grading_rubric": json.dumps(
                    {"keywords": ["chỉ số", "phần tử", "bộ nhớ"]}, ensure_ascii=False
                ),
                "difficulty": 2,
            },
            {
                "question_type": "short_answer",
                "prompt": "Mảng hai chiều (2D array) trong C được lưu trong bộ nhớ theo thứ tự nào (row-major hay column-major)? Giải thích ý nghĩa.",
                "reference_answer": (
                    "C lưu mảng hai chiều theo thứ tự row-major, tức là các phần tử của "
                    "hàng đầu tiên được lưu liên tiếp trong bộ nhớ, sau đó đến hàng thứ "
                    "hai, v.v. Điều này ảnh hưởng đến hiệu suất khi truy cập tuần tự theo "
                    "hàng so với theo cột."
                ),
                "grading_rubric": json.dumps(
                    {"keywords": ["row-major", "hàng", "bộ nhớ"]}, ensure_ascii=False
                ),
                "difficulty": 4,
            },
            {
                "question_type": "code",
                "prompt": (
                    "Viết đoạn code C khai báo một mảng `int arr[5]`, gán giá trị cho từng "
                    "phần tử bằng một vòng lặp `for` (ví dụ `arr[i] = i * 2`), rồi in toàn "
                    "bộ mảng ra màn hình."
                ),
                "reference_answer": None,
                "grading_rubric": json.dumps(
                    {"required_patterns": ["for", "printf"], "run_check": False}, ensure_ascii=False
                ),
                "difficulty": 2,
            },
            {
                "question_type": "code",
                "prompt": (
                    "Viết đoạn code C khai báo một mảng `int arr[] = {3, 7, 2, 9, 4};`, "
                    "dùng vòng lặp `for` để tìm và in ra giá trị lớn nhất (max) trong mảng."
                ),
                "reference_answer": None,
                "grading_rubric": json.dumps(
                    {"required_patterns": ["for", "if", "printf"], "run_check": False},
                    ensure_ascii=False,
                ),
                "difficulty": 4,
            },
        ],
    },
    {
        "topic": "con trỏ",
        "title": "Kiểm tra nhanh: Con trỏ trong C",
        "questions": [
            {
                "question_type": "mcq",
                "prompt": "Toán tử nào dùng để lấy địa chỉ của một biến trong C?",
                "reference_answer": "&",
                "grading_rubric": None,
                "difficulty": 1,
            },
            {
                "question_type": "short_answer",
                "prompt": "Con trỏ (pointer) trong C là gì? Giải thích ngắn gọn.",
                "reference_answer": (
                    "Con trỏ là một biến đặc biệt dùng để lưu trữ địa chỉ của một biến "
                    "khác trong bộ nhớ, cho phép truy cập và thay đổi giá trị thông qua địa chỉ đó."
                ),
                "grading_rubric": json.dumps(
                    {"keywords": ["địa chỉ", "biến", "bộ nhớ"]}, ensure_ascii=False
                ),
                "difficulty": 2,
            },
            {
                "question_type": "code",
                "prompt": (
                    "Viết đoạn code C khai báo một biến `int x = 10;`, một con trỏ `ptr` "
                    "trỏ tới `x`, rồi in ra giá trị của `x` thông qua `ptr` bằng printf."
                ),
                "reference_answer": None,
                "grading_rubric": json.dumps(
                    {"required_patterns": ["int", "*", "&", "printf"], "run_check": False}, ensure_ascii=False
                ),
                "difficulty": 3,
            },
            {
                "question_type": "mcq",
                "prompt": (
                    "Toán tử `*` khi đặt trước một biến con trỏ (ví dụ `*ptr`) có ý nghĩa "
                    "gì? (A) Khai báo một con trỏ mới (B) Lấy địa chỉ của ptr (C) Truy cập "
                    "(dereference) giá trị tại địa chỉ mà ptr đang trỏ tới (D) Nhân ptr với "
                    "một số"
                ),
                "reference_answer": "C",
                "grading_rubric": None,
                "difficulty": 3,
            },
            {
                "question_type": "short_answer",
                "prompt": "Phân biệt con trỏ `NULL` và con trỏ \"hoang\" (dangling pointer).",
                "reference_answer": (
                    "Con trỏ NULL là con trỏ được gán giá trị 0/NULL một cách có chủ đích, "
                    "không trỏ tới vùng nhớ nào, an toàn để kiểm tra trước khi dùng. Con "
                    "trỏ hoang (dangling pointer) là con trỏ vẫn còn giữ địa chỉ của một "
                    "vùng nhớ đã bị giải phóng (free) hoặc không còn hợp lệ, nếu dùng tiếp "
                    "sẽ gây lỗi không xác định."
                ),
                "grading_rubric": json.dumps(
                    {"keywords": ["NULL", "hoang", "giải phóng"]}, ensure_ascii=False
                ),
                "difficulty": 4,
            },
            {
                "question_type": "code",
                "prompt": (
                    "Viết đoạn code C khai báo mảng `int arr[] = {10, 20, 30, 40, 50};` và "
                    "một con trỏ `int *p = arr;`, dùng vòng lặp `for` cùng phép toán con "
                    "trỏ (`*(p + i)` hoặc `*p++`) để in ra từng phần tử của mảng."
                ),
                "reference_answer": None,
                "grading_rubric": json.dumps(
                    {"required_patterns": ["int", "for", "*", "printf"], "run_check": False},
                    ensure_ascii=False,
                ),
                "difficulty": 5,
            },
        ],
    },
    {
        "topic": "bộ nhớ",
        "title": "Kiểm tra nhanh: Bộ nhớ động trong C",
        "questions": [
            {
                "question_type": "mcq",
                "prompt": (
                    "Hàm nào trong C dùng để cấp phát động một vùng nhớ trên heap? "
                    "(A) alloc() (B) new() (C) malloc() (D) create()"
                ),
                "reference_answer": "C",
                "grading_rubric": None,
                "difficulty": 1,
            },
            {
                "question_type": "mcq",
                "prompt": (
                    "Sau khi sử dụng xong vùng nhớ được cấp phát động bằng `malloc`, lập "
                    "trình viên cần làm gì để tránh rò rỉ bộ nhớ (memory leak)? (A) Gán con "
                    "trỏ về 0 (B) Gọi hàm `free()` để giải phóng vùng nhớ (C) Khởi động lại "
                    "chương trình (D) Không cần làm gì, C tự động thu hồi"
                ),
                "reference_answer": "B",
                "grading_rubric": None,
                "difficulty": 3,
            },
            {
                "question_type": "short_answer",
                "prompt": "So sánh vùng nhớ stack và heap trong C: cách cấp phát, thời gian sống, ai quản lý.",
                "reference_answer": (
                    "Stack lưu các biến cục bộ, được cấp phát/giải phóng tự động khi "
                    "vào/ra khỏi hàm, có kích thước hạn chế. Heap dùng cho cấp phát động "
                    "(malloc/free), tồn tại đến khi được giải phóng thủ công hoặc chương "
                    "trình kết thúc, do lập trình viên tự quản lý."
                ),
                "grading_rubric": json.dumps(
                    {"keywords": ["stack", "heap", "cấp phát"]}, ensure_ascii=False
                ),
                "difficulty": 2,
            },
            {
                "question_type": "short_answer",
                "prompt": "Memory leak (rò rỉ bộ nhớ) là gì và nguyên nhân thường gặp gây ra nó trong C?",
                "reference_answer": (
                    "Memory leak là hiện tượng vùng nhớ được cấp phát động (bằng "
                    "malloc/calloc) không được giải phóng bằng free sau khi không còn sử "
                    "dụng, khiến bộ nhớ khả dụng của chương trình giảm dần theo thời gian. "
                    "Nguyên nhân thường gặp là quên gọi free, hoặc mất con trỏ tới vùng nhớ "
                    "đã cấp phát trước khi giải phóng."
                ),
                "grading_rubric": json.dumps(
                    {"keywords": ["rò rỉ", "malloc", "free"]}, ensure_ascii=False
                ),
                "difficulty": 4,
            },
            {
                "question_type": "code",
                "prompt": (
                    "Viết đoạn code C dùng `malloc` để cấp phát động một mảng 5 số nguyên, "
                    "gán giá trị bằng vòng lặp `for`, in ra các giá trị, rồi giải phóng "
                    "vùng nhớ bằng `free`."
                ),
                "reference_answer": None,
                "grading_rubric": json.dumps(
                    {"required_patterns": ["malloc", "for", "free"], "run_check": False},
                    ensure_ascii=False,
                ),
                "difficulty": 3,
            },
            {
                "question_type": "code",
                "prompt": (
                    "Viết đoạn code C đọc một số nguyên `n` từ bàn phím (số phần tử), dùng "
                    "`malloc` để cấp phát động một mảng `n` số nguyên, nhập giá trị cho "
                    "từng phần tử bằng vòng lặp, in lại mảng, rồi giải phóng vùng nhớ bằng "
                    "`free`."
                ),
                "reference_answer": None,
                "grading_rubric": json.dumps(
                    {"required_patterns": ["malloc", "scanf", "for", "free"], "run_check": False},
                    ensure_ascii=False,
                ),
                "difficulty": 5,
            },
        ],
    },
    {
        "topic": "struct",
        "title": "Kiểm tra nhanh: Struct trong C",
        "questions": [
            {
                "question_type": "mcq",
                "prompt": (
                    "Từ khoá nào trong C dùng để định nghĩa một kiểu dữ liệu có cấu trúc "
                    "(gồm nhiều trường khác kiểu)? (A) class (B) struct (C) union (D) typedef"
                ),
                "reference_answer": "B",
                "grading_rubric": None,
                "difficulty": 1,
            },
            {
                "question_type": "mcq",
                "prompt": (
                    "Khi có một con trỏ `p` trỏ tới một biến `struct`, toán tử nào dùng để "
                    "truy cập trực tiếp một trường (field) của struct đó qua con trỏ? "
                    "(A) . (dấu chấm) (B) :: (C) -> (D) []"
                ),
                "reference_answer": "C",
                "grading_rubric": None,
                "difficulty": 3,
            },
            {
                "question_type": "short_answer",
                "prompt": "Struct trong C là gì và nên dùng khi nào?",
                "reference_answer": (
                    "Struct là một kiểu dữ liệu do người dùng định nghĩa, cho phép nhóm "
                    "nhiều biến có kiểu dữ liệu khác nhau (các trường/field) thành một đơn "
                    "vị duy nhất. Nên dùng struct khi cần biểu diễn một đối tượng có nhiều "
                    "thuộc tính liên quan, ví dụ thông tin sinh viên (mã số, tên, điểm)."
                ),
                "grading_rubric": json.dumps(
                    {"keywords": ["struct", "trường", "kiểu dữ liệu"]}, ensure_ascii=False
                ),
                "difficulty": 2,
            },
            {
                "question_type": "short_answer",
                "prompt": "So sánh struct và mảng (array) trong C: điểm khác biệt chính.",
                "reference_answer": (
                    "Mảng chứa các phần tử cùng kiểu dữ liệu, truy cập qua chỉ số. Struct "
                    "chứa các trường có thể khác kiểu dữ liệu, truy cập qua tên trường. "
                    "Mảng phù hợp với tập hợp dữ liệu đồng nhất, struct phù hợp để mô tả "
                    "một đối tượng với nhiều thuộc tính khác nhau."
                ),
                "grading_rubric": json.dumps(
                    {"keywords": ["struct", "mảng", "kiểu dữ liệu"]}, ensure_ascii=False
                ),
                "difficulty": 4,
            },
            {
                "question_type": "code",
                "prompt": (
                    "Viết đoạn code C định nghĩa một `struct SinhVien` gồm các trường "
                    "`char ten[50]`, `int tuoi`, `float diem`, khai báo một biến kiểu này, "
                    "gán giá trị, rồi in thông tin ra màn hình bằng printf."
                ),
                "reference_answer": None,
                "grading_rubric": json.dumps(
                    {"required_patterns": ["struct", "printf"], "run_check": False},
                    ensure_ascii=False,
                ),
                "difficulty": 3,
            },
            {
                "question_type": "code",
                "prompt": (
                    "Viết đoạn code C định nghĩa `struct SinhVien` (gồm `char ten[50]`, "
                    "`float diem`), khai báo một biến struct và một con trỏ trỏ tới biến "
                    "đó, dùng toán tử `->` để gán và in giá trị các trường thông qua con trỏ."
                ),
                "reference_answer": None,
                "grading_rubric": json.dumps(
                    {"required_patterns": ["struct", "->", "printf"], "run_check": False},
                    ensure_ascii=False,
                ),
                "difficulty": 5,
            },
        ],
    },
    {
        "topic": "đệ quy",
        "title": "Kiểm tra nhanh: Đệ quy trong C",
        "questions": [
            {
                "question_type": "mcq",
                "prompt": (
                    "Trong một hàm đệ quy, điều kiện dừng (base case) có vai trò gì? "
                    "(A) Tăng tốc độ chạy của hàm (B) Là điều kiện để hàm ngừng gọi lại "
                    "chính nó, tránh đệ quy vô hạn (C) Khai báo kiểu trả về của hàm (D) "
                    "Không có vai trò gì, chỉ là quy ước"
                ),
                "reference_answer": "B",
                "grading_rubric": None,
                "difficulty": 1,
            },
            {
                "question_type": "mcq",
                "prompt": (
                    "Điều gì xảy ra nếu một hàm đệ quy không có điều kiện dừng (base case) "
                    "hoặc điều kiện dừng không bao giờ đạt được? (A) Hàm chạy nhanh hơn (B) "
                    "Chương trình tự động dừng sau 1 giây (C) Gây tràn ngăn xếp (stack "
                    "overflow) do gọi đệ quy vô hạn (D) Trình biên dịch sẽ báo lỗi cú pháp"
                ),
                "reference_answer": "C",
                "grading_rubric": None,
                "difficulty": 3,
            },
            {
                "question_type": "short_answer",
                "prompt": "Đệ quy (recursion) là gì? Cho một ví dụ đơn giản về bài toán có thể giải bằng đệ quy.",
                "reference_answer": (
                    "Đệ quy là kỹ thuật trong đó một hàm gọi lại chính nó để giải quyết "
                    "một bài toán nhỏ hơn cùng dạng, kết hợp với một điều kiện dừng (base "
                    "case) để kết thúc. Ví dụ: tính giai thừa n! = n * (n-1)!, với điều "
                    "kiện dừng 0! = 1."
                ),
                "grading_rubric": json.dumps(
                    {"keywords": ["gọi lại chính nó", "điều kiện dừng", "bài toán nhỏ hơn"]},
                    ensure_ascii=False,
                ),
                "difficulty": 2,
            },
            {
                "question_type": "short_answer",
                "prompt": "So sánh ưu và nhược điểm của giải pháp đệ quy so với dùng vòng lặp (for/while).",
                "reference_answer": (
                    "Ưu điểm của đệ quy: code thường ngắn gọn, dễ diễn đạt các bài toán có "
                    "tính chất chia nhỏ tự nhiên (như cây, giai thừa, Fibonacci). Nhược "
                    "điểm: tốn bộ nhớ stack cho mỗi lần gọi hàm, có thể chậm hơn và dễ gây "
                    "stack overflow nếu độ sâu đệ quy lớn, trong khi vòng lặp thường tiết "
                    "kiệm bộ nhớ và hiệu quả hơn cho các bài toán đơn giản."
                ),
                "grading_rubric": json.dumps(
                    {"keywords": ["đệ quy", "vòng lặp", "bộ nhớ"]}, ensure_ascii=False
                ),
                "difficulty": 4,
            },
            {
                "question_type": "code",
                "prompt": (
                    "Viết một hàm đệ quy C `int giaiThua(int n)` tính giai thừa của `n` "
                    "(n!), kèm điều kiện dừng khi `n <= 1`, và gọi hàm này trong `main` để "
                    "in `giaiThua(5)`."
                ),
                "reference_answer": None,
                "grading_rubric": json.dumps(
                    {"required_patterns": ["int", "if", "return"], "run_check": False},
                    ensure_ascii=False,
                ),
                "difficulty": 3,
            },
            {
                "question_type": "code",
                "prompt": (
                    "Viết một hàm đệ quy C `int fibonacci(int n)` trả về số Fibonacci thứ "
                    "`n` (với `fibonacci(0) = 0`, `fibonacci(1) = 1`), kèm điều kiện dừng "
                    "phù hợp, và gọi hàm này trong `main` để in `fibonacci(7)`."
                ),
                "reference_answer": None,
                "grading_rubric": json.dumps(
                    {"required_patterns": ["int", "if", "return"], "run_check": False},
                    ensure_ascii=False,
                ),
                "difficulty": 5,
            },
        ],
    },
    {
        "topic": "file",
        "title": "Kiểm tra nhanh: Làm việc với file trong C",
        "questions": [
            {
                "question_type": "mcq",
                "prompt": "Hàm nào trong C dùng để mở một file? (A) open() (B) fopen() (C) openfile() (D) fread()",
                "reference_answer": "B",
                "grading_rubric": None,
                "difficulty": 1,
            },
            {
                "question_type": "mcq",
                "prompt": (
                    "Để mở một file ở chế độ ghi thêm (append) — nội dung mới được thêm "
                    "vào cuối file mà không xoá nội dung cũ — tham số chế độ (mode) truyền "
                    "vào `fopen` là gì? (A) \"r\" (B) \"w\" (C) \"a\" (D) \"x\""
                ),
                "reference_answer": "C",
                "grading_rubric": None,
                "difficulty": 3,
            },
            {
                "question_type": "short_answer",
                "prompt": "Nêu các bước cơ bản khi làm việc với file trong C (mở, đọc/ghi, đóng).",
                "reference_answer": (
                    "Các bước cơ bản: (1) Mở file bằng fopen() với chế độ phù hợp (đọc, "
                    "ghi, hoặc thêm), nhận về con trỏ FILE*; (2) Đọc hoặc ghi dữ liệu bằng "
                    "các hàm như fscanf/fprintf, fgets/fputs, fread/fwrite; (3) Đóng file "
                    "bằng fclose() để giải phóng tài nguyên và đảm bảo dữ liệu được lưu."
                ),
                "grading_rubric": json.dumps(
                    {"keywords": ["mở file", "đọc/ghi", "đóng file"]}, ensure_ascii=False
                ),
                "difficulty": 2,
            },
            {
                "question_type": "short_answer",
                "prompt": "Vì sao sau khi gọi `fopen`, cần kiểm tra con trỏ trả về có khác `NULL` không trước khi sử dụng?",
                "reference_answer": (
                    "fopen trả về NULL nếu mở file thất bại (ví dụ file không tồn tại, "
                    "không có quyền truy cập). Nếu không kiểm tra và tiếp tục sử dụng con "
                    "trỏ NULL để đọc/ghi, chương trình sẽ gặp lỗi truy cập bộ nhớ không hợp "
                    "lệ (segmentation fault) hoặc hành vi không xác định."
                ),
                "grading_rubric": json.dumps(
                    {"keywords": ["NULL", "fopen", "lỗi"]}, ensure_ascii=False
                ),
                "difficulty": 4,
            },
            {
                "question_type": "code",
                "prompt": (
                    "Viết đoạn code C mở (hoặc tạo) một file văn bản tên `output.txt` ở "
                    "chế độ ghi (\"w\"), viết một dòng văn bản vào file bằng `fprintf`, rồi "
                    "đóng file bằng `fclose`."
                ),
                "reference_answer": None,
                "grading_rubric": json.dumps(
                    {"required_patterns": ["fopen", "fclose"], "run_check": False},
                    ensure_ascii=False,
                ),
                "difficulty": 3,
            },
            {
                "question_type": "code",
                "prompt": (
                    "Viết đoạn code C mở file văn bản `input.txt` ở chế độ đọc (\"r\"), "
                    "dùng vòng lặp `while` với `fgets` để đọc và in ra từng dòng của file "
                    "cho tới khi hết file (EOF), rồi đóng file."
                ),
                "reference_answer": None,
                "grading_rubric": json.dumps(
                    {"required_patterns": ["fopen", "while", "fclose"], "run_check": False},
                    ensure_ascii=False,
                ),
                "difficulty": 5,
            },
        ],
    },
    {
        "topic": "input/output",
        "title": "Kiểm tra nhanh: Nhập xuất (Input/Output) trong C",
        "questions": [
            {
                "question_type": "mcq",
                "prompt": (
                    "Hàm nào trong C dùng để xuất (in) dữ liệu ra màn hình theo định dạng? "
                    "(A) scanf() (B) printf() (C) getchar() (D) puts()"
                ),
                "reference_answer": "B",
                "grading_rubric": None,
                "difficulty": 1,
            },
            {
                "question_type": "mcq",
                "prompt": (
                    "Khi dùng `scanf` để đọc một giá trị kiểu `double` vào biến `d`, định "
                    "dạng (format specifier) nào là chính xác? (A) scanf(\"%d\", &d); "
                    "(B) scanf(\"%f\", &d); (C) scanf(\"%lf\", &d); (D) scanf(\"%c\", &d);"
                ),
                "reference_answer": "C",
                "grading_rubric": None,
                "difficulty": 3,
            },
            {
                "question_type": "short_answer",
                "prompt": "Phân biệt vai trò của `scanf` và `printf` trong C.",
                "reference_answer": (
                    "scanf dùng để đọc (nhập) dữ liệu từ bàn phím (luồng nhập chuẩn stdin) "
                    "vào các biến theo định dạng chỉ định. printf dùng để xuất (in) dữ "
                    "liệu ra màn hình (luồng xuất chuẩn stdout) theo định dạng chỉ định."
                ),
                "grading_rubric": json.dumps(
                    {"keywords": ["nhập", "xuất", "scanf"]}, ensure_ascii=False
                ),
                "difficulty": 2,
            },
            {
                "question_type": "short_answer",
                "prompt": "Vì sao nên kiểm tra giá trị trả về của `scanf` sau khi gọi?",
                "reference_answer": (
                    "scanf trả về số lượng phần tử đọc và gán giá trị thành công. Nếu "
                    "người dùng nhập sai định dạng (ví dụ nhập chữ thay vì số), scanf có "
                    "thể trả về giá trị nhỏ hơn số biến mong đợi và biến không được gán "
                    "giá trị hợp lệ. Kiểm tra giá trị trả về giúp phát hiện lỗi nhập liệu "
                    "và tránh sử dụng biến chưa được gán giá trị."
                ),
                "grading_rubric": json.dumps(
                    {"keywords": ["scanf", "giá trị trả về", "lỗi nhập liệu"]}, ensure_ascii=False
                ),
                "difficulty": 4,
            },
            {
                "question_type": "code",
                "prompt": (
                    "Viết đoạn code C đọc một số nguyên từ bàn phím bằng `scanf`, sau đó in "
                    "lại số đó ra màn hình bằng `printf`."
                ),
                "reference_answer": None,
                "grading_rubric": json.dumps(
                    {"required_patterns": ["scanf", "printf"], "run_check": False},
                    ensure_ascii=False,
                ),
                "difficulty": 2,
            },
            {
                "question_type": "code",
                "prompt": (
                    "Viết đoạn code C đọc hai số nguyên `a` và `b` từ bàn phím bằng "
                    "`scanf`, rồi tính và in ra tổng, hiệu, tích và thương (chia) của hai "
                    "số bằng `printf`."
                ),
                "reference_answer": None,
                "grading_rubric": json.dumps(
                    {"required_patterns": ["scanf", "printf"], "run_check": False},
                    ensure_ascii=False,
                ),
                "difficulty": 4,
            },
        ],
    },
    {
        "topic": "string",
        "title": "Kiểm tra nhanh: Chuỗi (String) trong C",
        "questions": [
            {
                "question_type": "mcq",
                "prompt": (
                    "Trong C, một chuỗi ký tự (string) được lưu trữ dưới dạng gì? (A) Một "
                    "kiểu dữ liệu string riêng biệt (B) Một mảng các ký tự (`char`) kết "
                    "thúc bằng ký tự `\\0` (C) Một con trỏ tới số nguyên (D) Một struct có "
                    "sẵn tên String"
                ),
                "reference_answer": "B",
                "grading_rubric": None,
                "difficulty": 1,
            },
            {
                "question_type": "mcq",
                "prompt": (
                    "Hàm nào trong thư viện `string.h` dùng để tính độ dài của một chuỗi "
                    "(không tính ký tự `\\0`)? (A) sizeof() (B) length() (C) strlen() "
                    "(D) strcount()"
                ),
                "reference_answer": "C",
                "grading_rubric": None,
                "difficulty": 3,
            },
            {
                "question_type": "short_answer",
                "prompt": "Ký tự đặc biệt `\\0` (null character) ở cuối chuỗi trong C có ý nghĩa gì?",
                "reference_answer": (
                    "Ký tự '\\0' (giá trị 0) đánh dấu điểm kết thúc của một chuỗi ký tự "
                    "trong C. Các hàm xử lý chuỗi như strlen, printf (%s) dựa vào ký tự "
                    "này để biết chuỗi kết thúc ở đâu, vì mảng char chứa chuỗi có thể có "
                    "kích thước lớn hơn độ dài thực của chuỗi."
                ),
                "grading_rubric": json.dumps(
                    {"keywords": ["kết thúc chuỗi", "null", "ký tự"]}, ensure_ascii=False
                ),
                "difficulty": 2,
            },
            {
                "question_type": "short_answer",
                "prompt": "Phân biệt hàm `strcpy` và `strcat` trong thư viện `string.h`.",
                "reference_answer": (
                    "strcpy(dest, src) sao chép (copy) toàn bộ nội dung chuỗi src vào "
                    "dest, ghi đè nội dung cũ của dest. strcat(dest, src) nối "
                    "(concatenate) chuỗi src vào cuối chuỗi dest hiện có, giữ nguyên nội "
                    "dung ban đầu của dest và thêm src vào sau."
                ),
                "grading_rubric": json.dumps(
                    {"keywords": ["strcpy", "strcat", "nối chuỗi"]}, ensure_ascii=False
                ),
                "difficulty": 4,
            },
            {
                "question_type": "code",
                "prompt": (
                    "Viết đoạn code C đọc một chuỗi (không chứa khoảng trắng) từ bàn phím "
                    "vào một mảng `char` bằng `scanf`, sau đó tính và in ra độ dài của "
                    "chuỗi bằng hàm `strlen`."
                ),
                "reference_answer": None,
                "grading_rubric": json.dumps(
                    {"required_patterns": ["scanf", "strlen", "printf"], "run_check": False},
                    ensure_ascii=False,
                ),
                "difficulty": 3,
            },
            {
                "question_type": "code",
                "prompt": (
                    "Viết đoạn code C nhập một chuỗi ký tự từ bàn phím, dùng vòng lặp `for` "
                    "để đảo ngược chuỗi (in ra các ký tự theo thứ tự ngược lại), không "
                    "dùng hàm đảo chuỗi có sẵn."
                ),
                "reference_answer": None,
                "grading_rubric": json.dumps(
                    {"required_patterns": ["for", "scanf", "printf"], "run_check": False},
                    ensure_ascii=False,
                ),
                "difficulty": 5,
            },
        ],
    },
]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        topics_by_name: dict[str, Topic] = {t.name: t for t in db.query(Topic).all()}
        for name in TOPIC_NAMES:
            if name not in topics_by_name:
                topic = Topic(name=name)
                db.add(topic)
                db.flush()
                topics_by_name[name] = topic
        db.commit()
        print(f"Topics: {len(topics_by_name)} (đã có hoặc vừa tạo)")

        quizzes_by_title: dict[str, Quiz] = {q.title: q for q in db.query(Quiz).all()}
        new_quizzes = 0
        new_questions = 0
        for quiz_seed in QUIZ_SEED:
            quiz = quizzes_by_title.get(quiz_seed["title"])
            if quiz is None:
                topic = topics_by_name.get(quiz_seed["topic"])
                quiz = Quiz(topic_id=topic.id if topic else None, title=quiz_seed["title"])
                db.add(quiz)
                db.flush()
                quizzes_by_title[quiz_seed["title"]] = quiz
                new_quizzes += 1
                existing_prompts: set[str] = set()
            else:
                existing_prompts = {
                    q.prompt for q in db.query(Question).filter(Question.quiz_id == quiz.id).all()
                }

            added = 0
            for q in quiz_seed["questions"]:
                if q["prompt"] in existing_prompts:
                    continue
                db.add(
                    Question(
                        quiz_id=quiz.id,
                        question_type=q["question_type"],
                        prompt=q["prompt"],
                        reference_answer=q["reference_answer"],
                        grading_rubric=q["grading_rubric"],
                        difficulty=q["difficulty"],
                    )
                )
                existing_prompts.add(q["prompt"])
                added += 1
            new_questions += added
            print(f"  {quiz_seed['title']}: +{added} câu hỏi mới")

        db.commit()
        print(f"Hoàn tất — tạo mới {new_quizzes} quiz, thêm {new_questions} câu hỏi mới.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
