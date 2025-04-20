import os
from pathlib import Path
from docx import Document
import PyPDF2
import google.generativeai as genai
from dotenv import load_dotenv
import json
import time
import subprocess
import platform
import atexit
import asyncio
from PIL import Image
import io
import traceback


class SmartDocumentProcessor:
    def __init__(self):
        load_dotenv()  # Load our API
        self.temp_dir = "temp"  # we save our temp directory
        os.makedirs(
            self.temp_dir, exist_ok=True
        )  # create it, if its already there than do nothing

        # Initialize Gemini models for us we use 2.0 flash its new experimental and an handle files/images
        print("Initializing Gemini models...")
        genai.configure(api_key=os.getenv("GEMINI_API"))
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
        self.model_vision = genai.GenerativeModel("gemini-2.0-flash-exp")
        print("Models initialized successfully!")

        # Register cleanup
        atexit.register(self._cleanup)

    # Cleanup function
    def _cleanup(self):
        """Clean up resources properly"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.stop()
            if not loop.is_closed():
                loop.close()
        except Exception:
            pass

    # Get the latest file in the temp directory
    def get_latest_file(self):
        print("\nLooking for files in temp directory...")
        files = [
            f
            for f in os.listdir(self.temp_dir)
            if f.endswith((".pdf", ".docx", ".png", ".jpg", ".jpeg"))
        ]
        if not files:
            raise Exception(
                "No PDF, DOCX, or image files (PNG/JPG) found in temp directory"
            )
        latest_file = max(
            [os.path.join(self.temp_dir, f) for f in files], key=os.path.getmtime
        )
        print(f"Found file: {latest_file}")
        return latest_file

    # basically loops through everything in the tmep folder and adds anything with a valid extension to an array and return the most recent of the files (theres typically only going to be 1 anyways)

    # Extract text from a document or PDF file
    def extract_text(self, file_path):
        extension = Path(file_path).suffix.lower()
        print(f"\nExtracting text from {extension} file...")

        # we are basically returning one big string from the extracted text from the file
        if extension == ".docx":
            doc = Document(file_path)
            text = "\n\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            print(f"Extracted {len(text)} characters from DOCX")
            return text
        elif extension == ".pdf":
            with open(file_path, "rb") as file:
                pdf = PyPDF2.PdfReader(file)
                text = "\n\n".join(page.extract_text() for page in pdf.pages)
                print(f"Extracted {len(text)} characters from PDF")
                return text
        raise ValueError(f"Unsupported file format: {extension}")

    # Process an image using Gemini 2.0 Flash
    async def process_image(self, image_path):
        """Process a PNG image using Gemini"""
        print("\nProcessing image with Gemini 2.0 Flash...")
        try:
            # Read and prepare the image
            with Image.open(image_path) as img:
                if img.mode != "RGB":
                    img = img.convert("RGB")
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format="PNG")
                img_bytes = img_byte_arr.getvalue()

            #  prompt for image analysis
            prompt = """Analyze this image and create a workflow diagram showing the relationships between elements.
            
            Key requirements:
            1. Process Identification:
               - Identify major visual elements as processes
               - Use descriptive names for processes
               - Each process should have both a title and description
            
            2. Flow Structure:
               - Identify connections between elements
               - Note any parallel processes or branches
               - Preserve the hierarchical structure from the image
            
            Return JSON in this format:
            {
                "nodes": [
                    {
                        "id": "process_name",
                        "text": "Description of what this element represents",
                        "type": "core"
                    }
                ],
                "edges": [
                    {
                        "from": "source_process",
                        "to": "target_process",
                        "label": "flow"
                    }
                ]
            }"""

            response = await self.model.generate_content_async(
                [prompt, img_bytes],
                generation_config={
                    "temperature": 0.3,
                    "top_p": 0.8,
                    "top_k": 40,
                },  # temperature is the randomness of the output, top_p is the probability of the output, top_k is the number of tokens to consider
            )

            # Process response
            response_text = (
                response.text.strip()
            )  # we strip the response text of any whitespace
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                result = json.loads(
                    json_str
                )  # we load the json string into a json object

                # Update node IDs
                nodes = result.get("nodes", [])
                for i, node in enumerate(nodes, 1):
                    node["id"] = f"node_{i}"

                print(f"Analysis complete. Found {len(nodes)} components.")
                return result
            else:
                raise ValueError("No valid JSON found in response")

        except Exception as e:
            print(f"Image analysis error: {str(e)}")
            return {
                "nodes": [
                    {
                        "id": "error_node",
                        "text": "Error analyzing image. Please try with a different image.",
                        "type": "error",
                    }
                ],
                "edges": [],
            }

    # Process a document using Gemini 2.0 Flash
    async def analyze_with_gemini(self, text):
        print("\nAnalyzing document content with Gemini 2.0 Flash...")

        prompt = """Create a comprehensive workflow diagram that shows how different processes interact and flow within the system.  Only base it off information provided

