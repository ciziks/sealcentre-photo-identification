from flask import Flask, render_template, request, redirect, url_for
from antidote import world, inject
from wrappers.Wildbook import Wildbook

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("landing_page.html")


@inject
@app.route("/upload_image", methods=["POST"])
def upload(wildbook: Wildbook = world[Wildbook]):
    if "image" not in request.files or "image_name" not in request.form:  # Check for image and image_name
        return redirect(request.url)
    
    image = request.files["image"]
    image_name = request.form["image_name"]  # Capture the name from the text input
    
    if image.filename == "":
        return redirect(request.url)

    # Save the file temporarily
    temp_image_path = "path_to_temp_storage" 
    image.save(temp_image_path)

    image_id = wildbook.upload_image(temp_image_path)

    gid_list = wildbook.detect_seal([image_id])

    wildbook.rename_annotations([gid_list], [image_name])  # Rename the uploaded image with the provided name
    
    # Handle the response
    return str(image_id)

if __name__ == "__main__":
    app.run(debug=True)
