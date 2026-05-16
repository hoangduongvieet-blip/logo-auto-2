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

    return logo.resize(
        (target_w, target_h),
        Image.LANCZOS
    )


def apply_opacity(logo, opacity):

    if opacity >= 1.0:
        return logo

    r, g, b, a = logo.split()

    a = a.point(
        lambda x: int(x * opacity)
    )

    return Image.merge(
        "RGBA",
        (r, g, b, a)
    )


# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Watermark Tool Pro",
    layout="wide"
)

# =========================
# CUSTOM CSS
# =========================
st.markdown("""
<style>

/* =========================
BACKGROUND
========================= */

.stApp {

    background:
        radial-gradient(circle at top left, #6d28d9 0%, transparent 30%),
        radial-gradient(circle at top right, #2563eb 0%, transparent 30%),
        radial-gradient(circle at bottom, #0f172a 10%, #020617 70%);

    color: white;
}

/* =========================
TITLE
========================= */

h1, h2, h3, h4, h5, h6, p, label {
    color: white !important;
}

/* =========================
GLASS CARD
========================= */

.glass-card {

    background: rgba(255,255,255,0.08);

    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);

    border: 1px solid rgba(255,255,255,0.12);

    border-radius: 24px;

    padding: 24px;

    box-shadow:
        0 8px 32px rgba(0,0,0,0.35);

    margin-bottom: 24px;
}

/* =========================
UPLOAD
========================= */

[data-testid="stFileUploader"] {

    background: rgba(255,255,255,0.05);

    border-radius: 18px;

    padding: 10px;
}

/* =========================
BUTTON
========================= */

.stButton > button {

    width: 100%;
    height: 54px;

    border: none;
    border-radius: 16px;

    background: linear-gradient(
        135deg,
        #7c3aed,
        #2563eb
    );

    color: white;

    font-weight: 700;
    font-size: 16px;

    transition: 0.3s ease;
}

.stButton > button:hover {

    transform: translateY(-2px);

    box-shadow:
        0 10px 25px rgba(124,58,237,0.45);
}

/* =========================
INPUT
========================= */

[data-baseweb="input"] {

    background: rgba(255,255,255,0.06);

    border-radius: 14px;
}

/* =========================
IMAGE
========================= */

img {
    border-radius: 20px;
}

/* =========================
SLIDER
========================= */

[data-baseweb="slider"] {
    padding-top: 10px;
}

</style>
""", unsafe_allow_html=True)

# =========================
# TITLE
# =========================
st.title("🖼️ Watermark Tool Pro")

# =========================
# TOP CONTROL PANEL
# =========================
st.markdown(
    '<div class="glass-card">',
    unsafe_allow_html=True
)

top1, top2, top3 = st.columns([1, 1, 1])

# =========================
# LOGO 1
# =========================
with top1:

    st.subheader("Logo 1")

    logo_l_file = st.file_uploader(
        "Upload Logo 1",
        type=['png']
    )

    size_l_ovr = st.number_input(
        "Size (%)",
        value=0,
        help="0 = Auto",
        key="size_logo_1"
    )

    pad_l_ovr = st.number_input(
        "Padding (px)",
        value=0,
        help="0 = Auto",
        key="pad_logo_1"
    )

# =========================
# LOGO 2
# =========================
with top2:

    st.subheader("Logo 2")

    logo_r_file = st.file_uploader(
        "Upload Logo 2",
        type=['png']
    )

    size_r_ovr = st.number_input(
        "Size (%)",
        value=0,
        help="0 = Auto",
        key="size_logo_2"
    )

    pad_r_ovr = st.number_input(
        "Padding (px)",
        value=0,
        help="0 = Auto",
        key="pad_logo_2"
    )

# =========================
# SETTINGS
# =========================
with top3:

    st.subheader("Settings")

    opacity = st.slider(
        "Opacity",
        0.0,
        1.0,
        1.0,
        0.1
    )

st.markdown(
    '</div>',
    unsafe_allow_html=True
)

# =========================
# MAIN GLASS CARD
# =========================
st.markdown(
    '<div class="glass-card">',
    unsafe_allow_html=True
)

col1, col2 = st.columns([1, 2])

