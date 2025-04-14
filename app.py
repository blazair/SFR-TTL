from flask import Flask, render_template_string, request
import sys

# Create the Flask app and set the static folder to your results directory.
# Make sure the folder 'results' (with your subfolders) is in the same directory as app.py.
app = Flask(__name__, static_folder='results', static_url_path='/results')

# Hard-coded options.
dates = ["dec6", "dec17", "feb15", "jan31", "oct3", "sep19"]
# These are the sensor variables (use exact folder names as saved).
sensor_variables = [
    "Chlorophyll_ug_L",
    "Conductivity_uS_cm",
    "Depth_Sonar",
    "Dissolved_Oxygen_Concentration_mg_L",
    "Dissolved_Oxygen_Saturation",
    "pH",
    "Temperature_°C"
]
# Display names for the kernel dropdown.
kernels = ["Exponential", "Squared Exponential", "Matern 3_2", "Matern 5_2"]

# Mapping for kernel names to folder names.
kernel_mapping = {
    "Exponential": "Exponential",
    "Squared Exponential": "Squared_Exponential",
    "Matern 3_2": "Matern_3_2",
    "Matern 5_2": "Matern_5_2"
}

@app.route("/", methods=["GET"])
def index():
    # Retrieve query parameters with defaults.
    selected_tab = request.args.get("tab", "sensor")
    selected_date = request.args.get("date", dates[0])
    selected_sensor = request.args.get("sensor", sensor_variables[0])
    selected_kernel = request.args.get("kernel", kernels[0])
    
    # Use the kernel mapping for sensor data file paths.
    kernel_folder = kernel_mapping.get(selected_kernel, selected_kernel)
    
    # Construct image paths for sensor data.
    sensor_mean_img = f"/results/{selected_date}/{selected_sensor}/kernels/{kernel_folder}/mean_{selected_date}_{selected_sensor}_{kernel_folder}.png"
    sensor_std_img  = f"/results/{selected_date}/{selected_sensor}/kernels/{kernel_folder}/std_{selected_date}_{selected_sensor}_{kernel_folder}.png"
    
    # For simulated field images, use the actual file names from your 'arti' folder.
    simulated_field_images = {
        "Exponential": "/results/arti/exp.png",
        "Squared Exponential": "/results/arti/sqexp.png",
        "Matern 3_2": "/results/arti/3_2.png",
        "Matern 5_2": "/results/arti/5_2.png"
    }
    
    # HTML template using Bootstrap.
    html = """
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>GP Regression Results</title>
      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
      <style>
        body { padding-top: 20px; }
        .img-col { flex: 1; padding: 10px; }
        .d-flex { display: flex; flex-wrap: wrap; }
      </style>
    </head>
    <body>
      <div class="container">
        <h1 class="mb-4">GP Regression Results</h1>
        <!-- Navigation Tabs -->
        <ul class="nav nav-tabs" id="myTab" role="tablist">
          <li class="nav-item">
            <a class="nav-link {% if selected_tab=='sensor' %}active{% endif %}" href="/?tab=sensor">Sensor Data</a>
          </li>
          <li class="nav-item">
            <a class="nav-link {% if selected_tab=='simulated' %}active{% endif %}" href="/?tab=simulated">Simulated Field</a>
          </li>
        </ul>
        <!-- Tab Content -->
        <div class="tab-content mt-4">
          {% if selected_tab == 'sensor' %}
          <div class="tab-pane fade show active">
            <!-- Dropdown Form -->
            <form method="get" class="row g-3 mb-4">
              <input type="hidden" name="tab" value="sensor">
              <div class="col-md-4">
                <label for="dateSelect" class="form-label">Date</label>
                <select name="date" id="dateSelect" class="form-select">
                  {% for d in dates %}
                    <option value="{{ d }}" {% if d == selected_date %}selected{% endif %}>{{ d }}</option>
                  {% endfor %}
                </select>
              </div>
              <div class="col-md-4">
                <label for="sensorSelect" class="form-label">Sensor Variable</label>
                <select name="sensor" id="sensorSelect" class="form-select">
                  {% for s in sensor_variables %}
                    <option value="{{ s }}" {% if s == selected_sensor %}selected{% endif %}>{{ s }}</option>
                  {% endfor %}
                </select>
              </div>
              <div class="col-md-4">
                <label for="kernelSelect" class="form-label">Kernel</label>
                <select name="kernel" id="kernelSelect" class="form-select">
                  {% for k in kernels %}
                    <option value="{{ k }}" {% if k == selected_kernel %}selected{% endif %}>{{ k }}</option>
                  {% endfor %}
                </select>
              </div>
              <div class="col-12">
                <button type="submit" class="btn btn-primary">View Results</button>
              </div>
            </form>
            <!-- Sensor Data Images: Mean and Uncertainty side by side -->
            <div class="d-flex">
              <div class="img-col">
                <h4>Mean Prediction</h4>
                <img src="{{ sensor_mean_img }}" alt="Sensor Mean Prediction" class="img-fluid">
              </div>
              <div class="img-col">
                <h4>Uncertainty Map</h4>
                <img src="{{ sensor_std_img }}" alt="Sensor Uncertainty" class="img-fluid">
              </div>
            </div>
          </div>
          {% else %}
          <div class="tab-pane fade show active">
            <h2>Simulated Field Results</h2>
            <!-- Display simulated field images in a grid -->
            <div class="row">
              {% for k, path in simulated_field_images.items() %}
                <div class="col-md-6 mb-4">
                  <h4>{{ k }}</h4>
                  <img src="{{ path }}" alt="Simulated Field {{ k }}" class="img-fluid">
                </div>
              {% endfor %}
            </div>
          </div>
          {% endif %}
        </div>
      </div>
      <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    return render_template_string(
        html,
        selected_tab=selected_tab,
        dates=dates,
        sensor_variables=sensor_variables,
        kernels=kernels,
        selected_date=selected_date,
        selected_sensor=selected_sensor,
        selected_kernel=selected_kernel,
        sensor_mean_img=sensor_mean_img,
        sensor_std_img=sensor_std_img,
        simulated_field_images=simulated_field_images
    )

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "export":
        # Use the Flask test client to generate static HTML.
        with app.test_client() as client:
            response = client.get("/")
            with open("site.html", "w", encoding="utf-8") as f:
                f.write(response.get_data(as_text=True))
        print("Static HTML saved as site.html")
        sys.exit(0)
    else:
        # Run the app normally.
        app.run(debug=True, host="0.0.0.0", port=5000)
