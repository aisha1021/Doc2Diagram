from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import os
import base64
from perform import SmartDocumentProcessor
import asyncio
from PIL import Image
import io

app = Flask(__name__)
CORS(app, supports_credentials=True)


@app.route("/process-document", methods=["POST"])
def process_document():
    try:
        print("Received request")
        print("Request headers:", dict(request.headers))
        print("Request files:", request.files)

        if "file" not in request.files:
            print("No file part in request")
            return {"error": "No file part"}, 400

        file = request.files["file"]
        if file.filename == "":
            print("No selected file")
            return {"error": "No selected file"}, 400

        print(f"Processing file: {file.filename}")

        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)

        file_path = os.path.join(temp_dir, file.filename)
        file.save(file_path)
        print(f"File saved at: {file_path}")

        processor = SmartDocumentProcessor()
        asyncio.run(processor.process())

        png_path = os.path.join(temp_dir, "workflow.png")
        if os.path.exists(png_path):
            return send_file(
                png_path,
                mimetype="image/png",
                as_attachment=True,
                download_name="workflow.png",
            )
        else:
            return {"error": "Failed to generate diagram"}, 500

    except Exception as e:
        import traceback

        print(f"Error occurred: {str(e)}")
        traceback.print_exc()
        return {"error": str(e)}, 500


@app.route("/process-camera", methods=["POST"])
def process_camera():
    try:
        print("Received request")
        print("Request headers:", dict(request.headers))
        print("Request files:", request.files)

        # Check for file
        if "file" not in request.files:
            print("No file part in request")
            return {"error": "No file part"}, 400

        file = request.files["file"]
        if file.filename == "":
            print("No selected file")
            return {"error": "No selected file"}, 400

        print(f"Processing file: {file.filename}")

        # Prepare temp directory
        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)

        # Clear existing files in temp directory
        for existing_file in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, existing_file)
            try:
                os.unlink(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")

        # Save the file
        file_path = os.path.join(temp_dir, file.filename)
        file.save(file_path)
        print(f"File saved at: {file_path}")

        # Process document
        processor = SmartDocumentProcessor()
        asyncio.run(processor.process())

        # Return the generated PNG
        png_path = os.path.join(temp_dir, "workflow.png")
        if os.path.exists(png_path):
            return send_file(
                png_path,
                mimetype="image/png",
                as_attachment=True,
                download_name="workflow.png",
            )
        else:
            return {"error": "Failed to generate diagram"}, 500

    except Exception as e:
        import traceback

        print(f"Error occurred: {str(e)}")
        traceback.print_exc()
        return {"error": str(e)}, 500


if __name__ == "__main__":
    app.run(debug=True, port=5001, host="0.0.0.0")
