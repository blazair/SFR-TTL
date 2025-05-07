from flask import Flask, render_template_string, request, send_from_directory, abort
import os, pathlib, re

BASE_DIR    = pathlib.Path(__file__).resolve().parent
IMAGES_ROOT = BASE_DIR / 'images'

app = Flask(__name__)

# ─── Static image route ─────────────────────────────────────────────────────
@app.route('/img/<path:filename>')
def send_img(filename):
    full = IMAGES_ROOT / filename
    if not full.is_file():
        abort(404)
    return send_from_directory(IMAGES_ROOT, filename)

# ─── Helpers ────────────────────────────────────────────────────────────────
def list_dirs(path, ignore=None):
    ignore = set(ignore or [])
    return sorted(p.name for p in path.iterdir() if p.is_dir() and p.name not in ignore)

def pretty(name: str) -> str:
    return 'Non-Stationary' if name=='ns' else re.sub(r'_', ' ', name).title()

def collect_images(date, var):
    out = {}
    kroot = IMAGES_ROOT / date / var / 'kernels'
    for k in list_dirs(kroot):
        mean = uncert = None
        for f in (kroot / k).iterdir():
            fn = f.name
            # stationary naming
            if k!='ns':
                if fn.startswith('mean_'): mean   = f'/img/{date}/{var}/kernels/{k}/{fn}'
                if fn.startswith('std_'):  uncert = f'/img/{date}/{var}/kernels/{k}/{fn}'
            else:
                if fn.endswith('_mean.png'):   mean   = f'/img/{date}/{var}/kernels/{k}/{fn}'
                if fn.endswith('_uncert.png'): uncert = f'/img/{date}/{var}/kernels/{k}/{fn}'
        out[k] = {'mean': mean, 'uncert': uncert}
    return out

