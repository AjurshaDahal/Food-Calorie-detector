import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models, transforms
from PIL import Image
import gradio as gr
import numpy as np

from inference import get_nutrition, NUTRITION_DB, PORTION_MULTIPLIERS

CHECKPOINT = "./checkpoints/best_model.pth"
DEVICE     = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_model():
    ckpt        = torch.load(CHECKPOINT, map_location=DEVICE)
    class_names = ckpt["classes"]
    num_classes = len(class_names)
    model = models.resnet50(weights=None)
    model.fc = nn.Sequential(nn.Dropout(0.4), nn.Linear(model.fc.in_features, num_classes))
    model.load_state_dict(ckpt["model_state"])
    model.to(DEVICE).eval()
    print(f"✅ Loaded {num_classes} classes on {DEVICE}")
    return model, class_names


model, CLASS_NAMES = load_model()

transform = transforms.Compose([
    transforms.Resize(256), transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225]),
])

FOOD_DESCRIPTIONS = {
    "pizza": "Italian flatbread with tomato sauce and toppings",
    "hot_dog": "Grilled sausage in a soft bun",
    "french_fries": "Deep-fried potato strips",
    "fried_rice": "Stir-fried rice with vegetables and egg",
    "sushi": "Japanese rice with seafood or vegetables",
    "ramen": "Japanese noodle soup with rich broth",
    "pad_thai": "Thai stir-fried rice noodles",
    "dumplings": "Filled dough pockets, steamed or fried",
    "spring_rolls": "Crispy rolled appetizer with fillings",
    "grilled_salmon": "Omega-3 rich grilled fish fillet",
    "chicken_curry": "Spiced chicken in aromatic sauce",
    "bibimbap": "Korean mixed rice bowl with vegetables",
    "pho": "Vietnamese beef noodle soup",
    "tacos": "Mexican tortilla with seasoned fillings",
    "nachos": "Tortilla chips with cheese and toppings",
    "waffles": "Grid-patterned baked breakfast cake",
    "pancakes": "Fluffy flat breakfast cakes",
    "omelette": "Folded egg dish with fillings",
    "caesar_salad": "Romaine lettuce with Caesar dressing",
    "greek_salad": "Fresh vegetables with feta cheese",
    "chocolate_cake": "Rich layered chocolate dessert",
    "cheesecake": "Creamy cheese-based dessert",
    "ice_cream": "Frozen dairy dessert",
    "donuts": "Fried dough ring with glaze",
    "apple_pie": "Baked pastry with spiced apple filling",
    "strawberry_shortcake": "Sponge cake with strawberries and cream",
    "miso_soup": "Japanese fermented soybean broth",
    "edamame": "Steamed young soybeans in pods",
}


