import streamlit as st
from PIL import Image, ImageOps
import zipfile
from io import BytesIO

# =========================
# CORE LOGIC
# =========================
def get_resolution_params(short_side: int):
    RESOLUTION_TIERS = [
        (7000, "8K", 7.0, 80),
        (3500, "4K", 7.0, 60),
        (2000, "2K", 8.0, 40),
        (1080, "Full HD", 9.0, 28),
        (720, "HD", 10.0, 18),
        (0, "SD", 10.0, 12),
    ]
    for min_px, name, logo_pct, padding in RESOLUTION_TIERS:
        if short_side >= min_px:
            return name, logo_pct, padding
    return "SD", 10.0, 12

def resize_logo(logo, target_w):
    orig_w, orig_h = logo.size
    target_h = int(orig_h * target_w / orig_w)
    return logo.resize((target_w, target_h), Image.LANCZOS)

def apply_opacity(logo, opacity_val):
    if opacity_val >= 100:
        return logo
    r, g, b, a = logo.split()
    a = a.point(lambda x: int(x * opacity_val / 100))
    return Image.merge("RGBA", (r, g, b, a))

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Tool Pro",
    layout="wide"
)

# =========================
# CUSTOM CSS (FIX TRÌNH ĐƠN & UPLOAD)
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;700&display=swap');

/* GLOBAL */
html, body, [data-testid="stAppViewContainer"], .stApp {
    font-family: 'Montserrat', sans-serif !important;
    background-color: #0b0c10 !important;
}

/* --- FIX LỖI MENU 3 CHẤM (THEME POPUP) --- */
/* Ẩn các icon dạng text bị lỗi (light_mode, dark_mode...) */
[data-baseweb="popover"] ul li button span:first-child,
[data-baseweb="popover"] div[role="presentation"] > div:first-child {
    display: none !important;
}

/* Hiển thị lại text System/Light/Dark chuẩn font Montserrat */
[data-baseweb="popover"] ul li button span:last-child {
    display: block !important;
    font-family: 'Montserrat', sans-serif !important;
    font-size: 14px !important;
    color: white !important;
}

/* Thêm icon Emoji mới thay thế icon lỗi */
[data-baseweb="popover"] ul li:nth-child(1) button::before { content: "🖥️ "; margin-right: 10px; }
[data-baseweb="popover"] ul li:nth-child(2) button::before { content: "☀️ "; margin-right: 10px; }
[data-baseweb="popover"] ul li:nth-child(3) button::before { content: "🌙 "; margin-right: 10px; }

/* Căn chỉnh lại menu popup */
[data-baseweb="popover"] ul li button {
    padding: 12px 20px !important;
    justify-content: flex-start !important;
}

/* --- FIX LỖI UPLOAD ĐÈ CHỮ --- */
[data-testid="stFileUploader"] section { 
    padding: 15px !important; 
}
/* Ẩn triệt để nút gốc và text gốc của Streamlit */
[data-testid="stFileUploader"] section button, 
[data-testid="stFileUploader"] section span { 
    display: none !important; 
}
/* Tạo lớp phủ mới sạch sẽ */
[data-testid="stFileUploader"] section::before {
    content: "📁 Kéo thả hoặc Click để chọn file";
    display: block;
    text-align: center;
    color: #ffffff;
    font-size: 14px;
    padding: 20px;
    border: 1px dashed rgba(255, 255, 255, 0.3);
    border-radius: 10px;
    cursor: pointer;
    width: 100%;
}
[data-testid="stFileUploaderDropzoneInstructions"] { 
    display: none !important; 
}

