import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from tkinter import Tk, Label, Entry, Button, filedialog, colorchooser, Listbox, Menu, Toplevel, Canvas, Scale
from PIL import Image, ImageTk, ImageDraw
import os
import threading
import queue
import webbrowser


# Global variables
generated_images = []
logo_path = None
logo_size = 80  # Default logo size
status_queue = queue.Queue()


def create_gradient(size, color1, color2):
    """Creates a gradient for QR code foreground."""
    base = Image.new('RGBA', size, color1)
    overlay = Image.new('RGBA', size, color2)
    mask = Image.new('L', size)
    draw = ImageDraw.Draw(mask)

    for i in range(size[0]):
        draw.rectangle([i, 0, i + 1, size[1]], fill=int(255 * (i / size[0])))

    return Image.composite(base, overlay, mask)


def generate_qrs():
    data_list = data_listbox.get(0, "end")
    if not data_list:
        # Use after() to schedule status update in the main thread
        root.after(0, status_queue.put, "Please add at least one string.")
        return

    color1 = qr_color_button["bg"]
    color2 = bg_color_button["bg"]

    global generated_images
    generated_images = []

    for data in data_list:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=15,
            border=1,
        )
        qr.add_data(data)
        qr.make(fit=True)

        qr_img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=RoundedModuleDrawer(),
        ).convert("RGBA")

        qr_img = apply_gradient_to_modules(qr_img, color1, color2)

        if logo_path:
            try:
                logo = Image.open(logo_path).convert("RGBA")
                logo.thumbnail((logo_size, logo_size))  # Use logo_size variable here
                logo_pos = (
                    (qr_img.size[0] - logo.size[0]) // 2,
                    (qr_img.size[1] - logo.size[1]) // 2,
                )
                qr_img.paste(logo, logo_pos, mask=logo)
            except Exception as e:
                root.after(0, status_queue.put, f"Error adding logo: {e}")

        blue_frame_size = 39
        qr_img_with_bg = Image.new(
            "RGBA",
            (qr_img.size[0] + blue_frame_size, qr_img.size[1] + blue_frame_size),
            (173, 216, 230, 255),
        )
        qr_img_with_bg.paste(qr_img, (blue_frame_size // 2, blue_frame_size // 2), qr_img)

        generated_images.append(qr_img_with_bg)

    # Update the status in the main thread after QR code generation
    root.after(0, status_queue.put, "QR codes generated successfully!")


def apply_gradient_to_modules(qr_img, color1, color2):
    """Apply a gradient color to the black and white modules of the QR code."""
    width, height = qr_img.size
    pixel_data = qr_img.load()

    # Create a gradient background
    gradient = create_gradient((width, height), color1, color2)

    # Apply the gradient to each module (black and white parts)
    for y in range(height):
        for x in range(width):
            if pixel_data[x, y] == (0, 0, 0, 255):  # If the module is black
                pixel_data[x, y] = gradient.getpixel((x, y))
            elif pixel_data[x, y] == (255, 255, 255, 255):  # If the module is white
                pixel_data[x, y] = (255, 255, 255, 255)  # Keep white as is

    return qr_img


def save_qrs():
    if not generated_images:
        status_label.config(text="No QR codes to save.", fg="red")
        return

    save_dir = filedialog.askdirectory()
    if save_dir:
        for i, img in enumerate(generated_images):
            # Save each QR code at a higher resolution (600 dpi)
            img.save(os.path.join(save_dir, f"qr_code_{i+1}.png"), dpi=(600, 600))
        status_label.config(text="QR codes saved successfully!", fg="green")


def add_to_list():
    data = data_entry.get()
    if data:
        data_listbox.insert("end", data)
        data_entry.delete(0, "end")


def remove_selected():
    selected = data_listbox.curselection()
    for index in selected[::-1]:
        data_listbox.delete(index)


def choose_qr_color():
    color = colorchooser.askcolor(title="Choose start gradient color")[1]
    if color:
        qr_color_button.config(bg=color)


def choose_bg_color():
    color = colorchooser.askcolor(title="Choose end gradient color")[1]
    if color:
        bg_color_button.config(bg=color)


def upload_logo():
    global logo_path
    logo_path = filedialog.askopenfilename(
        filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif"), ("All files", "*.*")]
    )
    if logo_path:
        status_label.config(text=f"Logo selected: {os.path.basename(logo_path)}", fg="green")


def show_about():
    about_window = Toplevel(root)
    about_window.title("About")
    about_window.geometry("400x200")
    about_window.resizable(False, False)
    
    # Display text with clickable link
    about_text = Label(
        about_window,
        text="QR Blazer\nVersion 4.1\n\nDeveloped by Peter De Ceuster\n© 2024 All Rights Reserved\n\nBuy me a coffee: ",
        font=("Arial", 12),
        justify="center"
    )
    about_text.pack(expand=True)
    
    # Create the clickable link label
    link = Label(about_window, text="Buy me a coffee", fg="blue", cursor="hand2")
    link.pack()
    link.bind("<Button-1>", lambda e: webbrowser.open("https://buymeacoffee.com/siglabo"))

    # Create the clickable link label
    link = Label(about_window, text="visit our site", fg="blue", cursor="hand2")
    link.pack()
    link.bind("<Button-1>", lambda e: webbrowser.open("peterdeceuster.uk"))


def show_preview():
    if not generated_images:
        status_label.config(text="No QR codes generated to preview.", fg="red")
        return
    
    # Show the first QR code as a preview
    preview_window = Toplevel(root)
    preview_window.title("QR Code Preview")
    preview_window.geometry("300x300")
    
    # Convert the first QR code to a format that can be displayed by Tkinter
    qr_preview_img = generated_images[0].resize((300, 300))
    qr_preview_img_tk = ImageTk.PhotoImage(qr_preview_img)
    
    # Create a label to display the image
    label = Label(preview_window, image=qr_preview_img_tk)
    label.image = qr_preview_img_tk  # Keep a reference to avoid garbage collection
    label.pack(pady=20)

    Button(preview_window, text="Close Preview", command=preview_window.destroy).pack()


def update_status():
    while not status_queue.empty():
        message = status_queue.get()
        status_label.config(text=message)
    # Continue checking the status queue
    root.after(100, update_status)


def generate_qrs_thread():
    threading.Thread(target=generate_qrs, daemon=True).start()


# Initialize GUI
root = Tk()
root.title("QR Blazer")
root.geometry("1024x768")
root.state("zoomed")

# Set custom icon
icon_path = os.path.join(os.getcwd(), "logo.png")
if os.path.exists(icon_path):
    root.iconphoto(True, ImageTk.PhotoImage(Image.open(icon_path)))


# Gradient background
canvas = Canvas(root)
canvas.place(relwidth=1, relheight=1)  # Set canvas size to cover the whole window

def set_gradient_background(event=None):
    gradient_img = create_gradient((root.winfo_width(), root.winfo_height()), "#FF7F50", "#FFFFFF")  # Example colors
    gradient_img_tk = ImageTk.PhotoImage(gradient_img)
    canvas.create_image(0, 0, anchor="nw", image=gradient_img_tk)
    canvas.image = gradient_img_tk  # Keep reference to prevent garbage collection

root.bind("<Configure>", set_gradient_background)


# Menu bar
menu_bar = Menu(root)
file_menu = Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Save QR Codes", command=save_qrs)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)
menu_bar.add_cascade(label="File", menu=file_menu)

help_menu = Menu(menu_bar, tearoff=0)
help_menu.add_command(label="About", command=show_about)
menu_bar.add_cascade(label="Help", menu=help_menu)

root.config(menu=menu_bar)

# Input fields
Label(root, text="Enter Data/URL:").grid(row=0, column=0, padx=5, pady=5)
data_entry = Entry(root, width=50)
data_entry.grid(row=0, column=1, padx=5, pady=5)
Button(root, text="Add", command=add_to_list).grid(row=0, column=2, padx=5, pady=5)

# Data List
Label(root, text="Data List:").grid(row=1, column=0, padx=5, pady=5)
data_listbox = Listbox(root, width=50, height=10, selectmode="extended")
data_listbox.grid(row=1, column=1, padx=5, pady=5, columnspan=2)

# Buttons (Left and Right aligned)
Button(root, text="Generate QR Codes", command=generate_qrs_thread).grid(row=2, column=0, padx=10, pady=10)
Button(root, text="Save QR Codes", command=save_qrs).grid(row=2, column=1, padx=10, pady=10)
Button(root, text="Show Preview", command=show_preview).grid(row=2, column=2, padx=10, pady=10)

# Color pickers (on the left)
Label(root, text="QR Code Color:").grid(row=3, column=0, padx=5, pady=5)
qr_color_button = Button(root, bg="black", width=20, command=choose_qr_color)
qr_color_button.grid(row=3, column=1, padx=5, pady=5)

Label(root, text="Background Color:").grid(row=4, column=0, padx=5, pady=5)
bg_color_button = Button(root, bg="white", width=20, command=choose_bg_color)
bg_color_button.grid(row=4, column=1, padx=5, pady=5)

# Logo upload and size (right side)
Button(root, text="Upload Logo", command=upload_logo).grid(row=5, column=0, padx=5, pady=10, columnspan=3)

Label(root, text="Logo Size:").grid(row=6, column=0, padx=5, pady=5)
logo_size_slider = Scale(root, from_=50, to=150, orient="horizontal", command=lambda value: globals().update({"logo_size": int(value)}))
logo_size_slider.set(logo_size)
logo_size_slider.grid(row=6, column=1, padx=5, pady=5)

# Status label
status_label = Label(root, text="Status: Waiting for input...", fg="blue")
status_label.grid(row=7, column=0, columnspan=3, pady=20)

# Start status update thread
update_status()

root.mainloop()
