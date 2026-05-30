import asyncio
from config import get_client, MODEL_NAME
from tools_exchange import exchange_tool, execute_exchange
from google.genai import types # type: ignore

async def main():
    # Khởi tạo Gemini Client từ cấu hình chung
    client = get_client()

    # Dòng 27-29: Yêu cầu bằng ngôn ngữ tự nhiên của người dùng
    user_content = "Please convert 250 US dollars into euros."
    
    print("--- Bước 1: Gửi yêu cầu tự nhiên đi kèm khai báo Tool ---")
    print(f"Yêu cầu: '{user_content}'")

    # Dòng 32-37: Gọi generate_content và truyền Tool vào cấu hình
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=user_content,
        config=types.GenerateContentConfig(
            tools=[exchange_tool]
        )
    )

    # Dòng 41-42: In thuộc tính text và danh sách function_calls của phản hồi
    print(f"Response Text (Trống nếu mô hình quyết định gọi hàm): '{response.text or ''}'")
    print(f"Response Function Calls: {response.function_calls}\n")

    # Dòng 49-52: Trích xuất và kiểm tra cuộc gọi hàm từ cấu trúc trả về
    if response.function_calls:
        function_call = response.function_calls[0]
        func_name = function_call.name
        func_args = function_call.args
        fc_id = getattr(function_call, "id", None) # Lấy ID định danh duy nhất của Gemini 3

        print("--- Bước 2: Kiểm tra cấu trúc cuộc gọi và Xác thực tham số ---")
        print(f"Tên hàm được yêu cầu: {func_name}")
        print(f"Tham số nhận được: {func_args}")
        print(f"ID cuộc gọi hàm (Gemini 3): {fc_id}\n")

        if func_name == "execute_exchange":
            from_curr = func_args.get("from_currency")
            to_curr = func_args.get("to_currency")
            amount = func_args.get("amount", 1.0)

            # Thực thi xử lý bất đồng bộ an toàn và có kiểm soát đầu vào
            print("Đang thực hiện tính toán tỷ giá bất đồng bộ...")
            result = await execute_exchange(
                from_currency=from_curr,
                to_currency=to_curr,
                amount=amount
            )
            print(f"Kết quả thực thi: {result}\n")

            print("--- Bước 3: Gửi kết quả ngược lại cho Gemini tích hợp và trả lời ---")
            
            # Xây dựng lịch sử hội thoại chuẩn hai lượt để gửi lại API
            history = [
                # Lượt 1: Yêu cầu của người dùng
                types.Content(
                    role="user", 
                    parts=[types.Part.from_text(text=user_content)]
                ),
                # Lượt 2: Phản hồi yêu cầu gọi hàm của mô hình
                response.candidates[0].content,
                # Lượt 3: Phản hồi kết quả của hàm (Tool Response) kèm ID đối chiếu
                types.Content(
                    role="tool",
                    parts=[
                        types.Part.from_function_response(
                            name=func_name,
                            response=result,
                            id=fc_id
                        )
                    ]
                )
            ]

            # Gửi lại toàn bộ lịch sử kèm Tool để mô hình sinh câu trả lời tự nhiên
            final_response = client.models.generate_content(
                model=MODEL_NAME,
                contents=history,
                config=types.GenerateContentConfig(
                    tools=[exchange_tool]
                )
            )

            print("Giải trình cuối cùng từ mô hình:")
            print(final_response.text)
    else:
        print("Mô hình không kích hoạt cuộc gọi hàm nào dựa trên yêu cầu này.")

if __name__ == "__main__":
    # Chạy vòng lặp sự kiện bất đồng bộ
    asyncio.run(main())