/* SLIDER TRẮNG */
div[data-baseweb="slider"] > div > div { background: rgba(255, 255, 255, 0.2) !important; }
div[data-baseweb="slider"] > div > div > div > div { background: #ffffff !important; }
div[role="slider"] { background-color: #ffffff !important; border: 2px solid #ffffff !important; }
div[data-testid="stThumbValue"] { color: #ffffff !important; }

/* GLASS CARD */
.glass-card {
    background: #12131c;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 24px;
}
.stButton > button {
    width: 100%; height: 50px;
    border: 1px solid #ffffff; border-radius: 12px;
    background: transparent; color: #ffffff;
    font-weight: 700; transition: 0.2s;
}
.stButton > button:hover { background: #ffffff !important; color: #0b0c10 !important; }
</style>
""", unsafe_allow_html=True)

# =========================
# TOP CONTROL PANEL
# =========================
st.title("Tool Pro")

st.markdown('<div class="glass-card">', unsafe_allow_html=True)
top1, top2, top3 = st.columns([1, 1, 1])

with top1:
    st.subheader("Logo 1")
    logo_l_file = st.file_uploader("Upload Logo 1", type=['png'], key="l1")
    size_l_ovr = st.slider("Size (%)", 0, 100, 0, key="s1")
    pad_l_ovr = st.slider("Padding (%)", 0, 50, 0, key="p1")

with top2:
    st.subheader("Logo 2")
    logo_r_file = st.file_uploader("Upload Logo 2", type=['png'], key="l2")
    size_r_ovr = st.slider("Size (%)", 0, 100, 0, key="s2")
    pad_r_ovr = st.slider("Padding (%)", 0, 50, 0, key="p2")

with top3:
    st.subheader("Settings")
    opacity = st.slider("Opacity (%)", 0, 100, 100, 5, key="opc")
st.markdown('</div>', unsafe_allow_html=True)

# =========================
# MAIN CONTENT
# =========================
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
col1, col2 = st.columns([1, 2])

with col1:
    pv_w, pv_h = 1000, 650
    canvas = Image.new("RGBA", (pv_w, pv_h), (35, 35, 35, 255))
    ss_pv = min(pv_w, pv_h)

    if logo_l_file:
        l_img = Image.open(logo_l_file).convert("RGBA")
        sz = size_l_ovr if size_l_ovr > 0 else 10
        pd = pad_l_ovr if pad_l_ovr > 0 else 5
        l_img = resize_logo(l_img, int(ss_pv * sz / 100))
        l_img = apply_opacity(l_img, opacity)
        canvas.paste(l_img, (int(pv_w*pd/100), int(pv_h*pd/100)), mask=l_img)

    if logo_r_file:
        r_img = Image.open(logo_r_file).convert("RGBA")
        sz = size_r_ovr if size_r_ovr > 0 else 10
        pd = pad_r_ovr if pad_r_ovr > 0 else 5
        r_img = resize_logo(r_img, int(ss_pv * sz / 100))
        r_img = apply_opacity(r_img, opacity)
        canvas.paste(r_img, (pv_w - r_img.width - int(pv_w*pd/100), int(pv_h*pd/100)), mask=r_img)
    
    st.image(canvas, use_container_width=True)

with col2:
    st.header("Xử lý hàng loạt")
    imgs = st.file_uploader("Chọn ảnh cần đóng dấu", type=['jpg','png','jpeg','webp'], accept_multiple_files=True, key="bulk")
    
    if st.button("🚀 Bắt đầu xử lý") and imgs:
        if not logo_l_file and not logo_r_file:
            st.error("Bạn phải upload ít nhất 1 logo!")
        else:
            zip_buf = BytesIO()
            bar = st.progress(0)
            l_orig = Image.open(logo_l_file).convert("RGBA") if logo_l_file else None
            r_orig = Image.open(logo_r_file).convert("RGBA") if logo_r_file else None

            with zipfile.ZipFile(zip_buf, "a", zipfile.ZIP_DEFLATED) as zf:
                for idx, f in enumerate(imgs):
                    img = ImageOps.exif_transpose(Image.open(f)).convert("RGBA")
                    w, h = img.size
                    ss = min(w, h)
                    tier, p_def, pad_def = get_resolution_params(ss)
                    
                    if l_orig:
                        sl = size_l_ovr if size_l_ovr > 0 else p_def
                        pl = pad_l_ovr if pad_l_ovr > 0 else pad_def
                        li = apply_opacity(resize_logo(l_orig, int(ss * sl / 100)), opacity)
                        img.paste(li, (int(w*pl/100), int(h*pl/100)), mask=li)
                    
                    if r_orig:
                        sr = size_r_ovr if size_r_ovr > 0 else p_def
                        pr = pad_r_ovr if pad_r_ovr > 0 else pad_def
                        ri = apply_opacity(resize_logo(r_orig, int(ss * sr / 100)), opacity)
                        img.paste(ri, (w - ri.width - int(w*pr/100), int(h*pr/100)), mask=ri)

                    ob = BytesIO()
                    ext = f.name.split('.')[-1].upper()
                    fmt = 'JPEG' if ext in ['JPG', 'JPEG'] else 'PNG'
                    img.convert("RGB").save(ob, format=fmt, quality=95)
                    zf.writestr(f.name, ob.getvalue())
                    bar.progress((idx + 1) / len(imgs))
            
            st.success("Đã xử lý xong!")
            st.download_button("📥 Tải về file ZIP", zip_buf.getvalue(), "images_watermarked.zip")

st.markdown('</div>', unsafe_allow_html=True)
