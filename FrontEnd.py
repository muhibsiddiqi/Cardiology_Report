import streamlit as st
import os
import subprocess
from PIL import Image
import warnings
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from io import BytesIO
import textwrap


def create_pdf(patient_name, img1_path, img2_path, report_text):
    """Creates a professional A4 PDF with patient details, images, and a detailed report."""
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=A4)
    width, height = A4

    # Margins and spacing
    margin = 50
    line_height = 14

    # Positions for elements
    title_y_position = height - margin - 50
    patient_name_y_position = title_y_position - 30
    images_y_position = patient_name_y_position - 100
    summary_y_position = images_y_position - 250

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin, title_y_position, "Radiology Report")

    # Patient Name
    c.setFont("Helvetica", 12)
    c.drawString(margin, patient_name_y_position, f"Patient Name: {patient_name}")

    # Frontal Image
    image_width, image_height = 200, 200
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, images_y_position, "Frontal Image:")
    img1 = ImageReader(img1_path)
    c.drawImage(img1, margin, images_y_position - image_height - 10, width=image_width, height=image_height)

    # Lateral Image
    c.drawString(margin + image_width + 50, images_y_position, "Lateral Image:")
    img2 = ImageReader(img2_path)
    c.drawImage(img2, margin + image_width + 50, images_y_position - image_height - 10, width=image_width, height=image_height)

    # Report Summary
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin, summary_y_position, "Report Summary:")
    c.setFont("Helvetica", 12)
    report_text_y_position = summary_y_position - 20

    # Properly formatted and wrapped report text
    sentences = report_text.split(". ")
    formatted_text = ". ".join(sentence.capitalize() for sentence in sentences)
    wrapped_text = textwrap.wrap(formatted_text, width=90)

    for line in wrapped_text:
        c.drawString(margin, report_text_y_position, line)
        report_text_y_position -= line_height
        if report_text_y_position < margin + 50:
            c.showPage()
            c.setFont("Helvetica", 12)
            report_text_y_position = height - margin - 50

    # Footer with signature
    c.setFont("Helvetica-Bold", 16)
    footer_y_position = margin + 50
    c.drawString(margin, footer_y_position, "Prepared By:")

    # Adjust the y-position for the names to create space
    name_start_y_position = footer_y_position - 20  # Adding space between the footer title and names
    c.setFont("Helvetica", 12)
    c.drawString(margin, name_start_y_position, "Muhib Hussain Siddiqi (21K-3089)")
    c.drawString(margin, name_start_y_position - 12, "Fahad Salman Amim (21K-3103)")
    c.drawString(margin, name_start_y_position - 24, "Muhammad Omer Shoaib (21K-3066)")

    c.setFillColor(colors.black)


    # Save the PDF
    c.save()
    pdf_buffer.seek(0)
    return pdf_buffer.read()


# Suppress all warnings
warnings.filterwarnings('ignore')

# Define paths
uploaded_images = "uploaded_images"
results_images = "results_images"

# Ensure directories exist
os.makedirs(uploaded_images, exist_ok=True)
os.makedirs(results_images, exist_ok=True)

# Streamlit UI
st.set_page_config(page_title="R2GEN Model Report Generator", layout="wide")
st.title("R2GEN Model Report Generator")
st.markdown("""
    <style>
        .title {
            font-size: 36px;
            font-weight: bold;
            color: #007bff;
        }
        .subheader {
            font-size: 18px;
            color: #6c757d;
        }
        .button {
            background-color: #28a745;
            color: white;
            border-radius: 5px;
            padding: 10px 20px;
            font-size: 16px;
            font-weight: bold;
        }
        .warning {
            font-size: 16px;
            color: #dc3545;
        }
        .result-text {
            font-size: 14px;
            color: #6c757d;
        }
    </style>
""", unsafe_allow_html=True)

# Section description
st.markdown("<p class='subheader'>Upload two images (frontal and lateral) for generating the report.</p>", unsafe_allow_html=True)

# Image upload widgets
col1, col2 = st.columns(2)
with col1:
    image1 = st.file_uploader("Upload Frontal Image", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
with col2:
    image2 = st.file_uploader("Upload Lateral Image", type=["jpg", "png", "jpeg"], label_visibility="collapsed")

# Patient name input
patient_name = st.text_input("Enter Patient Name:")

# Display uploaded images
if image1 and image2:
    st.markdown("### Uploaded Images")
    
    # Load and resize images using PIL
    img1 = Image.open(image1).resize((500, 500))
    img2 = Image.open(image2).resize((500, 500))

    col1, col2 = st.columns(2)
    with col1:
        st.image(img1, caption="Frontal Image", use_container_width=True)
    with col2:
        st.image(img2, caption="Lateral Image", use_container_width=True)

# Button to generate report
if st.button("Generate Report", key="generate_report", help="Click to generate the report based on uploaded images"):
    if image1 and image2 and patient_name:
        # Save images to uploaded_images folder
        img1_path = os.path.join(uploaded_images, "image1.png")
        img2_path = os.path.join(uploaded_images, "image2.png")

        with open(img1_path, "wb") as f:
            f.write(image1.getbuffer())

        with open(img2_path, "wb") as f:
            f.write(image2.getbuffer())

        # Run the inference script
        st.write("Processing images...")

        try:
            # Construct the command for the batch file
            command = f'python inference.py ' \
                      f'--checkpoint "ran_models/1_best_model.pth" ' \
                      f'--image_paths "{img1_path}" "{img2_path}" ' \
                      f'--ann_path "data/iu_xray/annotation.json" ' \
                      f'--threshold 3'
            
            # Run the command
            result = subprocess.run(command, shell=True, capture_output=True, text=True)

            # Check if process was successful
            if result.returncode == 0:
                st.success("Report generated successfully!")

                # Create PDF with the patient name, images, and report
                pdf = create_pdf(patient_name, img1_path, img2_path, result.stdout)

                # Provide download link
                pdf_file = BytesIO(pdf)
                st.download_button("Download Report", pdf_file, file_name=f"{patient_name}_report.pdf", mime="application/pdf")
            else:
                # Display any error messages
                error_message = result.stderr or "Unknown error occurred"
                st.error(f"Error in processing: {error_message}")

        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
    else:
        st.warning("Please upload both images and enter the patient's name to proceed.", icon="⚠️")