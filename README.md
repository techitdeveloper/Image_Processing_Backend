# Image_Processing_Backend
image processing system that receives a CSV file with product information, processes images listed in the CSV, and generates an output CSV file with processed image details. The system uses Flask as a web framework, SQLite for database management, and Python for backend processing.


Environment Setup
1. Clone the Repository
   git clone https://github.com/techitdeveloper/Image_Processing_Backend.git
   
   ```cd Image_Processing_Backend```

   2. Create a Virtual Environment


It's recommended to create a virtual environment to manage dependencies.

```python -m venv env```

```source env/bin/activate  # On Windows: env\Scripts\activate```

3. Install Dependencies
Install the necessary Python packages.

```pip install -r requirements.txt```

4. Set Up Environment Variables
This project requires certain environment variables to be set in a .env file. Create a .env file in the root of the project directory and add the following variables:
```# .env file
DATABASE_URL=sqlite:///image_processing.db
UPLOAD_FOLDER=uploads
SECRET_KEY=your_secret_key_here
```

```DATABASE_URL```: The path to your SQLite database. You can keep it as ```sqlite:///image_processing.db``` or change it based on your setup.
```UPLOAD_FOLDER```: Directory where uploaded files will be stored. Ensure this matches the directory specified in your code (uploads by default).
```IMAGE_FOLDER``` : Directory where compressed images will be stored. Ensure this matches the directory specified in your code (images by default).
```OUTPUT_FOLDER```: Directory where output csv files will be stored. Ensure this matches the directory specified in your code (ouptut by default).

5. Accessing the Application
You can now access the application by navigating to ```http://127.0.0.1:5000``` or local host in your web browser.
