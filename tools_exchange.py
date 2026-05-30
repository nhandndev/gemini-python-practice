import re
import asyncio
from google.genai import types # type: ignore

# Dòng 22: Danh sách các đơn vị tiền tệ được cho phép xử lý
ALLOWED_CURRENCIES = ["USD", "EUR", "MXN", "JPY", "GBP"]

# Dòng 23: Trình trích xuất Regular Expression cho mã tiền tệ
CURRENCY_REGEX = re.compile(r"\b(USD|EUR|MXN|JPY|GBP)\b", re.IGNORECASE)

# Dòng 24: Giới hạn lượng giao dịch tối đa
MAX_AMOUNT = 1000000.0


# Dòng 28: Lớp ExchangeRequest để tiền xử lý và kiểm tra dữ liệu đầu vào
class ExchangeRequest:
    def __init__(self, from_currency: str, to_currency: str, amount: float = 1.0):
        # Dòng 31-32: Lưu lại và chuyển đổi thành chữ hoa
        self.raw_from = str(from_currency).upper().strip()
        self.raw_to = str(to_currency).upper().strip()
        
        # Dòng 35-54: Các bước chuẩn hóa và kiểm tra nghiệp vụ
        if self.raw_from not in ALLOWED_CURRENCIES:
            raise ValueError(f"Currency '{from_currency}' is not supported.")
            
        if self.raw_to not in ALLOWED_CURRENCIES:
            raise ValueError(f"Currency '{to_currency}' is not supported.")
            
        try:
            self.amount = float(amount)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid amount format: {amount}")
            
        if self.amount <= 0 or self.amount > MAX_AMOUNT:
            raise ValueError(f"Amount must be between 0 and {MAX_AMOUNT}")

        self.from_currency = self.raw_from
        self.to_currency = self.raw_to


# Dòng 61-71: Hàm FetchExchangeRate bất đồng bộ (giả lập API ngoài)
async def fetch_exchange_rate(from_currency: str, to_currency: str) -> float:
    # Dòng 63: Chờ 0.3 giây giả lập độ trễ mạng
    await asyncio.sleep(0.3)
    
    # Bảng tỷ giá demo cố định dựa trên kết quả kịch bản video
    # Gốc USD làm chuẩn:
    usd_rates = {
        "USD": 1.0,
        "EUR": 0.92,  # 100 USD đổi sang 92 EUR
        "MXN": 17.0,  # 200 USD đổi sang 3400 MXN
        "JPY": 150.0,
        "GBP": 0.80,
    }
    
    # Trường hợp đặc biệt được mô tả: 50 EUR đổi sang 54 USD (tỷ giá ~ 1.08)
    if from_currency == "EUR" and to_currency == "USD":
        return 1.08

    rate_from = usd_rates.get(from_currency)
    rate_to = usd_rates.get(to_currency)
    
    if rate_from is None or rate_to is None:
        raise ValueError(f"No exchange rate found for {from_currency} -> {to_currency}")
        
    return rate_to / rate_from


# Dòng 74-85: Wrapper chạy toàn bộ quy trình xử lý quy đổi bất đồng bộ
async def execute_exchange(from_currency: str, to_currency: str, amount: float = 1.0) -> dict:
    try:
        req = ExchangeRequest(from_currency, to_currency, amount)
        rate = await fetch_exchange_rate(req.from_currency, req.to_currency)
        converted = req.amount * rate
        
        return {
            "status": "success",
            "from_currency": req.from_currency,
            "to_currency": req.to_currency,
            "amount": req.amount,
            "exchange_rate": rate,
            "converted_amount": round(converted, 2)
        }
    except ValueError as e:
        return {
            "status": "error",
            "message": str(e)
        }


# Dòng 90: Khai báo đặc tả hàm (Function Declaration) dạng JSON schema
exchange_declaration = types.FunctionDeclaration(
    name="execute_exchange",
    description="Calculate and execute currency exchange based on current deterministic demo rates.",
    # Dòng 97: Định nghĩa các tham số đầu vào
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            # Dòng 100-102
            "from_currency": types.Schema(
                type=types.Type.STRING,
                description="The currency ID to convert from (e.g., USD, EUR)."
            ),
            # Dòng 104-106
            "to_currency": types.Schema(
                type=types.Type.STRING,
                description="The currency ID to convert to (e.g., EUR, MXN)."
            ),
            # Dòng 108-111 (Amount là tùy chọn, kiểu số thực có giá trị tối thiểu)
            "amount": types.Schema(
                type=types.Type.NUMBER,
                description="The amount of currency to convert. (Optional)",
                minimum=0.0
            )
        },
        required=["from_currency", "to_currency"],
        # Dòng 115: Ngăn chặn mô hình gửi thêm các khóa không khai báo
        additional_properties=False
    )
)

# Dòng 120: Đóng gói khai báo trên thành một types.Tool
exchange_tool = types.Tool(function_declarations=[exchange_declaration])