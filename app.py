import streamlit as st
import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer
from peft import PeftModel

# --- Definisi model seperti waktu training ---
class CodebertModel(nn.Module):
    def __init__(self, model_name, num_label):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(model_name)
        self.head_label = nn.Linear(self.encoder.config.hidden_size, num_label)
        self.config = self.encoder.config

    def forward(self, input_ids=None, attention_mask=None, labels=None, **kwargs):
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask, **kwargs)
        pooled = outputs.last_hidden_state[:, 0, :]
        logits_label = self.head_label(pooled)
        return logits_label


# --- Fungsi untuk load LoRA model ---
def load_lora_model():
    base_model_name = "microsoft/codebert-base"  
    tokenizer = AutoTokenizer.from_pretrained(base_model_name)
    base_model = CodebertModel(model_name=base_model_name, num_label=2)
    model = PeftModel.from_pretrained(base_model, "lora_model", is_trainable=False)

    model.eval()
    return tokenizer, model


# --- Streamlit App ---
st.set_page_config(page_title="PHP Vulnerability Detector", page_icon="🛡️")
st.title("🛡️ Deteksi Kerentanan Kode PHP (XSS & SQLi)")
st.write("Masukkan potongan kode PHP untuk diperiksa apakah rentan terhadap serangan.")

tokenizer, model = load_lora_model()

code_input = st.text_area("💻 Masukkan kode PHP:", height=200)

if st.button("Periksa"):
    if not code_input.strip():
        st.warning("⚠️ Silakan masukkan kode terlebih dahulu.")
    else:
        inputs = tokenizer(
            code_input,
            padding='max_length',
            truncation=True,
            max_length=512,
            return_tensors="pt"
        )

        with torch.no_grad():
            logits = model(**inputs)
            probs = torch.softmax(logits, dim=1)
            pred = torch.argmax(probs, dim=1).item()

        confidence = probs[0][pred].item()
        label_map = {0: "🔴 Rentan", 1: "🟢 Aman"}
        st.markdown(f"### Hasil: {label_map[pred]} (Confidence: {confidence:.2%})")

        st.write("**Detail probabilitas:**")
        st.json({
            "bad (rentan)": float(probs[0][0]),
            "good (aman)": float(probs[0][1])
        })