@torch.no_grad()
def predict_gradio(image, item_count):
    if image is None:
        return build_empty_html()

    count = int(item_count) if item_count else 1

    pil_img = Image.fromarray(image).convert("RGB")
    tensor  = transform(pil_img).unsqueeze(0).to(DEVICE)
    probs   = F.softmax(model(tensor), dim=1)[0]
    top_p, top_i = probs.topk(5)

    best_food = CLASS_NAMES[top_i[0].item()]
    best_conf = round(top_p[0].item() * 100, 1)
    n         = get_nutrition(best_food, portion="Medium")

    desc = FOOD_DESCRIPTIONS.get(best_food, "Delicious food item")
    display_name = best_food.replace("_", " ").title()

    total_cal     = n["calories"] * count
    total_protein = round(n["protein_g"] * count, 1)
    total_carbs   = round(n["carbs_g"]   * count, 1)
    total_fat     = round(n["fat_g"]     * count, 1)
    total_fiber   = round(n["fiber_g"]   * count, 1)

    # Calorie ring color
    if total_cal < 300:   ring = "#22c55e"
    elif total_cal < 600: ring = "#f97316"
    else:                 ring = "#ef4444"

    # Confidence bar color
    if best_conf >= 80:   conf_color = "#22c55e"
    elif best_conf >= 50: conf_color = "#f97316"
    else:                 conf_color = "#ef4444"

    # SVG donut ring
    radius = 54
    circ   = 2 * 3.14159 * radius
    pct    = min(total_cal / 1000, 1.0)
    dash   = circ * pct
    gap    = circ - dash

    html = f"""
    <div style="font-family:'Segoe UI',system-ui,sans-serif; background:#f8fafc; border-radius:20px;
                padding:0; overflow:hidden; border:1px solid #e2e8f0; box-shadow:0 4px 24px rgba(0,0,0,0.08);">

      <!-- Header -->
      <div style="background:white; padding:20px 24px 16px; border-bottom:1px solid #f1f5f9;">
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:14px;">
          <div style="background:#dcfce7; border-radius:10px; width:40px; height:40px;
                      display:flex; align-items:center; justify-content:center; font-size:1.3em;">✅</div>
          <div>
            <div style="font-weight:700; font-size:1.05em; color:#0f172a;">Food Detected!</div>
            <div style="font-size:0.78em; color:#94a3b8;">Model: ResNet50 (Food-101) • Confidence: {best_conf}%</div>
          </div>
        </div>

        <!-- Food card -->
        <div style="background:#f8fafc; border-radius:14px; padding:16px; border:1px solid #e2e8f0;">
          <div style="font-size:1.25em; font-weight:700; color:#0f172a; margin-bottom:4px;">{display_name}</div>
          <div style="font-size:0.85em; color:#64748b; margin-bottom:12px;">{desc}</div>
          <div style="display:flex; align-items:center; gap:10px;">
            <div style="font-size:0.8em; color:#64748b; width:80px; flex-shrink:0;">Confidence</div>
            <div style="flex:1; background:#e2e8f0; border-radius:999px; height:8px;">
              <div style="width:{best_conf}%; background:{conf_color}; border-radius:999px; height:8px;"></div>
            </div>
            <div style="font-size:0.85em; font-weight:700; color:{conf_color}; width:45px; text-align:right;">{best_conf}%</div>
          </div>
        </div>
      </div>

      <!-- Calories + serving -->
      <div style="padding:20px 24px; background:white; margin-top:8px;">
        <div style="display:flex; align-items:center; gap:20px;">

          <!-- SVG donut -->
          <div style="position:relative; width:130px; height:130px; flex-shrink:0;">
            <svg width="130" height="130" viewBox="0 0 130 130">
              <circle cx="65" cy="65" r="{radius}" fill="none" stroke="#f1f5f9" stroke-width="12"/>
              <circle cx="65" cy="65" r="{radius}" fill="none" stroke="{ring}" stroke-width="12"
                      stroke-dasharray="{dash:.1f} {gap:.1f}"
                      stroke-dashoffset="{circ*0.25:.1f}"
                      stroke-linecap="round"/>
            </svg>
            <div style="position:absolute; top:50%; left:50%; transform:translate(-50%,-50%);
                        text-align:center; line-height:1.1;">
              <div style="font-size:1.6em; font-weight:800; color:#0f172a;">{total_cal}</div>
              <div style="font-size:0.7em; color:#94a3b8; font-weight:600; letter-spacing:0.05em;">KCAL</div>
            </div>
          </div>

          <!-- Serving info -->
          <div style="flex:1; display:flex; flex-direction:column; gap:10px;">
            <div style="background:#f8fafc; border-radius:12px; padding:12px 16px;
                        border:1px solid #e2e8f0; display:flex; justify-content:space-between; align-items:center;">
              <span style="color:#64748b; font-size:0.88em;">Serving</span>
              <span style="font-weight:700; color:#0f172a; font-size:0.88em;">{n['weight_g']}g / serving</span>
            </div>
            <div style="background:#f8fafc; border-radius:12px; padding:12px 16px;
                        border:1px solid #e2e8f0; display:flex; justify-content:space-between; align-items:center;">
              <span style="color:#64748b; font-size:0.88em;">Count</span>
              <span style="font-weight:700; color:#0f172a; font-size:0.88em;">{count} item{'s' if count>1 else ''} × {n['calories']} kcal</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Macros -->
      <div style="padding:0 24px 20px; background:white;">
        <div style="display:grid; grid-template-columns:1fr 1fr 1fr 1fr; gap:10px;">
          {macro_card("🥩", total_protein, "g", "PROTEIN", "#3b82f6", "#eff6ff")}
          {macro_card("🌾", total_carbs,   "g", "CARBS",   "#f97316", "#fff7ed")}
          {macro_card("🫒", total_fat,     "g", "FAT",     "#ef4444", "#fff1f2")}
          {macro_card("🥦", total_fiber,   "g", "FIBER",   "#22c55e", "#f0fdf4")}
        </div>
      </div>

      <!-- Footer note -->
      <div style="background:#f8fafc; padding:12px 24px; border-top:1px solid #f1f5f9;
                  font-size:0.75em; color:#94a3b8; text-align:center;">
        ℹ️ Calorie estimation is approximate and may vary based on portion size, preparation method, and ingredients.
      </div>
    </div>
    """
    return html