# ─── Main page ──────────────────────────────────────────────────────────────
@app.route('/', methods=['GET'])
def index():
    # 1) discover dates & variables
    dates     = list_dirs(IMAGES_ROOT, ignore=['arti'])
    date      = request.args.get('date', dates[0] if dates else '')
    if date not in dates: date = dates[0]

    variables = list_dirs(IMAGES_ROOT / date)
    var       = request.args.get('var', variables[0] if variables else '')
    if var not in variables: var = variables[0]

    # 2) discover kernels
    kernels   = list_dirs(IMAGES_ROOT / date / var / 'kernels')

    # 3) UI state
    mode          = request.args.get('mode', 'View')           # View | Compare
    view_type     = request.args.get('view_type', 'Stationary')# Stationary | Non-Stationary
    compare_type  = request.args.get('compare_type', 'single') # single | all
    kernel        = request.args.get('kernel', kernels[0])
    cmp_sel       = [kernel]                                   # default
    show_uncert   = request.args.get('uncert','off')=='on'

    # sanitize
    if kernel not in kernels:    kernel = kernels[0]
    if mode not in ['View','Compare']: mode = 'View'
    if view_type not in ['Stationary','Non-Stationary']: view_type = 'Stationary'
    if compare_type not in ['single','all']: compare_type = 'single'

    if mode=='Compare':
        if compare_type=='single':
            k = request.args.get('kernel', kernel)
            kernel = k if k in kernels else kernels[0]
            cmp_sel = [kernel]
        else:
            cmp_sel = kernels
    else:
        # View mode
        if view_type=='Non-Stationary':
            kernel = 'ns'

    imgs = collect_images(date, var)

    # ─── Render ───────────────────────────────────────────────────────────────
    return render_template_string("""
<!DOCTYPE html><html lang="en">
<head><meta charset="utf-8"><title>GP Explorer</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
  body { margin:0; font-family:sans-serif; }
  #sidebar { width:260px; background:#1e1e1e; height:100vh; position:fixed; overflow-y:auto; padding:1rem; }
  #sidebar h2{ color:#f0a020; }
  #sidebar label{ color:#f0a020; font-weight:500; }
  #sidebar select, #sidebar input[type=checkbox]+label { background:#333; color:#fff; border:1px solid #f0a020; }
  #content { margin-left:260px; padding:1rem; background:#121212; min-height:100vh; }
  .btn-primary{ background:#f0a020; border:#f0a020; color:#121212; }
  .btn-primary:hover{ background:#ffca70; }
  .img-thumb{ border:2px solid #f0a020; cursor:pointer; max-height:400px; margin:auto; display:block; }
  .card-custom{ background:#1a1a1a; border:1px solid #f0a020; }
  .card-header{ background:#f0a020; color:#121212; font-weight:600; }
</style></head><body>

<!-- SIDEBAR -->
<div id="sidebar">
  <h2>Controls</h2>
  <form>
    <!-- Date -->
    <div class="mb-3">
      <label>Date</label>
      <select name="date" class="form-select form-select-sm" onchange="this.form.submit()">
        {% for d in dates %}<option {% if d==date %}selected{% endif %}>{{d}}</option>{% endfor %}
      </select>
    </div>
    <!-- Variable -->
    <div class="mb-3">
      <label>Variable</label>
      <select name="var" class="form-select form-select-sm" onchange="this.form.submit()">
        {% for v in variables %}<option {% if v==var %}selected{% endif %}>{{v}}</option>{% endfor %}
      </select>
    </div>
    <!-- Mode -->
    <div class="mb-3">
      <label>Mode</label><br>
      <div class="form-check form-check-inline">
        <input class="form-check-input" type="radio" id="view" name="mode" value="View"
               {% if mode=='View' %}checked{% endif %} onchange="this.form.submit()">
        <label class="form-check-label" for="view">View</label>
      </div>
      <div class="form-check form-check-inline">
        <input class="form-check-input" type="radio" id="compare" name="mode" value="Compare"
               {% if mode=='Compare' %}checked{% endif %} onchange="this.form.submit()">
        <label class="form-check-label" for="compare">Compare</label>
      </div>
    </div>

    <!-- View controls -->
    {% if mode=='View' %}
      <div class="mb-3">
        <label>Type</label><br>
        <div class="form-check form-check-inline">
          <input class="form-check-input" type="radio" id="stat" name="view_type" value="Stationary"
                 {% if view_type=='Stationary' %}checked{% endif %} onchange="this.form.submit()">
          <label class="form-check-label" for="stat">Stationary</label>
        </div>
        <div class="form-check form-check-inline">
          <input class="form-check-input" type="radio" id="ns" name="view_type" value="Non-Stationary"
                 {% if view_type=='Non-Stationary' %}checked{% endif %} onchange="this.form.submit()">
          <label class="form-check-label" for="ns">Non-Stationary</label>
        </div>
      </div>
      {% if view_type=='Stationary' %}
        <div class="mb-3">
          <label>Kernel</label>
          <select name="kernel" class="form-select form-select-sm">
            {% for k in kernels %}<option value="{{k}}" {% if k==kernel %}selected{% endif %}>{{pretty(k)}}</option>{% endfor %}
          </select>
        </div>
      {% endif %}
    {% else %}
      <!-- Compare controls -->
      <div class="mb-3">
        <label>Compare With</label><br>
        <div class="form-check form-check-inline">
          <input class="form-check-input" type="radio" id="single" name="compare_type" value="single"
                 {% if compare_type=='single' %}checked{% endif %}>
          <label class="form-check-label" for="single">One Kernel</label>
        </div>
        <div class="form-check form-check-inline">
          <input class="form-check-input" type="radio" id="all" name="compare_type" value="all"
                 {% if compare_type=='all' %}checked{% endif %}>
          <label class="form-check-label" for="all">All Kernels</label>
        </div>
      </div>
      {% if compare_type=='single' %}
        <div class="mb-3">
          <label>Select Kernel</label>
          <select name="kernel" class="form-select form-select-sm">
            {% for k in kernels %}<option value="{{k}}" {% if k==kernel %}selected{% endif %}>{{pretty(k)}}</option>{% endfor %}
          </select>
        </div>
      {% endif %}
    {% endif %}

    <div class="mb-3 form-check">
      <input type="checkbox" class="form-check-input" id="u" name="uncert" {% if show_uncert %}checked{% endif %}>
      <label class="form-check-label" for="u">Show Uncertainty</label>
    </div>
    <button type="submit" class="btn btn-primary w-100">Apply</button>
  </form>
</div>

<!-- CONTENT -->
<div id="content">
  {% if mode=='View' %}
    {% if view_type=='Stationary' %}
      <h4 class="text-warning mb-3">Stationary – {{pretty(kernel)}}</h4>
      <div class="row g-4">
        <div class="col-md-6 text-center">
          <h6>Mean</h6>
          {% if imgs[kernel]['mean'] %}
            <img src="{{imgs[kernel]['mean']}}" class="img-thumb img-fluid"
                 data-bs-toggle="modal" data-bs-target="#m" data-src="{{imgs[kernel]['mean']}}">
          {% else %}<p class="text-danger">Missing</p>{% endif %}
        </div>
        {% if show_uncert %}
        <div class="col-md-6 text-center">
          <h6>Uncertainty</h6>
          {% if imgs[kernel]['uncert'] %}
            <img src="{{imgs[kernel]['uncert']}}" class="img-thumb img-fluid"
                 data-bs-toggle="modal" data-bs-target="#m" data-src="{{imgs[kernel]['uncert']}}">
          {% else %}<p class="text-danger">Missing</p>{% endif %}
        </div>
        {% endif %}
      </div>
    {% else %}
      <h4 class="text-warning mb-3">Non-Stationary</h4>
      <div class="row g-4">
        <div class="col-md-6 text-center">
          <h6>Mean</h6>
          {% if imgs['ns']['mean'] %}
            <img src="{{imgs['ns']['mean']}}" class="img-thumb img-fluid"
                 data-bs-toggle="modal" data-bs-target="#m" data-src="{{imgs['ns']['mean']}}">
          {% else %}<p class="text-danger">Missing</p>{% endif %}
        </div>
        {% if show_uncert %}
        <div class="col-md-6 text-center">
          <h6>Uncertainty</h6>
          {% if imgs['ns']['uncert'] %}
            <img src="{{imgs['ns']['uncert']}}" class="img-thumb img-fluid"
                 data-bs-toggle="modal" data-bs-target="#m" data-src="{{imgs['ns']['uncert']}}">
          {% else %}<p class="text-danger">Missing</p>{% endif %}
        </div>
        {% endif %}
      </div>
    {% endif %}
  {% else %}
    <h4 class="text-warning mb-3">Compare Non-Stationary</h4>
    {% if compare_type=='single' %}
      <!-- single compare -->
      <div class="row g-4">
        <div class="col-md-6 text-center">
          <h6>Non-Stationary Mean</h6>
          {% if imgs['ns']['mean'] %}
            <img src="{{imgs['ns']['mean']}}" class="img-thumb img-fluid"
                 data-bs-toggle="modal" data-bs-target="#m" data-src="{{imgs['ns']['mean']}}">
          {% else %}<p class="text-danger">Missing</p>{% endif %}
          {% if show_uncert %}
            <h6 class="mt-3">NS Uncertainty</h6>
            {% if imgs['ns']['uncert'] %}
              <img src="{{imgs['ns']['uncert']}}" class="img-thumb img-fluid"
                   data-bs-toggle="modal" data-bs-target="#m" data-src="{{imgs['ns']['uncert']}}">
            {% else %}<p class="text-danger">Missing</p>{% endif %}
          {% endif %}
        </div>
        <div class="col-md-6 text-center">
          <h6>Stationary ({{pretty(kernel)}}) Mean</h6>
          {% if imgs[kernel]['mean'] %}
            <img src="{{imgs[kernel]['mean']}}" class="img-thumb img-fluid"
                 data-bs-toggle="modal" data-bs-target="#m" data-src="{{imgs[kernel]['mean']}}">
          {% else %}<p class="text-danger">Missing</p>{% endif %}
          {% if show_uncert %}
            <h6 class="mt-3">Stationary Uncertainty</h6>
            {% if imgs[kernel]['uncert'] %}
              <img src="{{imgs[kernel]['uncert']}}" class="img-thumb img-fluid"
                   data-bs-toggle="modal" data-bs-target="#m" data-src="{{imgs[kernel]['uncert']}}">
            {% else %}<p class="text-danger">Missing</p>{% endif %}
          {% endif %}
        </div>
      </div>
    {% else %}
      <!-- all compare -->
      <div class="row g-4">
        {% for k in cmp_sel %}
          <div class="col-md-{{12 // (cmp_sel|length if cmp_sel|length<=4 else 4)}}">
            <div class="card card-custom">
              <div class="card-header text-center">{{pretty(k)}}</div>
              <div class="card-body text-center">
                <p class="mb-1">Mean</p>
                {% if imgs[k]['mean'] %}
                  <img src="{{imgs[k]['mean']}}" class="img-thumb img-fluid mb-2"
                       data-bs-toggle="modal" data-bs-target="#m" data-src="{{imgs[k]['mean']}}">
                {% else %}<p class="text-danger small">Missing</p>{% endif %}
                {% if show_uncert %}
                  <p class="mt-2 mb-1">Uncertainty</p>
                  {% if imgs[k]['uncert'] %}
                    <img src="{{imgs[k]['uncert']}}" class="img-thumb img-fluid"
                         data-bs-toggle="modal" data-bs-target="#m" data-src="{{imgs[k]['uncert']}}">
                  {% else %}<p class="text-danger small">Missing</p>{% endif %}
                {% endif %}
              </div>
            </div>
          </div>
        {% endfor %}
      </div>
    {% endif %}
  {% endif %}
</div>

<!-- Modal Viewer -->
<div class="modal fade" id="m" tabindex="-1">
  <div class="modal-dialog modal-xl modal-dialog-centered">
    <div class="modal-content bg-dark border-0">
      <img id="modalImg" src="#" class="img-fluid">
    </div>
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script>
  document.addEventListener('click', e=>{
    if(e.target.dataset.src){
      document.getElementById('modalImg').src = e.target.dataset.src;
    }
  });
</script>
</body></html>""",
    dates=dates, variables=variables, kernels=kernels,
    date=date, var=var, mode=mode, view_type=view_type,
    compare_type=compare_type, kernel=kernel,
    cmp_sel=cmp_sel, show_uncert=show_uncert,
    imgs=imgs, pretty=pretty)

if __name__=='__main__':
    app.run(debug=True)