# =========================
# PREVIEW
# =========================
with col1:

    preview_w = 1000
    preview_h = 650

    preview_bg = Image.new(
        "RGBA",
        (preview_w, preview_h),
        (35, 35, 35, 255)
    )

    short_side = min(
        preview_w,
        preview_h
    )

    mock_pct_l = (
        size_l_ovr
        if size_l_ovr > 0
        else 10
    )

    mock_pct_r = (
        size_r_ovr
        if size_r_ovr > 0
        else 10
    )

    mock_pad_l = (
        pad_l_ovr
        if pad_l_ovr > 0
        else 30
    )

    mock_pad_r = (
        pad_r_ovr
        if pad_r_ovr > 0
        else 30
    )

    logo_w_l = int(
        short_side * mock_pct_l / 100
    )

    logo_w_r = int(
        short_side * mock_pct_r / 100
    )

    canvas = preview_bg.copy()

    # =========================
    # PREVIEW LOGO 1
    # =========================
    if logo_l_file:

        logo_l_file.seek(0)

        l_prev = Image.open(
            logo_l_file
        ).convert("RGBA")

        l_prev = resize_logo(
            l_prev,
            logo_w_l
        )

        l_prev = apply_opacity(
            l_prev,
            opacity
        )

        canvas.paste(
            l_prev,
            (
                mock_pad_l,
                mock_pad_l
            ),
            mask=l_prev
        )

    # =========================
    # PREVIEW LOGO 2
    # =========================
    if logo_r_file:

        logo_r_file.seek(0)

        r_prev = Image.open(
            logo_r_file
        ).convert("RGBA")

        r_prev = resize_logo(
            r_prev,
            logo_w_r
        )

        r_prev = apply_opacity(
            r_prev,
            opacity
        )

        canvas.paste(
            r_prev,
            (
                preview_w - r_prev.width - mock_pad_r,
                mock_pad_r
            ),
            mask=r_prev
        )

    st.image(
        canvas,
        use_container_width=True
    )

# =========================
# PROCESSING
# =========================
with col2:

    st.header("Xử lý hàng loạt")

    uploaded_images = st.file_uploader(
        "Chọn ảnh cần đóng dấu",
        type=['jpg', 'jpeg', 'png', 'webp'],
        accept_multiple_files=True
    )

    if st.button("🚀 Bắt đầu xử lý") and uploaded_images:

        if not logo_l_file and not logo_r_file:

            st.error(
                "Bạn phải upload ít nhất 1 logo!"
            )

        else:

            zip_buffer = BytesIO()

            progress_bar = st.progress(0)

            # =========================
            # LOAD LOGO
            # =========================
            l_orig = (
                Image.open(
                    logo_l_file
                ).convert("RGBA")
                if logo_l_file else None
            )

            r_orig = (
                Image.open(
                    logo_r_file
                ).convert("RGBA")
                if logo_r_file else None
            )

            with zipfile.ZipFile(
                zip_buffer,
                "a",
                zipfile.ZIP_DEFLATED
            ) as zip_f:

                for idx, img_file in enumerate(uploaded_images):

                    # =========================
                    # FIX KHÔNG XOAY ẢNH
                    # =========================
                    img = ImageOps.exif_transpose(
                        Image.open(img_file)
                    ).convert("RGBA")

                    img_w, img_h = img.size

                    short_side = min(
                        img_w,
                        img_h
                    )

                    tier, pct, pad = get_resolution_params(
                        short_side
                    )

                    # =========================
                    # SIZE & PADDING LOGO 1
                    # =========================
                    pct_l = (
                        size_l_ovr
                        if size_l_ovr > 0
                        else pct
                    )

                    pad_l = (
                        pad_l_ovr
                        if pad_l_ovr > 0
                        else pad
                    )

                    # =========================
                    # SIZE & PADDING LOGO 2
                    # =========================
                    pct_r = (
                        size_r_ovr
                        if size_r_ovr > 0
                        else pct
                    )

                    pad_r = (
                        pad_r_ovr
                        if pad_r_ovr > 0
                        else pad
                    )

                    logo_w_l = max(
                        1,
                        int(short_side * pct_l / 100)
                    )

                    logo_w_r = max(
                        1,
                        int(short_side * pct_r / 100)
                    )

                    canvas = img.copy()

                    # =========================
                    # DÁN LOGO 1
                    # =========================
                    if l_orig:

                        l_img = apply_opacity(
                            resize_logo(
                                l_orig,
                                logo_w_l
                            ),
                            opacity
                        )

                        canvas.paste(
                            l_img,
                            (
                                pad_l,
                                pad_l
                            ),
                            mask=l_img
                        )

                    # =========================
                    # DÁN LOGO 2
                    # =========================
                    if r_orig:

                        r_img = apply_opacity(
                            resize_logo(
                                r_orig,
                                logo_w_r
                            ),
                            opacity
                        )

                        canvas.paste(
                            r_img,
                            (
                                img_w - r_img.width - pad_r,
                                pad_r
                            ),
                            mask=r_img
                        )

                    # =========================
                    # SAVE
                    # =========================
                    img_byte_arr = BytesIO()

                    ext = img_file.name.split('.')[-1].upper()

                    save_format = (
                        'JPEG'
                        if ext in ['JPG', 'JPEG']
                        else 'PNG'
                    )

                    canvas.convert("RGB").save(
                        img_byte_arr,
                        format=save_format,
                        quality=95
                    )

                    zip_f.writestr(
                        img_file.name,
                        img_byte_arr.getvalue()
                    )

                    progress_bar.progress(
                        (idx + 1) / len(uploaded_images)
                    )

            st.success("Đã xử lý xong!")

            st.download_button(
                "📥 Tải về file ZIP",
                zip_buffer.getvalue(),
                "images_watermarked.zip",
                "application/zip"
            )

st.markdown(
    '</div>',
    unsafe_allow_html=True
)