Key requirements:
1. Process Identification:
   - Identify major system processes
   - Use clear, technical naming for processes (lowercase with underscores)
   - Each process should have both a title and detailed description

2. Process Details:
   For each process, provide:
   - Title: Short, technical name (e.g., 'data_integration', 'claims_processing')
   - Description: 2-3 lines explaining key functionality
   - Type: Either 'core' or 'support' process

3. Flow Structure:
   - Multiple processes can run in parallel
   - Processes can converge or branch based on logic
   - Show both primary and secondary workflows
   - Include branching paths where relevant

Return JSON in this format:
{
    "nodes": [
        {
            "id": "process_name",
            "text": "Detailed description of functionality",
            "type": "core"
        }
    ],
    "edges": [
        {
            "from": "source_process",
            "to": "target_process",
            "label": "flow"
        }
    ]
}

Create a natural flow that allows for parallel processes and interconnected workflows."""

        try:
            print("Processing document...")
            max_length = 100000  # Much higher limit for Gemini 2.0
            if len(text) > max_length:
                text = text[:max_length] + "..."
                print(
                    "Document truncated to fit model limits (but using much higher limit)"
                )

            response = await self.model.generate_content_async(
                prompt + "\n\nDocument text:\n" + text,
                generation_config={"temperature": 0.3, "top_p": 0.8, "top_k": 40},
            )

            # Clean and parse response
            response_text = response.text.strip()

            # Find JSON in response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                result = json.loads(json_str)

                # Update node IDs
                nodes = result.get("nodes", [])
                for i, node in enumerate(nodes, 1):
                    node["id"] = f"node_{i}"

                print(f"Analysis complete. Found {len(nodes)} components.")
                return result
            else:
                raise ValueError("No valid JSON found in response")

        except Exception as e:
            print(f"Analysis error: {str(e)}")
            return {
                "nodes": [
                    {
                        "id": "node1",
                        "text": "Error analyzing document. Please try with a shorter text.",
                        "type": "error",
                    }
                ],
                "edges": [],
            }

    async def analyze_image_with_gemini(self, image_path):
        """Process an image using Gemini 2.0 Flash"""
        print("\nProcessing image with Gemini 2.0 Flash...")
        try:
            # Read and prepare the image
            with Image.open(image_path) as img:
                print(f"Image opened successfully: {img.size}, mode: {img.mode}")

                # Convert to RGB if needed
                if img.mode != "RGB":
                    print(f"Converting image from {img.mode} to RGB")
                    img = img.convert("RGB")

                # Resize if the image is too large
                max_size = (1024, 1024)
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.LANCZOS)
                    print(f"Resized image to: {img.size}")

                # Save to bytes - using BytesIO
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format="PNG", optimize=True, quality=85)
                img_byte_arr.seek(0)  # Important: reset the pointer to the start
                img_data = {"mime_type": "image/png", "data": img_byte_arr.getvalue()}

            # Enhanced prompt for better image analysis
            prompt = """Analyze this image in detail and create a comprehensive workflow diagram. Break down the analysis into clear steps:

            1. Initial Visual Analysis:
            - Identify all visual elements (shapes, text, icons, etc.)
            - Note their positions and relationships
            - Identify any color coding or visual hierarchies
            - Look for arrows, lines, or other connection indicators
            
            2. Workflow Components:
            - Break down the image into distinct process steps or components
            - Identify any parallel processes or decision points
            - Note any start/end points or key milestones
            - Identify any conditional flows or branches
            
            3. Process Classification:
            - Categorize each component (input, process, decision, output, etc.)
            - Identify primary vs. supporting processes
            - Note any dependencies between components
            - Identify process boundaries and interfaces
            
            4. Data and Information Flow:
            - Track how information or data moves between components
            - Identify input/output relationships
            - Note any feedback loops or cyclic processes
            - Identify any data transformation points

            Convert your analysis into this specific JSON format:
            {
                "nodes": [
                    {
                        "id": "unique_process_name",
                        "text": "Detailed description of what this component does and its role in the workflow",
                        "type": "core"
                    }
                ],
                "edges": [
                    {
                        "from": "source_process_name",
                        "to": "target_process_name",
                        "label": "describes the nature of this connection"
                    }
                ]
            }

            Requirements for the output:
            1. Each node must have a unique, descriptive ID
            2. Node descriptions should be clear and detailed
            3. All connections must reference valid node IDs
            4. Edge labels should describe the nature of the connection
            5. Use "core" or "support" for node types

            If you can't identify specific components, create logical groupings based on visual elements and their apparent relationships."""

            try:
                print("Sending request to Gemini...")
                response = (
                    await self.model.generate_content_async(  # Changed to self.model
                        contents=[
                            prompt,
                            img_data,
                        ],  # Pass as a list with img_data dictionary
                        generation_config={
                            "temperature": 0.3,
                            "top_p": 0.8,
                            "top_k": 40,
                            "max_output_tokens": 2048,
                        },
                    )
                )

                if not response or not response.text:
                    raise ValueError("Empty response from Gemini")

                print("\n=== Gemini's Complete Response ===")
                print(response.text)
                print("\n=== End of Gemini's Response ===\n")
                print("Successfully received response from Gemini")

            except Exception as api_error:
                print(f"Gemini API error: {str(api_error)}")
                raise

            # Process response
            response_text = response.text.strip()

            # Improved JSON extraction
            try:
                # Find JSON in response
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1

                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    print("\n=== Extracted JSON ===")
                    print(json_str)
                    print("\n=== End of JSON ===\n")

                    try:
                        result = json.loads(json_str)
                    except json.JSONDecodeError:
                        print(
                            "Initial JSON parsing failed, attempting to clean the JSON string..."
                        )
                        # Clean JSON string
                        json_str = json_str.replace("'", '"')
                        json_str = json_str.replace("\n", " ")
                        result = json.loads(json_str)

                    # Update node IDs
                    nodes = result.get("nodes", [])
                    for i, node in enumerate(nodes, 1):
                        node["id"] = f"node_{i}"

                    print(f"Analysis complete. Found {len(nodes)} components.")
                    return result
                else:
                    print("No JSON found in response, creating basic structure...")
                    # Create a basic structure from the text response
                    result = {
                        "nodes": [
                            {
                                "id": "node_1",
                                "text": response_text[:500],
                                "type": "core",
                            }
                        ],
                        "edges": [],
                    }
                    return result

            except Exception as json_error:
                print(f"JSON processing error: {str(json_error)}")
                traceback.print_exc()  # Print the full traceback
                return {
                    "nodes": [
                        {
                            "id": "error_node",
                            "text": f"Error processing response: {str(json_error)}. Please try again.",
                            "type": "error",
                        }
                    ],
                    "edges": [],
                }

        except Exception as e:
            print(f"Image analysis error (Detailed): {str(e)}")
            print(f"Error type: {type(e)}")
            if hasattr(e, "__traceback__"):
                traceback.print_tb(e.__traceback__)
            return {
                "nodes": [
                    {
                        "id": "error_node",
                        "text": f"Error analyzing image: {str(e)}. Please try with a different image.",
                        "type": "error",
                    }
                ],
                "edges": [],
            }

    # Generate Mermaid diagram from workflow data, a mermaid is a diagramming tool that takes text and converts it into a diagram
    def generate_mermaid(self, workflow_data):
        print("\nGenerating Mermaid diagram...")
        mermaid = [
            "%%{init: {'theme': 'default', 'themeVariables': { 'fontSize': '14px', 'fontFamily': 'arial', 'lineWidth': '2px' }}}%%",
            "flowchart LR",
            "    %% Style definitions",
            "    classDef core fill:#e3f2fd,stroke:#1565c0,stroke-width:2px,rx:8,ry:8",
            "    classDef support fill:#f3f3f3,stroke:#78909c,stroke-width:2px,rx:8,ry:8",
            "    %% Link styles",
            "    linkStyle default stroke:#2196f3,stroke-width:2px",
            "",
        ]

        # Add nodes with detailed styling
        for node in workflow_data["nodes"]:
            # Format text with line breaks
            text = node["text"].replace('"', "'")
            words = text.split()
            lines = []
            current_line = []

            for word in words:
                if (
                    sum(len(w) for w in current_line) + len(current_line) + len(word)
                    > 30
                ):
                    lines.append(" ".join(current_line))
                    current_line = [word]
                else:
                    current_line.append(word)

            if current_line:
                lines.append(" ".join(current_line))

            node_text = "<br>".join(lines)
            node_id = node["id"].lower().replace(" ", "_")

            # Add node with text
            mermaid.append(f'    {node_id}["{node_text}"]')
            mermaid.append(f'    class {node_id} {node.get("type", "core")}')

        # Add connections with flow labels
        mermaid.append("")
        for edge in workflow_data.get("edges", []):
            from_id = edge["from"].lower().replace(" ", "_")
            to_id = edge["to"].lower().replace(" ", "_")
            label = edge.get("label", "flow")
            mermaid.append(f'    {from_id} --> |"{label}"| {to_id}')

        return "\n".join(mermaid)

    # Generate PNG image from Mermaid code
    def generate_image(self, mmd_file):
        print("\nGenerating PNG image...")
        png_file = os.path.join(self.temp_dir, "workflow.png")

        try:
            if platform.system() == "Darwin":  # macOS
                command = [
                    "npx",
                    "@mermaid-js/mermaid-cli",
                    "mmdc",
                    "-i",
                    mmd_file,
                    "-o",
                    png_file,
                    "-b",
                    "transparent",
                    "-s",
                    "2",
                ]
            else:  # Windows (reverting to the working version)
                command = [
                    "npx.cmd" if platform.system() == "Windows" else "npx",
                    "@mermaid-js/mermaid-cli",
                    "-i",
                    mmd_file,
                    "-o",
                    png_file,
                    "-b",
                    "transparent",
                    "-s",
                    "2",
                ]

            env = os.environ.copy()
            env["NODE_OPTIONS"] = "--no-warnings"

            result = subprocess.run(
                command, check=True, capture_output=True, text=True, env=env
            )

            if result.stderr:
                print("Command output:", result.stderr)

            if os.path.exists(png_file):
                print(f"Opening generated image: {png_file}")
                if platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", png_file])
                elif platform.system() == "Windows":
                    os.startfile(png_file)
                else:  # Linux
                    subprocess.run(["xdg-open", png_file])
                return png_file
            else:
                raise FileNotFoundError("PNG file was not generated")

        except Exception as e:
            print(f"Error generating/opening image: {str(e)}")
            print("\nTroubleshooting steps:")
            print("1. Check if Node.js is installed: node --version")
            print("2. Check if npm is installed: npm --version")
            print("3. Reinstall mermaid-cli: npm install -g @mermaid-js/mermaid-cli")
            print(
                "4. Try running manually: npx @mermaid-js/mermaid-cli -i input.mmd -o output.png"
            )
            return None

    # Main processing function, it will call the other functions to process the document
    async def process(self):
        try:
            print("\n=== Starting Processing ===")
            start_time = time.time()

            file_path = self.get_latest_file()
            extension = Path(file_path).suffix.lower()

            # Check if it's an image file
            if extension in [".png", ".jpg", ".jpeg"]:
                workflow_data = await self.analyze_image_with_gemini(file_path)
            else:
                # Original document processing path
                text = self.extract_text(file_path)
                workflow_data = await self.analyze_with_gemini(text)

            mermaid_code = self.generate_mermaid(workflow_data)
            mmd_path = os.path.join(self.temp_dir, "workflow.mmd")

            with open(mmd_path, "w", encoding="utf-8") as f:
                f.write(mermaid_code)

            png_file = self.generate_image(mmd_path)

            if png_file:
                print(f"\nWorkflow diagram saved as: {png_file}")

            print(f"\nTotal processing time: {time.time() - start_time:.2f} seconds")

        except Exception as e:
            print(f"\nError occurred: {str(e)}")
        finally:
            self._cleanup()


if __name__ == "__main__":
    processor = SmartDocumentProcessor()  # we create a new instance of the processor
    asyncio.run(processor.process())  # then we run the process function
