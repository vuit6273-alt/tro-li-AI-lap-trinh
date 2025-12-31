import streamlit as st
import google.generativeai as genai
import sys
import io
import traceback
import time
from contextlib import redirect_stdout

# --- CẤU HÌNH GIAO DIỆN WEB ---
st.set_page_config(
    page_title="Smart Coding Mentor - AI Trợ lý Tin học",
    page_icon="🤖",
    layout="wide"
)

# --- CSS TÙY CHỈNH (Giao diện chuyên nghiệp cho KHKT) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code&family=Inter:wght@400;600&display=swap');
    
    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
    }

    /* Khung soạn thảo code */
    .stTextArea textarea {
        font-family: 'Fira Code', monospace;
        background-color: #1e1e1e;
        color: #d4d4d4;
        font-size: 15px;
        line-height: 1.6;
        border-radius: 10px;
    }

    /* Khung Mentor phản hồi */
    .mentor-box {
        background-color: #ffffff;
        border-left: 6px solid #1e88e5;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        color: #0d47a1;
        line-height: 1.7;
    }
</style>
""", unsafe_allow_html=True)

# --- HÀM THỰC THI CODE ---
def execute_python_code(code, user_input=""):
    output_buffer = io.StringIO()
    input_lines = user_input.split('\n')
    
    def mock_input(prompt=""):
        return input_lines.pop(0) if input_lines else ""

    try:
        with redirect_stdout(output_buffer):
            # Môi trường thực thi an toàn cơ bản
            exec_globals = {
                "input": mock_input,
                "__builtins__": __import__("builtins"),
                "math": __import__("math"),
                "random": __import__("random"),
                "datetime": __import__("datetime")
            }
            exec(code, exec_globals)
        return True, output_buffer.getvalue(), None, None
    except Exception:
        exc_type, exc_value, exc_tb = sys.exc_info()
        stack = traceback.extract_tb(exc_tb)
        line_no = stack[-1].lineno if stack else "không xác định"
        error_msg = f"{exc_type.__name__}: {exc_value}"
        return False, output_buffer.getvalue(), error_msg, line_no

# --- HÀM GỌI AI GEMINI ---
def call_gemini(prompt, system_instruction, api_key):
    if not api_key:
        return "⚠️ Vui lòng nhập Gemini API Key ở bảng bên trái để kích hoạt Mentor."
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-preview-09-2025",
            system_instruction=system_instruction
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Lỗi kết nối AI: {str(e)}"

# --- GIAO DIỆN NGƯỜI DÙNG ---
def main():
    st.markdown("<h1 style='text-align: center; color: #1565c0;'>🚀 SMART CODING MENTOR</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Hệ thống trợ lý AI hỗ trợ tư duy lập trình cá nhân hóa</p>", unsafe_allow_html=True)

    with st.sidebar:
        st.header("⚙️ Cấu hình hệ thống")
        api_key = st.text_input("Gemini API Key:", type="password", help="Lấy key tại aistudio.google.com")
        st.divider()
        grade = st.selectbox("Đối tượng học sinh:", ["Khối 10", "Khối 11", "Khối 12"])
        st.info("💡 Mentor sẽ điều chỉnh cách giải thích phù hợp với khối lớp của bạn.")

    col_code, col_out = st.columns([3, 2])

    with col_code:
        st.subheader("📝 Soạn thảo Code")
        code_input = st.text_area("Nhập mã Python:", height=400, placeholder="# Viết code của em vào đây...")
        user_input_data = st.text_input("📥 Dữ liệu vào (Input):", placeholder="Nhập các giá trị cách nhau bằng dấu xuống dòng")

        c1, c2, c3 = st.columns(3)
        run_btn = c1.button("▶️ Chạy thử", use_container_width=True)
        mentor_btn = c2.button("🧐 Hỏi Mentor", use_container_width=True)
        sol_btn = c3.button("🔑 Xem lời giải", use_container_width=True)

    with col_out:
        st.subheader("🖥️ Kết quả & Gợi ý")
        output_placeholder = st.empty()

        if run_btn:
            if not code_input.strip():
                st.warning("Em chưa nhập code nhé!")
            else:
                success, out, err, line = execute_python_code(code_input, user_input_data)
                with output_placeholder.container():
                    if success:
                        st.success("✅ Chương trình chạy thành công!")
                        st.code(out if out else "[Không có dữ liệu xuất]")
                    else:
                        st.error(f"❌ Phát hiện lỗi tại dòng {line}")
                        st.info(f"**Lỗi:** {err}")

        st.divider()
        if mentor_btn:
            if not code_input.strip():
                st.info("Nhập code trước khi hỏi Mentor nhé.")
            else:
                with st.spinner("Thầy Mentor đang xem bài..."):
                    _, _, err, line = execute_python_code(code_input, user_input_data)
                    sys_msg = f"""
                    Bạn là giáo viên Tin học THPT tại Việt Nam, dạy học sinh {grade}.
                    QUY TẮC: Không bao giờ cho code đúng ngay lập tức.
                    Nhiệm vụ: Giải thích lỗi '{err}' ở dòng {line} bằng phương pháp gợi mở (Socratic).
                    Hãy đặt câu hỏi để học sinh tự nhận ra mình sai ở đâu.
                    """
                    prompt = f"Mã nguồn của học sinh:\n{code_input}\n\nThông báo lỗi: {err}"
                    hint = call_gemini(prompt, sys_msg, api_key)
                    st.markdown(f"<div class='mentor-box'><b>👨‍🏫 Mentor hướng dẫn:</b><br><br>{hint}</div>", unsafe_allow_html=True)

        if sol_btn:
            with st.expander("SPOILER: Xem mã nguồn chuẩn"):
                with st.spinner("Đang chuẩn bị..."):
                    sol = call_gemini(f"Viết code chuẩn và giải thích cho bài này: {code_input}", "Bạn là lập trình viên giỏi, cung cấp code sạch và giải thích.", api_key)
                    st.code(sol, language="python")

if __name__ == "__main__":
    main()