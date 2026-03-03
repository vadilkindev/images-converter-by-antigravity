import streamlit as st
from PIL import Image
import io
import zipfile

st.set_page_config(page_title="Image Converter", page_icon="🖼️", layout="centered")

st.title("🖼️ Image Format Converter")
st.write("Upload an image locally to convert it to PNG, JPEG, or WebP.")

uploaded_files = st.file_uploader("Choose images...", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True)

if uploaded_files:
    st.write(f"**{len(uploaded_files)} image(s) uploaded.**")
    
    st.write("### Conversion Options")
    # Select target format
    target_format = st.selectbox("Convert all to:", ["PNG", "JPEG", "WEBP"])
    
    if st.button("Convert All Images"):
        
        # Prepare an in-memory zip file
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for uploaded_file in uploaded_files:
                st.markdown(f"#### Processing: `{uploaded_file.name}`")
                try:
                    # Read the image
                    image = Image.open(uploaded_file)
                    
                    # Show image preview
                    st.image(image, caption=f"Original: {uploaded_file.name}", use_container_width=True)
                    
                    # Create a BytesIO buffer to save the new image
                    buf = io.BytesIO()
                    
                    # Formats like JPEG do not support transparency (alpha channel)
                    if target_format == "JPEG" and image.mode in ("RGBA", "P"):
                        image_to_save = image.convert("RGB")
                    else:
                        image_to_save = image
                    
                    # Check original size
                    uploaded_file.seek(0)
                    original_size_mb = len(uploaded_file.read()) / (1024 * 1024)
                    
                    # Compress if above 5MB
                    quality = 100
                    max_size_mb = 5.0
                    
                    if original_size_mb > max_size_mb:
                        st.warning(f"Image is {original_size_mb:.2f}MB (over 5MB). Compressing...")
                        
                        # Iteratively compress
                        while True:
                            iter_buf = io.BytesIO()
                            # If format supports quality parameter (JPEG/WEBP)
                            if target_format in ["JPEG", "WEBP"]:
                                image_to_save.save(iter_buf, format=target_format, quality=quality, optimize=True)
                            else:
                                # PNG compression using optimization 
                                image_to_save.save(iter_buf, format=target_format, optimize=True)
                            
                            size_mb = iter_buf.tell() / (1024 * 1024)
                            
                            if size_mb <= max_size_mb or quality <= 10:
                                if target_format == "PNG" and size_mb > max_size_mb:
                                    # Fallback: Resize image for PNG if optimization isn't enough
                                    st.info("Resizing image to meet size constraints for PNG.")
                                    width, height = image_to_save.size
                                    image_to_save = image_to_save.resize((int(width * 0.8), int(height * 0.8)), Image.LANCZOS)
                                    continue # Retry save and check size
                                buf = iter_buf
                                break
                            
                            # Decrease quality or resize depending on formula
                            if target_format != "PNG":
                                quality -= 10
                                
                    else:
                        # Save normally
                        image_to_save.save(buf, format=target_format)
                    
                    # Write to zip file
                    new_file_name = f"{uploaded_file.name.rsplit('.', 1)[0]}_converted.{target_format.lower()}"
                    zip_file.writestr(new_file_name, buf.getvalue())
                    
                    st.markdown("---")
                except Exception as e:
                    st.error(f"An error occurred while processing '{uploaded_file.name}': {e}")
        
        # After all files are processed, offer ZIP download
        zip_data = zip_buffer.getvalue()
        if zip_data:
            st.success("All images processed successfully!")
            st.download_button(
                label=f"⬇️ Download All Converted Images (.zip)",
                data=zip_data,
                file_name=f"converted_images.zip",
                mime="application/zip",
                # The key shouldn't be dynamic per uploaded file anymore
                key="download_all_zip"
            )
