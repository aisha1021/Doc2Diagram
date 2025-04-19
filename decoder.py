import base64

# Replace with your image path
image_path = "../test.jpg"

# Read and convert the image
with open(image_path, "rb") as image_file:
    encoded_string = base64.b64encode(image_file.read()).decode("utf-8")

# Create the proper JSON format
json_body = '{{"image": "data:image/jpeg;base64,{0}"}}'.format(encoded_string)

print(json_body)