def macro_card(icon, value, unit, label, color, bg):
    return f"""
    <div style="background:{bg}; border-radius:14px; padding:14px 10px; text-align:center;">
      <div style="font-size:1.4em; margin-bottom:4px;">{icon}</div>
      <div style="font-size:1.2em; font-weight:800; color:#0f172a;">{value}{unit}</div>
      <div style="font-size:0.7em; font-weight:600; color:{color}; letter-spacing:0.06em; margin-top:2px;">{label}</div>
      <div style="margin-top:8px; background:rgba(0,0,0,0.08); border-radius:999px; height:3px;">
        <div style="width:60%; background:{color}; border-radius:999px; height:3px;"></div>
      </div>
    </div>"""


def build_empty_html():
    return """
    <div style="font-family:'Segoe UI',sans-serif; background:#f8fafc; border-radius:20px;
                padding:40px 24px; text-align:center; border:1px solid #e2e8f0; color:#94a3b8;">
      <div style="font-size:2.5em; margin-bottom:12px;">📷</div>
      <div style="font-size:1em; font-weight:600;">Upload a food photo to get started</div>
      <div style="font-size:0.85em; margin-top:6px;">Supports 28 food categories</div>
    </div>"""


# ─── CUSTOM CSS ──────────────────────────────────────────────────────────────

css = """
body { background: #f1f5f9 !important; }
.gradio-container { max-width: 960px !important; margin: 0 auto !important; }
#title-block { background: white; border-radius: 20px; padding: 28px 32px 20px;
               margin-bottom: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
#title-block h1 { font-size: 1.8em !important; font-weight: 800 !important;
                   color: #0f172a !important; margin: 0 0 4px !important; }
#title-block p  { color: #64748b !important; margin: 0 !important; font-size: 0.95em !important; }
.input-panel { background: white !important; border-radius: 20px !important;
               padding: 24px !important; box-shadow: 0 2px 12px rgba(0,0,0,0.06) !important;
               border: 1px solid #e2e8f0 !important; }
.gr-button-primary { background: #f97316 !important; border: none !important;
                     border-radius: 12px !important; font-weight: 700 !important;
                     font-size: 1em !important; padding: 14px !important;
                     box-shadow: 0 4px 14px rgba(249,115,22,0.35) !important; }
.gr-button-primary:hover { background: #ea6c00 !important; transform: translateY(-1px) !important; }
footer { display: none !important; }
"""

# ─── UI ──────────────────────────────────────────────────────────────────────

with gr.Blocks(css=css) as demo:

    with gr.Column(elem_id="title-block"):
        gr.Markdown("# 🍽️ Food Detector")
        gr.Markdown("Get instant calorie estimates from a photo")

    with gr.Row(equal_height=True):
        # Left panel
        with gr.Column(scale=1, elem_classes="input-panel"):
            image_input = gr.Image(
                sources=["upload", "webcam"],
                type="numpy",
                label="Upload or capture food image",
                height=300,
            )

            gr.Markdown("**🔢 How many items can you count?**")
            gr.Markdown("<span style='color:#64748b; font-size:0.85em;'>(e.g., number of momos, slices, pieces)</span>")

            item_count = gr.Slider(
                minimum=1, maximum=10, value=1, step=1,
                label="Item count"
            )

            submit_btn = gr.Button("🔍 Analyze Food", variant="primary", size="lg")

        # Right panel
        with gr.Column(scale=1):
            result_html = gr.HTML(value=build_empty_html())

    submit_btn.click(
        fn=predict_gradio,
        inputs=[image_input, item_count],
        outputs=result_html
    )

    image_input.change(
        fn=predict_gradio,
        inputs=[image_input, item_count],
        outputs=result_html
    )

if __name__ == "__main__":
    demo.launch(share=False, server_port=7860, show_error=True)